import time
from typing import Optional

from src.emulator.adb_connector import ADBConnector


def is_app_running(adb: ADBConnector, package: str) -> bool:

	try:
		proc = adb._adb("shell", "pidof", package)
		out = proc.stdout.decode("utf-8", errors="ignore").strip()
		return len(out) > 0
	except Exception:
		return False


def launch_app(adb: ADBConnector, package: str) -> None:

	# Use monkey to start the main launcher activity
	adb._adb("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")


def ensure_app(adb: ADBConnector, package: str, wait_seconds: int = 10) -> None:

	if not is_app_running(adb, package):
		launch_app(adb, package)
		deadline = time.time() + max(0, wait_seconds)
		while time.time() < deadline:
			if is_app_running(adb, package):
				return
			time.sleep(0.5)


