# cells
EMPTY = -1
WALL = 7

# tetro rotations
TETROS = [
    [
        [(1, 0), (1, 1), (1, 2), (1, 3)],  # I
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)]
    ],
    [
        [(1, 0), (1, 1), (1, 2), (0, 2)],  # J
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(2, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)]
    ],
    [
        [(1, 0), (1, 1), (1, 2), (2, 2)],  # L
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(2, 0), (0, 1), (1, 1), (2, 1)]
    ],
    [
        [(0, 0), (1, 0), (1, 1), (0, 1)]   # O
    ],
    [
        [(0, 1), (1, 1), (1, 0), (2, 0)],  # S
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)]
    ],
    [
        [(0, 0), (1, 0), (2, 0), (1, 1)],  # T
        [(2, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (0, 2), (1, 2), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (0, 2)]
    ],
    [
        [(0, 0), (1, 0), (1, 1), (2, 1)],  # Z
        [(2, 0), (2, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (1, 1), (0, 1), (0, 2)]
    ]
]

# tetro blueprints must be sorted by y
# this is so when we join rows, we know the first affected rows
# are lower on the board, since they would have been processed first
# (used when collapsing rows, and more efficient to have it already sorted
# vs sorting every time)

# this function is not needed since the tetros are already correct,
# but it can help stop breakages if someone adds their own tetro
for tetro in TETROS:
    for rotation in tetro:
        rotation.sort(key=lambda x: x[1])


TETRO_HEIGHTS = [
    tetro[0][-1][1] + 1 for tetro in TETROS
]

# next tetro and stored tetro previews
# true/false indicates whether width of preview is odd
PREVIEWS = [
    [[(2, 1), (2, 2), (2, 3), (2, 4)], True],
    [[(3, 2), (3, 3), (3, 4), (2, 4)], False],
    [[(2, 2), (2, 3), (2, 4), (3, 4)], False],
    [[(2, 2), (3, 2), (2, 3), (3, 3)], False],
    [[(1, 3), (2, 3), (2, 2), (3, 2)], True],
    [[(1, 2), (2, 2), (3, 2), (2, 3)], True],
    [[(1, 2), (2, 2), (2, 3), (3, 3)], True]
]


# glyphs for displaying score

NO_GLYPH = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
]

NUMBER_GLYPHS = [
    [
        [1, 1, 1],  # zero
        [1, 0, 1],
        [1, 0, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    [
        [0, 1, 0],  # one
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0]
    ],
    [
        [1, 1, 1],  # two
        [0, 0, 1],
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 1]
    ],
    [
        [1, 1, 1],  # three
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ],
    [
        [1, 0, 1],  # four
        [1, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [0, 0, 1]
    ],
    [
        [1, 1, 1],  # five
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ],
    [
        [1, 1, 1],  # six
        [1, 0, 0],
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    [
        [1, 1, 1],  # seven
        [0, 0, 1],
        [0, 0, 1],
        [0, 0, 1],
        [0, 0, 1]
    ],
    [
        [1, 1, 1],  # eight
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    [
        [1, 1, 1],  # nine
        [1, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ],
]
