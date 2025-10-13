import argparse
import os
from typing import Optional

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.callbacks import CheckpointCallback

from src.envs.cr_sim_env import ClashRoyaleSimEnv, SimConfig
from src.models.feature_extractor import CRDictExtractor


def make_env(seed: int = 0):

	def _init():
		cfg = SimConfig()
		env = ClashRoyaleSimEnv(config=cfg, seed=seed)
		return env

	return _init


def train(total_steps: int, save_dir: Optional[str], load_path: Optional[str], eval_only: bool = False):

	set_random_seed(42)
	env = DummyVecEnv([make_env(42)])

	policy_kwargs = dict(
		features_extractor_class=CRDictExtractor,
		features_extractor_kwargs=dict(features_dim=512),
		lstm_hidden_size=256,
		n_lstm_layers=1,
		shared_lstm=True,
		enable_critic_lstm=False,
	)

	if load_path and os.path.isfile(load_path):
		model = RecurrentPPO.load(load_path, env=env, policy_kwargs=policy_kwargs, device="auto")
	else:
		model = RecurrentPPO(
			"MultiInputLstmPolicy",
			env,
			learning_rate=3e-4,
			n_steps=512,
			batch_size=1024,
			ent_coef=0.02,
			clip_range=0.2,
			gamma=0.997,
			gae_lambda=0.95,
			policy_kwargs=policy_kwargs,
			verbose=1,
			device="auto",
		)

	if eval_only:
		obs = env.reset()
		lstm_states = None
		episode_starts = np.ones((env.num_envs,), dtype=bool)
		for _ in range(1000):
			action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
			obs, reward, done, info = env.step(action)
			episode_starts = done
		return

	callback = None
	if save_dir:
		os.makedirs(save_dir, exist_ok=True)
		callback = CheckpointCallback(save_freq=5000, save_path=save_dir, name_prefix="cr_agent")

	model.learn(total_timesteps=int(total_steps), callback=callback)
	if save_dir:
		latest = os.path.join(save_dir, "latest")
		model.save(latest)


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("--total-steps", type=int, default=200000)
	parser.add_argument("--save-dir", type=str, default=None)
	parser.add_argument("--load", type=str, default=None)
	parser.add_argument("--eval-only", action="store_true")
	args = parser.parse_args()

	train(total_steps=args.total_steps, save_dir=args.save_dir, load_path=args.load, eval_only=args.eval_only)


if __name__ == "__main__":

	main()


