from keypad_studio.themes import PALETTES


def luminance(color):
    rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def ratio(a, b):
    a, b = sorted([luminance(a), luminance(b)])
    return (b + 0.05) / (a + 0.05)


def test_theme_text_contrast_and_neutral_dark_surfaces():
    for colors in PALETTES.values():
        for fg, bg in (
            ("text", "background"),
            ("text", "surface"),
            ("text", "raised"),
            ("muted", "background"),
            ("muted", "raised"),
            ("primary_text", "primary"),
            ("selected_text", "selected"),
            ("status", "background"),
        ):
            assert ratio(colors[fg], colors[bg]) >= 4.5, (fg, bg, colors)
        assert ratio(colors["focus"], colors["background"]) >= 3
    for key in ("background", "surface", "raised"):
        c = PALETTES["dark"][key]
        assert c[1:3] == c[3:5] == c[5:7] and c not in ("#000000", "#ffffff")
