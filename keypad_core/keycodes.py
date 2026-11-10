"""USB usage codes, plus explicit German Windows/Mac text mappings."""

NAMES = {
    "ctrl": 224,
    "control": 224,
    "shift": 225,
    "alt": 226,
    "option": 226,
    "cmd": 227,
    "win": 227,
    "gui": 227,
    "altgr": 230,
    "enter": 40,
    "escape": 41,
    "esc": 41,
    "backspace": 42,
    "tab": 43,
    "space": 44,
    "delete": 76,
    "home": 74,
    "end": 77,
    "right": 79,
    "left": 80,
    "down": 81,
    "up": 82,
    "pageup": 75,
    "pagedown": 78,
}
for _i, _char in enumerate("abcdefghijklmnopqrstuvwxyz"):
    NAMES[_char] = 4 + _i
for _i, _char in enumerate("1234567890"):
    NAMES[_char] = 30 + _i
for _i in range(1, 13):
    NAMES["f%d" % _i] = 57 + _i


def chord(names):
    if not isinstance(names, list) or not 1 <= len(names) <= 6:
        raise ValueError("A shortcut needs 1–6 key names")
    try:
        return tuple(NAMES[n.lower()] for n in names)
    except (KeyError, AttributeError):
        raise ValueError("Unsupported shortcut key")


_US_PLAIN = "-=[]\\;',./`"
_US_SHIFT = '_+{}|:"<>?~'
_US_CODES = (45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 53)
_DE_PLAIN = {
    "ß": 45,
    "ü": 47,
    "+": 48,
    "#": 49,
    "ö": 51,
    "ä": 52,
    ",": 54,
    ".": 55,
    "-": 56,
    "<": 100,
}
_DE_SHIFT = {
    "!": 30,
    '"': 31,
    "§": 32,
    "$": 33,
    "%": 34,
    "&": 35,
    "/": 36,
    "(": 37,
    ")": 38,
    "=": 39,
    "?": 45,
    "Ü": 47,
    "*": 48,
    "'": 49,
    "Ö": 51,
    "Ä": 52,
    ";": 54,
    ":": 55,
    "_": 56,
    ">": 100,
    "°": 53,
}


def character(char, layout):
    """Return one or more tuples of usages; dead accents also emit space."""
    if char in ("\n", "\t", "\b", " "):
        return [({"\n": 40, "\t": 43, "\b": 42, " ": 44}[char],)]
    if char.lower() in "abcdefghijklmnopqrstuvwxyz":
        c = char.lower()
        if layout != "us":
            c = {"y": "z", "z": "y"}.get(c, c)
        return [((225,) if char.isupper() else ()) + (NAMES[c],)]
    if char in "0123456789":
        return [(NAMES[char],)]
    if layout == "us":
        if char in _US_PLAIN:
            return [(_US_CODES[_US_PLAIN.index(char)],)]
        if char in _US_SHIFT:
            return [(225, _US_CODES[_US_SHIFT.index(char)])]
        shifted = "!@#$%^&*()"
        if char in shifted:
            return [(225, 30 + shifted.index(char))]
    else:
        if char in _DE_PLAIN:
            return [(_DE_PLAIN[char],)]
        if char in _DE_SHIFT:
            return [(225, _DE_SHIFT[char])]
        if char in ("^", "`", "´"):
            return [{"^": (53,), "`": (225, 46), "´": (46,)}[char], (44,)]
        if layout == "de_windows":
            alt = {
                "@": 20,
                "[": 37,
                "\\": 45,
                "]": 38,
                "{": 36,
                "|": 100,
                "}": 39,
                "~": 48,
                "€": 8,
                "µ": 16,
            }
            if char in alt:
                return [(230, alt[char])]
        elif layout == "de_macos":
            alt = {"@": 15, "[": 34, "]": 35, "{": 37, "}": 38, "|": 36, "€": 8, "µ": 16}
            if char in alt:
                return [(226, alt[char])]
            if char == "\\":
                return [(226, 225, 36)]
            if char == "~":
                return [(226, 17), (44,)]
    raise ValueError("Character not supported by %s: U+%04X" % (layout, ord(char)))
