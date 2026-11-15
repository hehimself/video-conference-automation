import os
import sys
import time
import json
import zipfile
from pathlib import Path
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from keypad_studio.device import DeviceWorker
from keypad_studio.profiles import Library
from keypad_studio.runner import Runner, extract_latest
from keypad_studio.window import Window


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def spin(ms=50):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_editor_selection_swap_undo_and_platform_edits(app, tmp_path):
    library = Library(tmp_path)
    device = DeviceWorker()
    runner = Runner(library, device)
    window = Window(library, device, runner)
    before = window.profile["keys"][0]["label"]
    window.label.setText("My action")
    window.capture()
    window.select_key(1)
    assert window.profile["keys"][0]["label"] == "My action" and not runner.runs
    window.swap(0, 1)
    assert window.profile["keys"][1]["label"] == "My action"
    window.undo()
    assert window.profile["keys"][0]["label"] == "My action"
    window.target.setCurrentIndex(window.target.findData("macos"))
    assert window.profile["target_os"] == "macos"
    window.action_editor.load({"type": "hotkey", "keys": ["cmd", "m"]})
    window.capture()
    window.save_local()
    assert window.profile["keys"][1]["bindings"]["macos"]["press"]["keys"] == ["cmd", "m"]
    window.board.timer.stop()
    window.deleteLater()


def test_script_output_state_progress_failure_timeout_and_cancel(app, tmp_path):
    library = Library(tmp_path / "settings")
    device = DeviceWorker()
    runner = Runner(library, device)
    states = []
    progress = []
    feedback = []
    runner.state.connect(lambda *x: states.append(x))
    runner.progress.connect(lambda *x: progress.append(x))
    runner.feedback.connect(lambda *x: feedback.append(x))
    script = tmp_path / "script.py"
    script.write_text(
        'import json,os\nprint(json.dumps({"type":"state","state":"on"}),flush=True)\nprint(json.dumps({"type":"progress","value":0.5}),flush=True)\nassert os.environ["KEYPAD_KEY_ID"]=="0"\n'
    )
    library.set_binding(
        "example", runner.os_name, {"executable": sys.executable, "path": str(script), "timeout": 2}
    )
    runner.start(0, {"type": "run_script", "binding_id": "example"})
    spin(500)
    assert states == [(0, "on")] and progress == [(0, 0.5)] and feedback[-1] == (0, "success")
    script.write_text("raise SystemExit(3)\n")
    runner.start(0, {"type": "run_script", "binding_id": "example"})
    spin(500)
    assert feedback[-1] == (0, "error")
    script.write_text("import time\ntime.sleep(20)\n")
    library.set_binding(
        "example", runner.os_name, {"executable": sys.executable, "path": str(script), "timeout": 1}
    )
    runner.start(0, {"type": "run_script", "binding_id": "example"})
    spin(1400)
    assert feedback[-1] == (0, "error") and not runner.runs
    runner.start(0, {"type": "run_script", "binding_id": "example"})
    spin(50)
    runner.cancel(0)
    spin(100)
    assert not runner.runs


def test_zip_extraction_and_traversal_rejection(tmp_path):
    source = tmp_path / "downloads"
    source.mkdir()
    destination = tmp_path / "out"
    with zipfile.ZipFile(source / "ok.zip", "w") as archive:
        archive.writestr("folder/test.txt", "hello")
    extract_latest(source, destination)
    assert (destination / "folder/test.txt").read_text() == "hello"
    (source / "ok.zip").unlink()
    with zipfile.ZipFile(source / "bad.zip", "w") as archive:
        archive.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError):
        extract_latest(source, destination)
    assert not (tmp_path / "escape.txt").exists()


