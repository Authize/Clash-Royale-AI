import argparse
from typing import Optional
import os

import numpy as np
from sb3_contrib import RecurrentPPO

from src.emulator.adb_connector import ADBConnector
from src.emulator.connector import EmulatorConnector
from src.emulator.memu_mapping import board_to_pixels, hand_slot_to_pixels
from src.agents.rule_agent import RuleAgent
from src.emulator.utils import ensure_app
from src.utils.recorder import Recorder


def main():

	parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=None, help="Path to trained model .zip (omit for rule mode)")
    parser.add_argument("--serial", type=str, default=None, help="ADB device serial (optional)")
    parser.add_argument("--adb-path", type=str, default="adb", help="Path to adb.exe (MEmu adb supported)")
    parser.add_argument("--mode", type=str, choices=["rule", "rl"], default="rule")
    parser.add_argument("--package", type=str, default="com.supercell.clashroyale", help="Android package name of Clash Royale")
    parser.add_argument("--log-dir", type=str, default=None, help="If set, logs observations/actions to this directory")
    parser.add_argument("--save-frames", action="store_true", help="Save JPEG frames to log dir (larger storage)")
    parser.add_argument("--hot-reload", action="store_true", help="Auto-reload model when file timestamp changes (rl mode)")
	args = parser.parse_args()

    adb = ADBConnector(serial=args.serial, adb_path=args.adb_path)
    bridge = EmulatorConnector(grid_rows=18, grid_cols=32)
    # Ensure Clash Royale is running
    ensure_app(adb, package=args.package, wait_seconds=12)
    recorder = Recorder(out_dir=args.log_dir, save_frames=args.save_frames) if args.log_dir else None
    last_mtime = None
	model = None
	if args.mode == "rl":
		if not args.model:
			raise ValueError("--model is required in rl mode")
		model = RecurrentPPO.load(args.model, device="cpu")
	else:
		rule = RuleAgent(rows=18, cols=32)

	obs = bridge.capture_observation()
	lstm_state = None
	start = np.array([True])

	while True:
		# Capture
		frame = adb.screencap()
		# TODO: Convert frame to observation
		obs = bridge.capture_observation()

        if args.mode == "rl":
            # Optional hot-reload of model weights
            if args.hot_reload and args.model:
                try:
                    mtime = os.path.getmtime(args.model)
                    if last_mtime is None:
                        last_mtime = mtime
                    elif mtime != last_mtime:
                        model = RecurrentPPO.load(args.model, device="cpu")
                        last_mtime = mtime
                except Exception:
                    pass
            # Predict
			action, lstm_state = model.predict(obs, state=lstm_state, episode_start=start, deterministic=True)
			start = np.array([False])
			bridge.action_to_emulator(action)
		else:
			card_idx, row, col = rule.choose_action()
			w, h = adb.get_screen_size()
			hx, hy = hand_slot_to_pixels(slot_idx=card_idx % 4, screen_w=w, screen_h=h)
			x, y = board_to_pixels(row=row, col=col, rows=18, cols=32, screen_w=w, screen_h=h)
			adb.tap(hx, hy)
			adb.swipe(hx, hy, x, y, duration_ms=120)

        # Logging (optional)
        if recorder is not None:
            try:
                reward = 0.0
                if args.mode == "rl":
                    recorded_action = action
                else:
                    recorded_action = np.array([card_idx, row, col], dtype=np.int64)
                recorder.log_step(obs=obs, action=recorded_action, reward=reward, frame=frame if args.save_frames else None)
            except Exception:
                pass


if __name__ == "__main__":

	main()


