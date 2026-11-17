"""Windows regression test: the Settings dialog opened from the tray responds."""

import os
import subprocess  # nosec B404
import sys

import pytest

PROBE = os.path.join(os.path.dirname(__file__), "win_tray_dialog_probe.py")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows tray integration test")
@pytest.mark.parametrize("mode", ["menu", "direct"])
def test_settings_dialog_from_tray_responds(mode):
    """Open Settings from the tray icon, click Cancel, expect the dialog to close."""
    env = dict(os.environ)
    # The probe needs the real "windows" Qt platform, not "offscreen".
    env.pop("QT_QPA_PLATFORM", None)
    try:
        result = subprocess.run(  # nosec B603
            [sys.executable, PROBE, mode],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"probe did not finish:\n{error.stdout}\n{error.stderr}")
    print(result.stdout)
    print(result.stderr[-3000:])
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr[-3000:]}"
