import argparse
import os
from typing import Dict

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sb3_contrib import RecurrentPPO


def load_logs(log_dir: str) -> Dict[str, np.ndarray]:

	path = os.path.join(log_dir, "tensors.npz")
	data = np.load(path)
	return {k: data[k] for k in data.files}


def finetune(model_path: str, log_dir: str, out_path: str) -> None:

	# Load model
	model = RecurrentPPO.load(model_path, device="cpu")
	policy = model.policy
	policy.train()

	# Simple BC on action logits for card, row, col (assuming MultiDiscrete)
	logs = load_logs(log_dir)
	obs_spatial = torch.tensor(logs["obs_spatial"]).float()
	obs_context = torch.tensor(logs["obs_context"]).float()
	actions = torch.tensor(logs["action"]).long()

	optimizer = optim.Adam(policy.parameters(), lr=1e-4)
	criterion = nn.CrossEntropyLoss()

	batch_size = 256
	n = obs_spatial.shape[0]
	for epoch in range(3):
		perm = torch.randperm(n)
		for i in range(0, n, batch_size):
			idx = perm[i : i + batch_size]
			obs = {"spatial": obs_spatial[idx], "context": obs_context[idx]}
			with torch.no_grad():
				hidden = None
				# Use policy.extract_features; then mheads are inside policy
			features = policy.extract_features(obs)
			# Policy forward to get logits
			# Note: SB3 recurrent policy expects sequences; for BC we keep it simple
			pi_distribution = policy._get_action_dist_from_latent(policy.mlp_extractor.forward_actor(features))
			# For MultiDiscrete, distribution.proba_distribution_net returns logits list
			if not hasattr(pi_distribution, "distributions"):
				continue
			logits = [d.logits for d in pi_distribution.distributions]
			loss = 0.0
			for head, act in zip(logits, [actions[:, 0], actions[:, 1], actions[:, 2]]):
				loss = loss + criterion(head, act)
			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

	# Save fine-tuned model
	model.save(out_path)


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("--model", type=str, required=True)
	parser.add_argument("--logs", type=str, required=True)
	parser.add_argument("--out", type=str, required=True)
	args = parser.parse_args()

	finetune(model_path=args.model, log_dir=args.logs, out_path=args.out)


if __name__ == "__main__":

	main()