def test_theme_switch_persists_without_changing_profile(app, tmp_path):
    from copy import deepcopy
    from keypad_studio.themes import PALETTES

    library = Library(tmp_path)
    device = DeviceWorker()
    runner = Runner(library, device)
    window = Window(library, device, runner)
    original = deepcopy(window.profile)
    window.appearance.setCurrentIndex(window.appearance.findData("light"))
    assert window.board.buttons[0].theme is PALETTES["light"]
    assert window.profile == original and not window.dirty
    assert Library(tmp_path).settings["appearance"] == "light"
    window.appearance.setCurrentIndex(window.appearance.findData("dark"))
    assert window.board.buttons[0].theme is PALETTES["dark"] and window.profile == original
    window.board.timer.stop()
    window.deleteLater()


def test_cancelled_binding_dialog_does_not_change_settings(app, tmp_path):
    from copy import deepcopy
    from keypad_studio.widgets import BindingDialog

    library = Library(tmp_path)
    original = deepcopy(library.settings)
    dialog = BindingDialog(library, library.all()[0], "macos")
    dialog.controls["path"].setText("/private/unsaved-script.py")
    dialog.capture()
    dialog.reject()
    assert library.settings == original


def test_new_script_actions_have_distinct_settings(app):
    from keypad_studio.widgets import ActionEditor

    one, two = ActionEditor(), ActionEditor()
    for editor in (one, two):
        editor.kind.setCurrentIndex(editor.kind.findData("run_script"))
    assert one.value()["binding_id"] != two.value()["binding_id"]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_compact_editor_keeps_keys_preview_and_test_controls_separate(app, tmp_path, theme):
    from PySide6.QtCore import QPoint, QRect
    from PySide6.QtWidgets import QPushButton

    library = Library(tmp_path)
    device = DeviceWorker()
    window = Window(library, device, Runner(library, device))
    window.appearance.setCurrentIndex(window.appearance.findData(theme))
    window.resize(1100, 760)
    window.show()
    app.processEvents()
    center = window.board.parentWidget()
    assert center.rect().contains(window.board.geometry())
    assert window.board.geometry().bottom() < window.preview_button.geometry().top()
    assert window.preview_button.geometry().bottom() < window.diagnostic.geometry().top()
    for key in window.board.buttons:
        bounds = QRect(key.mapTo(window.board, QPoint()), key.size())
        assert window.board.rect().contains(bounds)
        assert key.accessibleName().startswith("Key ")
    test = next(b for b in window.findChildren(QPushButton) if b.text() == "Test action")
    for tab in range(3):
        window.tabs.setCurrentIndex(tab)
        app.processEvents()
        assert test.isVisibleTo(window)
        assert window.tabs.geometry().bottom() < test.geometry().top()
    window.hide()
    assert not window.board.timer.isActive()
    window.deleteLater()


def test_friendly_trigger_and_state_labels_preserve_protocol_values(app, tmp_path):
    from copy import deepcopy
    from keypad_core.schema import effect, validate

    library = Library(tmp_path)
    device = DeviceWorker()
    runner = Runner(library, device)
    window = Window(library, device, runner)
    press = deepcopy(window.action_editor.value())
    os_name = window.profile["target_os"]
    window.trigger.setCurrentIndex(window.trigger.findData("release"))
    window.action_editor.load({"type": "hotkey", "keys": ["ctrl", "a"]})
    window.capture()
    window.trigger.setCurrentIndex(window.trigger.findData("press"))
    assert window.action_editor.value() == press
    actions = window.profile["keys"][0]["bindings"][os_name]
    assert actions["release"] == {"type": "hotkey", "keys": ["ctrl", "a"]}
    assert "On release" not in actions
    window.state_choice.setCurrentIndex(window.state_choice.findData("error"))
    window.override.setChecked(True)
    window.key_effect.load(effect("blink", [200, 30, 30]))
    window.capture()
    assert window.profile["keys"][0]["lighting"]["error"]["name"] == "blink"
    validate(window.profile)
    assert not runner.runs
    window.board.timer.stop()
    window.deleteLater()
