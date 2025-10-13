import subprocess
import tempfile
from typing import Tuple, Optional

import numpy as np
import cv2


class ADBConnector:

	"""
	Android ADB-based connector for capturing frames and sending input events.
	Requires adb to be in PATH and an emulator/device connected.

	Note: Ensure usage complies with app and platform terms.
	"""

	def __init__(self, serial: Optional[str] = None):

		self.serial = serial

	def _adb(self, *args: str) -> subprocess.CompletedProcess:

		base = ["adb"]
		if self.serial:
			base += ["-s", self.serial]
		return subprocess.run(base + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

	def screencap(self) -> np.ndarray:

		# Capture PNG via adb and decode to BGR image
		proc = self._adb("exec-out", "screencap", "-p")
		data = proc.stdout
		image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
		if image is None:
			raise RuntimeError("Failed to decode screencap")
		return image

	def tap(self, x: int, y: int) -> None:

		self._adb("shell", "input", "tap", str(x), str(y))

	def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 150) -> None:

		self._adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))


