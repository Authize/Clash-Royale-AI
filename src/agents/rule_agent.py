from typing import Tuple

import numpy as np

from src.emulator.memu_mapping import board_to_pixels, hand_slot_to_pixels


class RuleAgent:

	def __init__(self, rows: int = 18, cols: int = 32):

		self.rows = rows
		self.cols = cols

	def choose_action(self) -> Tuple[int, int, int]:

		# Naive policy: cycle hand[0] and place at random defensive tile
		card_idx = 0
		row = np.random.randint(0, self.rows // 2)
		col = np.random.randint(0, self.cols)
		return int(card_idx), int(row), int(col)


