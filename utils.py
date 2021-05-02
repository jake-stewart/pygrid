def hex2rgb(hex_color):
    hex_color = hex_color.replace("#", "")
    r, g, b = [hex_color[i:i+2] for i in range(0, len(hex_color), 2)]
    return (int(r, 16), int(g, 16), int(b, 16))


def color_mix(rgb_1, rgb_2, perc):
    perc_alt = 1 - perc
    return (
        int(rgb_1[0] * perc_alt + rgb_2[0] * perc),
        int(rgb_1[1] * perc_alt + rgb_2[1] * perc),
        int(rgb_1[2] * perc_alt + rgb_2[2] * perc)
    )
