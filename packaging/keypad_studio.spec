"""Native application packaging, including version metadata and bundled firmware."""

import sys
import runpy
from pathlib import Path

root = Path(SPECPATH).parent
version = runpy.run_path(str(root / "keypad_studio/__init__.py"))["__version__"]
assets = root / "keypad_studio/assets"
mac = sys.platform == "darwin"
app_icon = str(assets / ("app-icon.icns" if mac else "app-icon.ico"))
hidden = ["keypad_studio.zip_helper", "pyautogui"]
windows_version = None
if not mac:
    from PyInstaller.utils.win32.versioninfo import (
        VSVersionInfo,
        FixedFileInfo,
        StringFileInfo,
        StringTable,
        StringStruct,
        VarFileInfo,
        VarStruct,
    )

    hidden += ["pywinauto", "pycaw.pycaw"]
    numbers = tuple(int(n) for n in version.split(".")) + (0,)
    windows_version = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=numbers,
            prodvers=numbers,
            mask=0x3F,
            flags=0,
            OS=0x40004,
            fileType=1,
            subtype=0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        "040904B0",
                        [
                            StringStruct("FileDescription", "Keypad Studio"),
                            StringStruct("FileVersion", version),
                            StringStruct("ProductName", "Keypad Studio"),
                            StringStruct("ProductVersion", version),
                            StringStruct("OriginalFilename", "Keypad Studio.exe"),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )

a = Analysis(
    [str(root / "tools/desktop_entry.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(assets), "keypad_studio/assets"),
        (str(root / "build/firmware-bundle"), "firmware-bundle"),
        (str(root / "keypad_studio/LUCIDE-LICENSE.txt"), "licenses"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Keypad Studio",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=app_icon,
    version=windows_version,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Keypad Studio")
if mac:
    app = BUNDLE(
        coll,
        name="Keypad Studio.app",
        icon=app_icon,
        bundle_identifier="com.keypadstudio.desktop",
        version=version,
        info_plist={"CFBundleVersion": version, "NSHighResolutionCapable": True},
    )
