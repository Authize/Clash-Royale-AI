import argparse
from typing import Optional

import numpy as np
from sb3_contrib import RecurrentPPO

from src.emulator.adb_connector import ADBConnector
from src.emulator.connector import EmulatorConnector


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("--model", type=str, required=True, help="Path to trained model .zip")
	parser.add_argument("--serial", type=str, default=None, help="ADB device serial (optional)")
	args = parser.parse_args()

	adb = ADBConnector(serial=args.serial)
	bridge = EmulatorConnector(grid_rows=18, grid_cols=32)
	model = RecurrentPPO.load(args.model, device="cpu")

	obs = bridge.capture_observation()
	lstm_state = None
	start = np.array([True])

	while True:
		# Capture
		frame = adb.screencap()
		# TODO: Convert frame to observation
		obs = bridge.capture_observation()

		# Predict
		action, lstm_state = model.predict(obs, state=lstm_state, episode_start=start, deterministic=True)
		start = np.array([False])

		# Act
		bridge.action_to_emulator(action)


if __name__ == "__main__":

	main()


