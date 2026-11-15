# Validation — 10 November 2026

Local environment: macOS 15.6.1, Apple Silicon, Python 3.11.11. Connected hardware:
original RP2040 Pico, Pimoroni RGB Keypad Base, CircuitPython 10.3.1.

## Automated and packaged-app checks

- 33 tests pass: schema/size limits, debounce, repeat/hold/release, concurrent keys,
  nonblocking macros, diagnostic suppression, state restoration, German layouts,
  checksummed slot recovery, stale revisions, streaming transfers, editor edits,
  script output/failure/timeout/cancellation, ZIP extraction, theme preference and
  text contrast, and independent settings for newly assigned scripts.
- Formatting, compilation and Git whitespace checks pass.
- Mac ARM64 standalone app built with PyInstaller; launched from a temporary
  directory with only system directories on PATH, without the source environment.
- Packaged firmware manifest and packaged ZIP-extraction helper verified.
- Light and dark-gray themes rendered and visually reviewed; normal text token
  pairs meet at least 4.5:1 contrast, with visible keyboard focus indicators.

## Physical device checks

- User confirmed corner positions 1, 4, 13, 16 with the Pico at the top.
- German Mac USB text output, including Y/Z, case, punctuation, brackets, backslash,
  Option characters and umlauts, exactly matched a dedicated input field. Output
  was sent only after verifying the test process owned the focused input window.
- A 6,763-byte profile saved and read back correctly; preview left saved data
  unchanged; stale revisions were rejected; the profile survived a device restart.
- The user's saved Current Pico profile was restored and verified afterward.
- Three-second rainbow-animation sample: 29.1 LED frames/second, 425.7 switch scans/
  second, maximum observed scan gap 24 ms, 105,568 bytes free heap.
- A memory spike found in the fuller device test was corrected by streaming reads,
  preallocating upload storage, avoiding duplicate JSON parsing and releasing the
  startup profile reference. The full device test then passed.

## Remaining platform/application checks

Windows CI/build instructions are included, but a Windows build and physical
Windows test were not run locally. Windows audio/window adapters and German Windows
HID mappings still need validation on Windows. Live Teams/Discord meeting behavior
was not exercised; presets remain editable shortcuts and locally tracked states.
The animation figures above are a short sample, not a long-duration benchmark.

Opt-in hardware utilities are `tools/hardware_smoke.py` and `tools/hid_input_check.py`.
The smoke utility temporarily changes the active device profile; quit the companion
first and keep a private backup before running it. The HID check is Mac-specific.

## Interface polish — 15 November 2026

- 36 tests pass, including compact layout checks in both themes and action/state
  editing with friendly labels that retain the existing protocol values.
- Light and dark-gray layouts were visually reviewed at 1400 × 940 and 1100 × 760.
  All 16 keys, device preview controls, and the fixed Test action footer fit without
  overlapping. Lighting and Activity tabs were also reviewed at the compact size.
- Original README banner, badges, keypad photograph, and connected-device
  screenshot are retained alongside refreshed theme screenshots.
- The updated Mac ARM64 application was packaged and launched with isolated
  settings, no device connection, and only system directories on PATH. Its native
  UI, SVG icons, and bundled icon license were checked.
- This pass changes the desktop interface; firmware and the saved Pico profile
  were not changed.

## Quit behavior and primary button — 15 November 2026

- All 43 automated tests pass.
- Window close now quits; hiding the editor while keeping the companion running
  requires the explicit menu choice. Native Quit, the Quit shortcut, and tray Quit
  share one shutdown path.
- Isolated Qt event-loop regressions cover close, native Quit events, the actual
  assigned shortcut, background/reopen, quit while hidden, and Save/Discard/Cancel.
  Each exits with the script process stopped, USB worker stopped, and singleton
  socket released. Shutdown polls asynchronously rather than blocking the GUI.
- Actual Cocoa windows also passed Command-Q and macOS normal-termination checks,
  with the disposable script, USB worker, and singleton socket fully released.
  The rebuilt standalone app exited successfully through window close.
- Save to Pico uses white text on `#2563EB` (5.17:1 contrast); selection and focus
  accents retain `#3A86FF`.

## Native application icon — 15 November 2026

- Shared vector artwork generates a transparent 1024px PNG, multi-resolution macOS
  ICNS, and Windows ICO. Runtime and native packages use the same blue keypad.
- The Mac build verifies `CFBundleIconFile` and the embedded ICNS bytes. After
  targeted Launch Services registration, macOS `NSWorkspace.iconForFile` resolved
  the correct blue keypad icon for the `.app` file itself.
- The rebuilt standalone app launched and closed successfully with isolated
  settings, no device connection, and only system directories on PATH.
