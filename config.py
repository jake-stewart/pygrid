from utils import hex2rgb

one_dark_theme = {
    "background_color": hex2rgb("#282C34"),
    "cell_color":       hex2rgb("#ABB2BF"),
    "grid_color":       hex2rgb("#474D58"),
    "red":              hex2rgb("#E06C75"),
    "green":            hex2rgb("#98C379"),
    "blue":             hex2rgb("#61AFEF"),
    "yellow":           hex2rgb("#E5C07B"),
    "magenta":          hex2rgb("#C678DD"),
    "cyan":             hex2rgb("#56B6C2"),
}

boring_theme = {
    "background_color": hex2rgb("#FFFFFF"),
    "cell_color":       hex2rgb("#000000"),
    "grid_color":       hex2rgb("#888888"),
    "red":              hex2rgb("#FF0000"),
    "green":            hex2rgb("#00FF00"),
    "blue":             hex2rgb("#0000FF"),
    "yellow":           hex2rgb("#FFFF00"),
    "magenta":          hex2rgb("#FF00FF"),
    "cyan":             hex2rgb("#00FFFF"),
}

gruvbox_dark_theme = {
    "background_color": hex2rgb("#282828"),
    "cell_color":       hex2rgb("#EBDBB2"),
    "grid_color":       hex2rgb("#625A52"),
    "red":              hex2rgb("#FB4934"),
    "green":            hex2rgb("#B8BB26"),
    "blue":             hex2rgb("#83A598"),
    "yellow":           hex2rgb("#FABD2F"),
    "magenta":          hex2rgb("#D3859B"),
    "cyan":             hex2rgb("#83A598"),
}

gruvbox_light_theme = {
    "background_color": hex2rgb("#FBF1C7"),
    "cell_color":       hex2rgb("#3C3836"),
    "grid_color":       hex2rgb("#928374"),
    "red":              hex2rgb("#CC241D"),
    "green":            hex2rgb("#98971A"),
    "blue":             hex2rgb("#458588"),
    "yellow":           hex2rgb("#D79921"),
    "magenta":          hex2rgb("#B16286"),
    "cyan":             hex2rgb("#689D6A"),
}

solarized_dark_theme = {
    "background_color": hex2rgb("#002B36"),
    "cell_color":       hex2rgb("#EEE8D5"),
    "grid_color":       hex2rgb("#39575F"),
    "red":              hex2rgb("#DC322F"),
    "green":            hex2rgb("#859900"),
    "blue":             hex2rgb("#268BD2"),
    "yellow":           hex2rgb("#B58900"),
    "magenta":          hex2rgb("#6C71C4"),
    "cyan":             hex2rgb("#2AA198"),
}

config = one_dark_theme
config["fps"] = 60
config["grid_percentage"] = 0.1
