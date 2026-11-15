"""Regression checks for clean exit instead of hidden/abandoned app processes."""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.mark.parametrize(
    "mode", ["close", "native", "shortcut", "background", "hidden-native", "unsaved", "discard"]
)
def test_quit_releases_threads_scripts_and_single_instance_socket(mode, tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "tests_v2.lifecycle_probe", mode, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        timeout=12,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1]) == {
        "stopped": True,
        "server_closed": True,
        "exit_ready": True,
    }
    assert "QThread: Destroyed" not in result.stderr
    assert "QProcess: Destroyed" not in result.stderr
    if mode in ("unsaved", "discard"):
        profiles = [json.loads(p.read_text()) for p in (tmp_path / "profiles").glob("*.json")]
        profile = next(p for p in profiles if p["id"] == "current-pico")
        if mode == "unsaved":
            assert profile["keys"][0]["label"] == "Preserved on quit"
        else:
            assert profile["keys"][0]["label"] != "Discarded on quit"
