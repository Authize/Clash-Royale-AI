import math
import random
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional

import gymnasium as gym
import numpy as np
from gymnasium import spaces


# Simplified Clash Royale–style simulator environment.
# This is not a full-physics replica; it provides:
# - Spatial grid observation with channels for friendly/opponent pressure and units
# - Vector context with elixir, timers, and last-opponent-play embedding
# - Factorized action: (card_index, row, col) with legality masks via info


@dataclass
class SimConfig:

	grid_rows: int = 18
	grid_cols: int = 32
	spatial_channels: int = 16
	card_vocab_size: int = 24
	max_steps: int = 3600  # ~3m at 50 ms per step
	decision_interval: int = 3  # act every N ticks
	initial_elixir: float = 5.0
	elixir_cap: float = 10.0
	elixir_regen_per_sec: float = 0.267  # approx 1 elixir every 3.75s (single elixir time)
	step_time_s: float = 0.05  # 50 ms per env step
	dense_reward_scale: float = 0.001


class ClashRoyaleSimEnv(gym.Env):

	metadata = {"render_modes": ["human"], "render_fps": 20}

	def __init__(self, config: Optional[SimConfig] = None, seed: Optional[int] = None):

		super().__init__()
		self.config = config or SimConfig()
		self.np_random, _ = gym.utils.seeding.np_random(seed)

		C, H, W = self.config.spatial_channels, self.config.grid_rows, self.config.grid_cols
		self.observation_space = spaces.Dict(
			{
				"spatial": spaces.Box(low=0.0, high=1.0, shape=(C, H, W), dtype=np.float32),
				"context": spaces.Box(low=-1.0, high=1.0, shape=(32,), dtype=np.float32),
			}
		)

		self.action_space = spaces.MultiDiscrete(
			[
				self.config.card_vocab_size,  # card index
				self.config.grid_rows,  # row
				self.config.grid_cols,  # col
			]
		)

		# Internal state
		self._step_count = 0
		self._match_time_s = 0.0
		self._our_elixir = self.config.initial_elixir
		self._opp_elixir = self.config.initial_elixir
		self._our_tower_hp = 1.0
		self._opp_tower_hp = 1.0
		self._last_opp_play = np.zeros(4, dtype=np.float32)  # [card_id_onehot (proj), row, col, time_since]
		self._spatial = np.zeros(
			(self.config.spatial_channels, self.config.grid_rows, self.config.grid_cols), dtype=np.float32
		)
		self._cooldown_ticks = 0

	def seed(self, seed: Optional[int] = None) -> None:

		self.np_random, _ = gym.utils.seeding.np_random(seed)

	def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):

		if seed is not None:
			self.seed(seed)
		self._step_count = 0
		self._match_time_s = 0.0
		self._our_elixir = self.config.initial_elixir
		self._opp_elixir = self.config.initial_elixir
		self._our_tower_hp = 1.0
		self._opp_tower_hp = 1.0
		self._last_opp_play = np.zeros(4, dtype=np.float32)
		self._spatial.fill(0.0)
		self._cooldown_ticks = 0
		obs = self._make_obs()
		info = {"legal_mask": self._make_legal_mask()}
		return obs, info

	def step(self, action: np.ndarray):

		card_idx, row, col = int(action[0]), int(action[1]), int(action[2])
		terminated = False
		truncated = False
		reward = 0.0

		# Apply action if legal and not on cooldown
		if self._cooldown_ticks == 0 and self._is_action_legal(card_idx, row, col):
			cost = self._card_cost(card_idx)
			if self._our_elixir >= cost:
				self._our_elixir -= cost
				self._cooldown_ticks = self.config.decision_interval  # small action interval
				self._apply_player_card(card_idx, row, col)

		# Simulate opponent simple policy occasionally
		if self._step_count % (self.config.decision_interval * 2) == 0:
			self._simulate_opponent()

		# Advance simulation by one tick
		self._advance_tick()
		self._step_count += 1
		self._match_time_s += self.config.step_time_s
		if self._cooldown_ticks > 0:
			self._cooldown_ticks -= 1

		# Dense reward: damage dealt minus taken, scaled
		damage_delta = (self._prev_opp_hp - self._opp_tower_hp) - (self._prev_our_hp - self._our_tower_hp)
		reward += self.config.dense_reward_scale * damage_delta

		# Terminal conditions
		if self._our_tower_hp <= 0.0 or self._opp_tower_hp <= 0.0:
			terminated = True
			reward += 1.0 if self._opp_tower_hp <= 0.0 and self._our_tower_hp > 0.0 else -1.0
		if self._step_count >= self.config.max_steps:
			truncated = True

		obs = self._make_obs()
		info = {"legal_mask": self._make_legal_mask()}
		return obs, reward, terminated, truncated, info

	def _advance_tick(self) -> None:

		# Store previous HP for reward computation
		self._prev_opp_hp = self._opp_tower_hp
		self._prev_our_hp = self._our_tower_hp

		# Very simple pressure-to-damage conversion
		friendly_pressure = float(self._spatial[1].mean())
		opponent_pressure = float(self._spatial[2].mean())
		self._opp_tower_hp = max(0.0, self._opp_tower_hp - 0.01 * friendly_pressure)
		self._our_tower_hp = max(0.0, self._our_tower_hp - 0.01 * opponent_pressure)

		# Diffuse spatial maps slightly
		self._spatial[1] *= 0.98
		self._spatial[2] *= 0.98

		# Elixir regen
		regen = self.config.elixir_regen_per_sec * self.config.step_time_s
		self._our_elixir = min(self.config.elixir_cap, self._our_elixir + regen)
		self._opp_elixir = min(self.config.elixir_cap, self._opp_elixir + regen)

		# Age last opponent play timestamp feature
		self._last_opp_play[-1] = np.clip(self._last_opp_play[-1] + self.config.step_time_s, 0.0, 10.0)

	def _apply_player_card(self, card_idx: int, row: int, col: int) -> None:

		# Increase friendly pressure near placement
		self._stamp_pressure(channel=1, row=row, col=col, magnitude=0.8)

	def _simulate_opponent(self) -> None:

		# Opponent plays randomly if enough elixir
		legal = []
		for c in range(self.config.card_vocab_size):
			if self._opp_elixir >= self._card_cost(c):
				legal.append(c)
		if not legal:
			return
		card = int(self.np_random.integers(0, len(legal)))
		card_idx = legal[card]
		row = int(self.np_random.integers(self.config.grid_rows // 2, self.config.grid_rows))
		col = int(self.np_random.integers(0, self.config.grid_cols))
		self._opp_elixir -= self._card_cost(card_idx)
		self._stamp_pressure(channel=2, row=row, col=col, magnitude=0.8)
		self._last_opp_play = np.array([
			float(card_idx) / max(1.0, float(self.config.card_vocab_size - 1)),
			float(row) / max(1.0, float(self.config.grid_rows - 1)),
			float(col) / max(1.0, float(self.config.grid_cols - 1)),
			0.0,
		], dtype=np.float32)

	def _stamp_pressure(self, channel: int, row: int, col: int, magnitude: float) -> None:

		# Add a Gaussian blob to a channel
		H, W = self.config.grid_rows, self.config.grid_cols
		r0 = np.clip(row, 0, H - 1)
		c0 = np.clip(col, 0, W - 1)
		sigma = 1.5
		for r in range(max(0, r0 - 3), min(H, r0 + 4)):
			for c in range(max(0, c0 - 3), min(W, c0 + 4)):
				dr = r - r0
				dc = c - c0
				val = magnitude * math.exp(-(dr * dr + dc * dc) / (2 * sigma * sigma))
				self._spatial[channel, r, c] = np.clip(self._spatial[channel, r, c] + val, 0.0, 1.0)

	def _make_obs(self) -> Dict[str, np.ndarray]:

		# Channel 0: static map (river/lanes). Fill once.
		if self._step_count == 0:
			self._spatial[0].fill(0.0)
			mid = self.config.grid_rows // 2
			self._spatial[0, mid - 1 : mid + 1, :].fill(1.0)

		# Compose context vector
		ctx = np.zeros((32,), dtype=np.float32)
		ctx[0] = np.clip(self._our_elixir / self.config.elixir_cap, 0.0, 1.0)
		ctx[1] = np.clip(self._opp_elixir / self.config.elixir_cap, 0.0, 1.0)
		ctx[2] = np.clip(self._match_time_s / 180.0, 0.0, 1.0)
		ctx[3:7] = self._last_opp_play  # card, row, col, dt
		# Remaining slots reserved for future (hand one-hots, timers, etc.)

		return {"spatial": self._spatial.copy(), "context": ctx}

	def _card_cost(self, card_idx: int) -> float:

		# Deterministic pseudo costs in [2, 6]
		return 2.0 + 4.0 * ((card_idx % 7) / 6.0)

	def _is_action_legal(self, card_idx: int, row: int, col: int) -> bool:

		if not (0 <= card_idx < self.config.card_vocab_size):
			return False
		if not (0 <= row < self.config.grid_rows and 0 <= col < self.config.grid_cols):
			return False
		# Basic rule: cannot place on opponent back rows; restrict to our side
		return row < (self.config.grid_rows // 2)

	def _make_legal_mask(self) -> np.ndarray:

		# Card legality: 1 if playable by elixir; placement legality is enforced by environment
		mask = np.zeros((self.config.card_vocab_size,), dtype=np.int8)
		for i in range(self.config.card_vocab_size):
			mask[i] = 1 if self._our_elixir >= self._card_cost(i) else 0
		return mask

	def render(self):

		# Minimal textual render for debugging
		print(
			f"t={self._match_time_s:.1f}s our_hp={self._our_tower_hp:.2f} opp_hp={self._opp_tower_hp:.2f} our_elixir={self._our_elixir:.2f}"
		)


