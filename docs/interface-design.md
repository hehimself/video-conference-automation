# Interface design

The desktop editor uses PySide6/Qt on both supported operating systems. Qt owns
focus, keyboard navigation, menus, dialogs, and accessibility. Fusion styling makes
control decoration consistent across platforms; text uses the system UI font.

The November 2026 polish pass used UI Skills 0.2.4:

```sh
npx ui-skills start
npx ui-skills list --category craft
npx ui-skills get baseline-ui
```

[Baseline UI](https://github.com/ibelick/ui-skills/blob/main/skills/baseline-ui/SKILL.md)
informed the hierarchy, spacing, visible labels, keyboard focus, and restrained
accents. Its web framework requirements are translated to existing Qt primitives.

- The profile library stays on the left; Duplicate and Rename are in Profile options.
  Computer settings, Import, and Export remain in the sidebar.
- The center contains the selected profile, target OS/layout, and a vertical keypad
  with the Pico at the top. Save locally belongs to the local profile; the main
  Save to Pico button is separate. Device previews sit below the keypad.
- The inspector groups action, lighting, and activity. Test action stays visible
  below all three tabs. The key options menu includes legacy script-launch macros.
- Neutral light and dark-gray surfaces share the blue accent `#3A86FF`. The primary
  button uses white text on `#2563EB` for 5.17:1 text contrast. RGB indicators use the
  profile's actual lighting colors. Appearance never edits a profile or device.
- Keys expose numbered accessible names, selection state, and full-label tooltips.
  Long names wrap or truncate. The minimum supported window is 1100 × 760.
- Lighting preview redraws stop when the editor is hidden. No decorative animation
  was introduced. Closing the window quits the application. **Keep companion
  running** is an explicit File/menu-bar/tray menu choice; **Quit**, **⌘Q**, and
  Dock → Quit all use the same cleanup and unsaved-edit handling.

Palette and control rules live in `keypad_studio/themes.py`; the board and profile
rows live in `keypad_studio/widgets.py`. The small SVG icon set is rendered locally,
with no new network or runtime dependency. Lucide/Feather notices accompany the
source package and standalone builds in `keypad_studio/LUCIDE-LICENSE.txt`.

The app's blue 4 × 4 keypad icon is shared between the runtime icon and native
packages. `keypad_studio/assets/app-icon.svg` is the source; `tools/build_icons.py`
generates the PNG, macOS ICNS, and Windows ICO variants. The Mac build checks that
`CFBundleIconFile` resolves to the correct embedded icon before completing.
