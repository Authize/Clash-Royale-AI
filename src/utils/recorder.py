import json
import os
import time
from typing import Any, Dict, Optional

import numpy as np


class Recorder:

	def __init__(self, out_dir: str, save_frames: bool = False):

		self.out_dir = out_dir
		self.save_frames = save_frames
		os.makedirs(self.out_dir, exist_ok=True)
		self.jsonl_path = os.path.join(self.out_dir, "events.jsonl")
		self.npz_path = os.path.join(self.out_dir, "tensors.npz")
		self._jsonl = open(self.jsonl_path, "a", encoding="utf-8")
		self._tensors: Dict[str, list] = {"obs_spatial": [], "obs_context": [], "action": [], "reward": []}

	def log_step(self, obs: Dict[str, np.ndarray], action: np.ndarray, reward: float, frame: Optional[np.ndarray] = None) -> None:

		# Append tensor data for periodic NPZ flush
		self._tensors["obs_spatial"].append(np.asarray(obs.get("spatial")))
		self._tensors["obs_context"].append(np.asarray(obs.get("context")))
		self._tensors["action"].append(np.asarray(action))
		self._tensors["reward"].append(np.asarray([reward], dtype=np.float32))

		# JSON line with metadata
		rec = {
			"t": time.time(),
			"reward": float(reward),
		}
		self._jsonl.write(json.dumps(rec) + "\n")
		self._jsonl.flush()

		# Optional frame saving
		if self.save_frames and frame is not None:
			idx = int(len(self._tensors["action"]) - 1)
			frame_path = os.path.join(self.out_dir, f"frame_{idx:07d}.jpg")
			try:
				import cv2
				cv2.imwrite(frame_path, frame)
			except Exception:
				pass

	def flush(self) -> None:

		# Save and clear accumulated tensors
		if not self._tensors["action"]:
			return
		arrays = {k: np.stack(v, axis=0) for k, v in self._tensors.items() if len(v) > 0}
		if arrays:
			np.savez_compressed(self.npz_path, **arrays)
		for k in list(self._tensors.keys()):
			self._tensors[k] = []

	def close(self) -> None:

		self.flush()
		try:
			self._jsonl.close()
		except Exception:
			pass


