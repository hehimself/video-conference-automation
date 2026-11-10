# Profiles and extension points

Profiles are UTF-8 JSON, `schema_version: 1`. See `keypad_core/schema.py` for
validation and `keypad_studio/presets.py` for complete examples. Key IDs are raw
hardware indices, 0–15; the UI displays 1–16. Rotation changes the view without
renumbering keys. Each key contains a label, `hold_ms`, `repeat_ms`, lighting and
`bindings.windows` / `bindings.macos`. Each platform maps `press`, `hold` and
`release` to actions. Press fires immediately; hold is an additional action after
the threshold. Repeat replays press while held. A busy key drops repeat events
rather than queuing a backlog. Different keys continue independently.

## Actions

| Type | Fields | Execution |
|---|---|---|
| `none` | — | Pico |
| `hotkey` | `keys`: array, e.g. `["cmd","shift","m"]` | Pico |
| `text` | `text`: up to 2048 characters | Pico |
| `media` | `code`: volume_up/down, mute, play_pause, next/previous_track | Pico |
| `delay` | `ms`: 0–60000 | Pico |
| `sequence` | `steps`: up to 32 actions, nesting up to four levels | Pico if all steps are independent; otherwise companion |
| `toggle` | — | Local on/off state |
| `effect` | `effect`: lighting settings; `scope`: board/key | Pico |
| `run_script` | `binding_id` | Companion |
| `open_app`, `focus_app` | `binding_id`, optional `app` | Companion |
| `open_url` | `binding_id`, optional `url` | Companion |
| `play_sound` | `binding_id` | Companion |
| `app_volume` | `binding_id`, `app`, `delta`: -1…1 | Windows companion |
| `extract_zip` | `binding_id` | Companion |

An optional per-key `alternate` platform action implements alternating shortcuts,
used by Current Pico's minimize/restore button. Toggle state resets when profiles
load or the device restarts; it does not represent verified application state.

Host paths live in `computer-settings.json` in the application data directory,
under `bindings.<binding_id>.<platform>`. These override descriptive defaults in a
profile and are not exported or uploaded. Computer Settings supports executable,
script/sound path, arguments and interpreter flags (JSON string arrays), working directory, application,
URL, download/extraction paths and timeout (1–3600 seconds).

Text uses the saved `de_windows`, `de_macos`, or `us` keyboard layout. German Mac
and Windows use different Option/AltGr mappings. Text is prevalidated before any
characters are sent. Unsupported characters produce an error instead of typing a
partial command. Shortcuts use named letters and translate German Y/Z usages.

## Lighting

Effects contain `name`, RGB `color` (0–255), `speed` (0.05–20), `duration`
(0.05–60 seconds) and `direction` (right/left/down/up). A profile supplies whole-pad
idle lighting and brightness 0–1. Keys can override idle/pressed/on/off/running/
success/error styles. Temporary full-pad effects replace idle colors, with state
indicators above them. Press/running/result feedback takes precedence. Expired
effects restore the underlying current state. Procedural calculations are shared
between the UI and firmware in `keypad_core/effects.py`.

## Scripts

Choose an explicit executable/interpreter. Python, PowerShell, shell scripts and
native executables can be used; arguments are passed directly without a shell.
For shell scripts choose `/bin/zsh`, `/bin/bash`, or `powershell.exe` as applicable.
Scripts inherit the user's environment and receive:

- `KEYPAD_KEY_ID`: zero-based key ID
- `KEYPAD_PROFILE_ID`: active profile ID
- `KEYPAD_OS`: `macos` or `windows`

Ordinary stdout/stderr appears in Activity. Flush one JSON object per line for
optional feedback on the triggering key:

```json
{"type":"state","state":"on"}
{"type":"progress","value":0.5}
```

States are `on` or `off`; progress ranges from 0 to 1. Exit code zero gives success;
other exits, timeouts and cancellation give error. Timeouts kill the launched
process; scripts that create their own detached processes must manage those
processes themselves. Imported profiles never execute scripts on import or preview.

The packaged application includes Python for itself; running an external `.py`
script still requires selecting a suitable Python interpreter on that computer.

## USB protocol v1

CDC DATA receives newline-delimited JSON, maximum 1400 bytes per line:

```json
{"v":1,"id":1,"cmd":"hello","args":{}}
```

Replies are `{"id":1,"ok":true,"result":{...}}` or `ok:false` with `error`.
Commands: hello, heartbeat, diagnostic, stats, cancel, read_begin/read_chunk,
write_begin/write_chunk/write_commit, preview_stop, feedback, execute, maintenance.
Profile chunks are 384 bytes encoded as Base64. The initial write declares size,
SHA-256, current revision and whether it is a preview. Offsets must be contiguous;
commit verifies size, hash and the profile schema. Device profiles are limited to
16 KiB. Both starter profiles are under 7 KiB.

The hello reply includes firmware/protocol versions, boot session, event floor,
revision and resource limits. New connections discard events at or below the
event floor. Host actions require a five-second companion heartbeat lease and are
never replayed on reconnection. `execute` accepts only validated device actions,
with an execution ID; completion events keep mixed sequences ordered.

Diagnostic mode suppresses physical actions and requires renewal every 15 seconds;
held keys must be released before actions resume. Explicit Test can still execute
an action. Previews expire after 30 seconds, restore the saved profile, and never
write flash. A/B save slots retain checksummed revisions; startup chooses the newest
valid slot. FAT filesystem failure can still require BOOTSEL recovery; A/B protects
profile writes, not against every possible filesystem failure.
