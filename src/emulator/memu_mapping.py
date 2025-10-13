from typing import Tuple


def board_to_pixels(row: int, col: int, rows: int, cols: int, screen_w: int, screen_h: int) -> Tuple[int, int]:

	# Simple uniform mapping of a logical grid to screen pixels
	px = int((col + 0.5) * (screen_w / cols))
	py = int((row + 0.5) * (screen_h / rows))
	return px, py


def hand_slot_to_pixels(slot_idx: int, screen_w: int, screen_h: int) -> Tuple[int, int]:

	# Approximate 4 hand slots along the bottom; adjust empirically
	bottom_y = int(screen_h * 0.93)
	spacing = int(screen_w * 0.18)
	start_x = int(screen_w * 0.28)
	px = start_x + slot_idx * spacing
	py = bottom_y
	return px, py


