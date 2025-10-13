from typing import Dict, Tuple, Any

import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class CRDictExtractor(BaseFeaturesExtractor):

	def __init__(self, observation_space, features_dim: int = 512):

		# Expect Dict(spatial: (C,H,W), context: (D,))
		super().__init__(observation_space, features_dim)
		spatial_space = observation_space["spatial"]
		context_space = observation_space["context"]
		c, h, w = spatial_space.shape
		ctx_dim = context_space.shape[0]

		self.cnn = nn.Sequential(
			nn.Conv2d(c, 32, kernel_size=3, stride=1, padding=1),
			nn.ReLU(inplace=True),
			nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
			nn.ReLU(inplace=True),
			nn.Conv2d(64, 64, kernel_size=3, stride=2, padding=1),
			nn.ReLU(inplace=True),
		)
		with torch.no_grad():
			dummy = torch.zeros(1, c, h, w)
			cnn_out = self.cnn(dummy)
			flat_dim = cnn_out.view(1, -1).shape[1]

		self.context_mlp = nn.Sequential(
			nn.Linear(ctx_dim, 128),
			nn.ReLU(inplace=True),
		)
		self.fc = nn.Sequential(
			nn.Linear(flat_dim + 128, features_dim),
			nn.ReLU(inplace=True),
		)

	def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:

		spatial = observations["spatial"].float()
		context = observations["context"].float()
		cnn_out = self.cnn(spatial)
		flat = torch.flatten(cnn_out, start_dim=1)
		ctx = self.context_mlp(context)
		features = self.fc(torch.cat([flat, ctx], dim=1))
		return features


