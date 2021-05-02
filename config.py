from utils import hex2rgb

one_dark_theme = {
    "background_color": hex2rgb("#282C34"),
    "cell_color":       hex2rgb("#ABB2BF"),
    "grid_color":       hex2rgb("#5C6370"),
    "red":              hex2rgb("#E06C75"),
    "green":            hex2rgb("#98C379"),
    "blue":             hex2rgb("#61AFEF"),
    "yellow":           hex2rgb("#E5C07B"),
    "magenta":          hex2rgb("#C678DD"),
    "cyan":             hex2rgb("#56B6C2"),
}

boring_theme = {
    "background_color": hex2rgb("#ffffff"),
    "cell_color":       hex2rgb("#000000"),
    "grid_color":       hex2rgb("#888888"),
    "red":              hex2rgb("#ff0000"),
    "green":            hex2rgb("#00ff00"),
    "blue":             hex2rgb("#0000ff"),
    "yellow":           hex2rgb("#ffff00"),
    "magenta":          hex2rgb("#ff00ff"),
    "cyan":             hex2rgb("#00ffff"),
}

gruvbox_dark_theme = {
    "background_color": hex2rgb("#282828"),
    "cell_color":       hex2rgb("#ebdbb2"),
    "grid_color":       hex2rgb("#928374"),
    "red":              hex2rgb("#fb4934"),
    "green":            hex2rgb("#b8bb26"),
    "blue":             hex2rgb("#83a598"),
    "yellow":           hex2rgb("#fabd2f"),
    "magenta":          hex2rgb("#d3859b"),
    "cyan":             hex2rgb("#83a598"),
}

gruvbox_light_theme = {
    "background_color": hex2rgb("#fbf1c7"),
    "cell_color":       hex2rgb("#3c3836"),
    "grid_color":       hex2rgb("#928374"),
    "red":              hex2rgb("#cc241d"),
    "green":            hex2rgb("#98971a"),
    "blue":             hex2rgb("#458588"),
    "yellow":           hex2rgb("#d79921"),
    "magenta":          hex2rgb("#b16286"),
    "cyan":             hex2rgb("#689d6a"),
}

solarized_dark_theme = {
    "background_color": hex2rgb("#002b36"),
    "cell_color":       hex2rgb("#eee8d5"),
    "grid_color":       hex2rgb("#586e75"),
    "red":              hex2rgb("#dc322f"),
    "green":            hex2rgb("#859900"),
    "blue":             hex2rgb("#268bd2"),
    "yellow":           hex2rgb("#b58900"),
    "magenta":          hex2rgb("#6c71c4"),
    "cyan":             hex2rgb("#2aa198"),
}

config = one_dark_theme
config["fps"] = 60
config["grid_thickness"] = 1
