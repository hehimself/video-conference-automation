# Keypad Studio

![Original video conference automation project](images/header.png)

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Original MicroPython implementation](https://img.shields.io/badge/Made%20with-MicroPython-1f425f.svg)](docs/legacy-readme.md "Original MicroPython implementation")
[![Development status](https://img.shields.io/badge/Status-in%20progress-orange.svg)](#use-it)
[![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](LICENSE)

A visual Mac and Windows editor for the **Raspberry Pi Pico + Pimoroni RGB Keypad Base**.
Click a virtual key, choose actions and lighting, and save the active profile to the Pico.

**[Download Keypad Studio for macOS or Windows](https://github.com/hehimself/video-conference-automation/releases/latest)**

Choose the Apple Silicon or Intel Mac disk image, or the Windows x64 ZIP. On Mac,
drag the app from the disk image into Applications. On Windows, extract the full
ZIP and open Keypad Studio.exe inside its folder. Python is not required. Builds
are not notarized/commercially signed; see the release notes for OS prompts.

![Keypad Studio in light mode with visual key mapping and the action inspector](images/editor-light.png)

## Hardware

A Raspberry Pi Pico mounted on the Pimoroni RGB Keypad Base, with 16 illuminated keys.

![Pimoroni RGB Keypad Base with a Raspberry Pi Pico](https://cdn.shopify.com/s/files/1/0174/1800/products/pico-addons-2_1024x1024.jpg?v=1611177905)

## Use it

1. Open **Keypad Studio**. The editor works without a connected device.
2. Select **Current Pico** or **Classic Conference**, or create a new profile.
   **Profile options** contains Duplicate and Rename.
3. Choose the target OS and keyboard layout. German Mac and Windows are distinct.
4. Click a virtual key to edit its action, sequence, timing and lighting. Drag keys to
   swap assignments; Copy/Paste and Undo are available. Click a sequence step and
   Edit to configure it without writing JSON.
5. Use **Computer settings** in the sidebar to select scripts, interpreters, sound files and app paths.
6. Preview lighting locally or on the connected Pico. Preview never saves flash or
   triggers physical key actions.
7. **Save locally** keeps the profile in your computer's library. **Save to Pico**
   replaces only its active profile, verifies it by reading it back, and persists it
   across unplugging.

Keyboard shortcuts, media controls, text, keyboard macros and lighting work with the
app fully quit. Scripts, app launch/focus, URLs and computer-side sequences require
the background companion. Closing the window fully quits the app and companion,
as do **Quit Keypad Studio**, **⌘Q** on Mac, and **Quit** in the Dock or tray menu.
Unsaved edits offer Save, Discard, or Cancel. To hide the editor while keeping
computer-side actions available, choose **File → Keep companion running** (also
available from the menu-bar/tray icon). Launch the app at login using the
operating system's Login Items / Startup Apps if desired.

**Set up Pico** provides backup, CircuitPython upgrade and firmware installation
steps. Normal operation hides the CIRCUITPY drive so only firmware writes its files.
See [firmware setup and recovery](docs/firmware.md).

## Appearance

Use the top-right selector for **Dark gray**, **Light**, or **Follow system**. Your
choice stays on this computer and does not change any Pico lighting values. Both
themes use neutral surfaces from the [shadcn v3 palette](https://v3.shadcn.com/colors),
with readable text, visible focus indicators and muted dark-mode accents, informed
by the [UX Design Institute guide](https://www.uxdesigninstitute.com/blog/dark-mode-design-practical-guide/).

<details>
<summary>Compare light and dark-gray themes</summary>

| Light | Dark gray |
| --- | --- |
| ![Keypad Studio light theme](images/editor-light.png) | ![Keypad Studio dark-gray theme](images/editor-dark.png) |

</details>

<details>
<summary>Original connected-device screenshot</summary>

![Original Keypad Studio screenshot with a connected Pico](images/keypad-studio.jpg)

</details>

## Starter profiles

**Current Pico** reproduces the connected device's shortcuts, media keys, animations,
and locally tracked toggles, with Mac variants. Script keys use the reliable direct
runner by default. Open the inspector's **Key options** menu (•••) and choose
**Use a legacy script-launch macro** to use standalone
Windows PowerShell launch sequences instead; edit their text steps to set your path.
The original text-entry key is intentionally empty until re-entered.

**Classic Conference** preserves the earlier Teams/Discord layout, including the ZIP
extraction key that the old firmware did not dispatch. Application volume controls
work on Windows; these bindings are unassigned on macOS. Configure local paths before
using script, sound, download or app-specific actions.

Shortcut-driven colors track presses, not the actual application mute state. Use
Learn / diagnostic mode to confirm the physical positions before saving mappings.
The default view has the Pico at the top: keys 1–4 across the first row, 13–16 across
the last. The physical corner positions were checked on the connected device.

## Run from source

Python 3.10–3.13 (3.11 recommended):

```sh
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m keypad_studio
```

Use `--learn` to start with physical actions suppressed, or `--no-device` for a
hardware-free editor. Mac computer-side keyboard injection may require Accessibility
permission; standalone USB keyboard actions do not use that permission.

Settings and profiles normally live in the OS application-data directory. Set
`KEYPAD_HOME` to choose a different directory. Machine-specific paths are separate
from exported/device profiles. Only one companion instance runs at a time.

## Build standalone applications

```sh
python tools/build_firmware.py
python tools/build_app.py
```

The Mac result is `dist/Keypad Studio.app`; Windows produces
`dist/Keypad Studio/Keypad Studio.exe`. Build on each target OS. Users do not need
Python to run these packages. Running their own Python scripts still requires a
chosen Python interpreter. The included GitHub Actions workflow tests and packages
Mac and Windows independently. Local builds are unsigned; signing/notarization can
be added for public distribution using the publisher's credentials.

Open **Keypad Studio.app** in Finder on Mac. The application bundle includes the
blue keypad icon for Finder and the Dock; Windows builds embed the same artwork.
The icon source is `keypad_studio/assets/app-icon.svg`. To regenerate its PNG,
ICNS and ICO files after editing it, run `python tools/build_icons.py` before building.

To create and smoke-test the local download package, run
`python tools/package_release.py --target macOS-arm64`, `--target macOS-x86_64`,
or `--target Windows-x64` on the matching computer. Versioned DMG/ZIP files and
their checksums are written to `release-assets/`.

The **Build and release** workflow tests, builds, and packages all three targets on
pushes and pull requests. Pushing a `vX.Y.Z` tag matching the project version also
publishes a GitHub release after every client passes its packaged-app checks.
Release assets are uploaded as a draft, verified, and then published together.

## Develop and extend

- `keypad_core/`: portable schema, effects, cooperative scheduler, storage and protocol.
- `keypad_studio/`: editor, local library, USB worker, script runner and OS adapters.
- `firmware/`: CircuitPython entry points and the small hardware adapter.
- `tests_v2/`: isolated automated tests; old `tests/` files are historical scripts that
  can trigger real automation and are deliberately excluded from test discovery.
- [Profile/action/protocol reference](docs/profile-format.md), including script feedback.
- [Validation results and remaining platform checks](docs/validation.md).
- [Interface design and UI Skills guidance](docs/interface-design.md).
- `examples/progress_script.py`: a script that reports progress and a key state.

```sh
python -m pytest
python -m black --line-length 100 keypad_core keypad_studio firmware tools tests_v2 examples
```

The original `script.py`, `pico_code.py`, images and audio remain available for
reference. Their original documentation is in [the legacy README](docs/legacy-readme.md).
