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
