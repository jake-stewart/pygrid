from pygrid import PyGrid
from keycodes import *
from tetris_data import *
from utils import color_mix
import random
import math

# game states
PAUSED = 0
PLAYING = 1
DROPPING = 2
DEAD = 3


# keybindings
ROTATE_KEYS = {KEY_UP,    KEY_K, KEY_W}
LEFT_KEYS   = {KEY_LEFT,  KEY_H, KEY_A}
DOWN_KEYS   = {KEY_DOWN,  KEY_J, KEY_S}
RIGHT_KEYS  = {KEY_RIGHT, KEY_L, KEY_D}

STORE_KEYS  = {KEY_Q, KEY_ESCAPE}
PAUSE_KEY = KEY_P
DROP_KEY = KEY_SPACE


class TetrisGrid(PyGrid):
    ui_width = 14
    ui_height = 19

    def __init__(self, background_color, cell_color, cyan, yellow,
                 magenta, green, blue, red, orange, cell_size=20, fps=60,
                 board_width=10, board_height=20, difficulty_rate=1,
                 left_padding=1, right_padding=1, top_padding=1, bottom_padding=1,
                 min_hold_time=5, ticks_per_drop=15, tick_speed=0.05, animate=True,
                 fancy_drop=False):

        self.red = red
        self.animate = animate
        self.fancy_drop = fancy_drop

        self.dropping = False

        self.cell_color = cell_color
        self.score = 0
        self.difficulty = 0
        self.level_cap = difficulty_rate
        self.difficulty_rate = difficulty_rate

        self.game_state = PLAYING
        self.old_game_state = PLAYING

        self.next_preview_odd = False
        self.stored_preview_odd = False

        self.ones_glyph = NO_GLYPH
        self.tens_glyph = NO_GLYPH
        self.hundreds_glyph = NO_GLYPH

        self.stored_tetro = None
        self.current_tetro = None
        self.next_tetro = self.get_random_tetro()

        self.colors = [cyan, yellow, magenta, green, blue, red, orange]
        self.preview_colors = [
            color_mix(background_color, color, 0.15) for color in self.colors
        ]

        self.left_padding = left_padding
        self.right_padding = right_padding
        self.top_padding = top_padding
        self.bottom_padding = bottom_padding

        self.board_left_padding = left_padding + 1
        self.board_top_padding = top_padding + 1

        self.board_width = board_width

        if board_height + 2 < self.ui_height:
            self.board_height = self.ui_height - 2
        else:
            self.board_height = board_height

        self.x_vel = 0
        self.y_vel = 0
        self.hold_time = 0
        self.min_hold_time = min_hold_time
        self.tick = 0
        self.default_ticks_per_drop = ticks_per_drop
        self.ticks_per_drop = ticks_per_drop


        screen_width = board_width + left_padding + right_padding + self.ui_width
        screen_height = board_height + top_padding + bottom_padding + 2


        self.next_tetro_display_x = screen_width - right_padding - 6
        self.next_tetro_display_y = top_padding

        self.stored_tetro_display_x = screen_width - right_padding - 6
        self.stored_tetro_display_y = top_padding + 7

        self.number_display_positions = [
            screen_width - right_padding - 3,
            screen_width - right_padding - 7,
            screen_width - right_padding - 11
        ]
        self.number_display_y = screen_height - bottom_padding - 5


        PyGrid.__init__(
            self,
            n_columns=screen_width,
            n_rows=screen_height,
            cell_size=cell_size,
            allowed_resize=False,
            allowed_pan=False,
            allowed_zoom=False,
            background_color=background_color,
            animation_duration=0.1,
            grid_thickness=0,
            fps=fps
        )

        self.drop_tick_speed = 0.01
        self.fall_tick_speed = tick_speed
        self.set_timer(self.fall_tick_speed)
        self.create_board()

    def get_random_tetro(self):
        return random.randint(0, len(TETROS) - 1)

    def new_tetro(self):
        self.current_tetro = self.next_tetro
        self.generate_next_tetro()
        self.can_store = True

        self.x = self.board_width // 2 - 1
        self.y = -TETRO_HEIGHTS[self.current_tetro]
        self.rotation = 0

        self.find_preview()
        self.draw_preview(animate=self.animate)
        self.draw_tetro()

    def draw_preview(self, animate):
        for x, y in TETROS[self.current_tetro][self.rotation]:
            if self.preview_y + y < 0:
                continue

            self.draw_cell(
                self.board_left_padding + self.x + x,
                self.board_top_padding + self.preview_y + y,
                self.preview_colors[self.current_tetro],
                animate=animate
            )

    def erase_preview(self, animate=False):
        for x, y in TETROS[self.current_tetro][self.rotation]:
            if self.preview_y + y < 0:
                continue

            self.erase_cell(
                self.board_left_padding + self.x + x,
                self.board_top_padding + self.preview_y + y,
                animate=animate
            )

    def place_tetro(self):
        full_rows = []
        for x, y in TETROS[self.current_tetro][self.rotation]:
            self.rows[self.y + y][self.x + x] = self.current_tetro
            self.row_totals[self.y + y] += 1
            if self.row_totals[self.y + y] == self.board_width:
                full_rows.append(self.y + y)

        if full_rows:
            self.score += len(full_rows)
            self.difficulty += 1
            self.set_difficulty()
            self.draw_score(self.cell_color)
            self.collapse_rows(full_rows)

        self.new_tetro()


    def set_difficulty(self):
        if self.ticks_per_drop == 1:
            return

        new_level, self.difficulty = divmod(self.difficulty, self.level_cap)

        if new_level:
            self.level_cap += self.difficulty_rate
            self.ticks_per_drop -= 1

    def erase_next_tetro(self):
        preview, is_odd = PREVIEWS[self.next_tetro]
        for x, y in preview:
            self.erase_cell(
                self.next_tetro_display_x + x,
                self.next_tetro_display_y + y,
                animate=self.animate
            )

    def convert_odd_preview(self, x, y):
        for row in range(1, 5):
            self.erase_cell(x, y + row, animate=self.animate)

        for row in range(6):
            self.draw_cell(
                x - 1, y + row,
                self.cell_color,
                animate=self.animate
            )

    def convert_even_preview(self, x, y):
        for row in range(6):
            self.erase_cell(x - 1, y + row, animate=self.animate)

        for row in range(1, 5):
            self.draw_cell(
                x, y + row,
                self.cell_color,
                animate=self.animate
            )

    def erase_stored_tetro(self):
        if self.stored_tetro is None:
            return
        preview, is_odd = PREVIEWS[self.stored_tetro]
        for x, y in preview:
            self.erase_cell(
                self.stored_tetro_display_x + x,
                self.stored_tetro_display_y + y,
                animate=self.animate
            )

    def draw_stored_tetro(self):
        preview, is_odd = PREVIEWS[self.stored_tetro]
        if is_odd != self.stored_preview_odd:
            if is_odd:
                self.convert_odd_preview(
                    self.stored_tetro_display_x,
                    self.stored_tetro_display_y
                )
            else:
                self.convert_even_preview(
                    self.stored_tetro_display_x,
                    self.stored_tetro_display_y
                )

        self.stored_preview_odd = is_odd

        for x, y in preview:
            self.draw_cell(
                self.stored_tetro_display_x + x,
                self.stored_tetro_display_y + y,
                self.colors[self.stored_tetro],
                animate=self.animate
            )

    def draw_next_tetro(self):
        preview, is_odd = PREVIEWS[self.next_tetro]
        if is_odd != self.next_preview_odd:
            if is_odd:
                self.convert_odd_preview(
                    self.next_tetro_display_x,
                    self.next_tetro_display_y
                )
            else:
                self.convert_even_preview(
                    self.next_tetro_display_x,
                    self.next_tetro_display_y
                )

        self.next_preview_odd = is_odd

        for x, y in preview:
            self.draw_cell(
                self.next_tetro_display_x + x,
                self.next_tetro_display_y + y,
                self.colors[self.next_tetro],
                animate=self.animate
            )

    def draw_tetro(self):
        for x, y in TETROS[self.current_tetro][self.rotation]:
            if self.y + y < 0:
                continue

            self.draw_cell(
                self.board_left_padding + self.x + x,
                self.board_top_padding + self.y + y,
                self.colors[self.current_tetro]
            )

    def erase_tetro(self, animate=False):
        for x, y in TETROS[self.current_tetro][self.rotation]:
            if self.y + y < 0:
                continue

            self.erase_cell(
                self.board_left_padding + self.x + x,
                self.board_top_padding + self.y + y,
                animate=animate
            )

    def find_preview(self):
        self.preview_y = self.y
        collision = False
        while not collision:
            self.preview_y += 1
            collision = self.collision(
                self.x, self.preview_y,
                self.current_tetro, self.rotation
            )
        self.preview_y -= 1

    def collision(self, x1, y1, tetro, rotation):
        for x2, y2 in TETROS[tetro][rotation]:
            if not 0 <= x1 + x2 < self.board_width:
                return True
            if y1 + y2 < 0:
                continue
            if self.rows[y1 + y2][x1 + x2] >= 0:
                return True
        return False

    def rotate(self):
        new_rotation = (self.rotation + 1) % len(TETROS[self.current_tetro])

        if self.collision(self.x, self.y, self.current_tetro, new_rotation):
            return

        self.erase_preview(animate=False)
        self.erase_tetro(animate=False)

        self.rotation = new_rotation
        self.find_preview()
        self.draw_preview(animate=False)
        self.draw_tetro()

    def move(self, direction):
        if not direction:
            return

        collision = self.collision(
            self.x + direction,
            self.y,
            self.current_tetro,
            self.rotation
        )

        if collision:
            return

        self.erase_tetro(animate=False)
        self.erase_preview(animate=False)
        self.x += direction
        self.find_preview()
        self.draw_preview(animate=False)
        self.draw_tetro()

    def fall(self):
        if self.y == self.preview_y:
            # game over
            if self.y <= 0:
                self.game_state = DEAD
                self.ones_glyph = NO_GLYPH
                self.tens_glyph = NO_GLYPH
                self.hundreds_glyph = NO_GLYPH
                self.erase_score()
                self.draw_screen(self.red)
                self.stop_timer()
                return

            self.place_tetro()
            return True

        else:
            animate = self.fancy_drop and self.game_state == DROPPING
            self.erase_tetro(animate=animate)
            self.y += 1
            self.draw_tetro()
            return False

    def collapse_rows(self, full_rows):
        for row in full_rows:
            del self.rows[row]
            del self.row_totals[row]
            self.rows.insert(0, self.empty_row.copy())
            self.row_totals.insert(0, 0)

        empties = 0
        n = 0
        for row in range(full_rows[-1], 0, -1):
            if not self.row_totals[row]:
                if empties == len(full_rows):
                    break
                empties += 1
            self.draw_row(row)
            n += 1

    def draw_row(self, row):
        for col, color in enumerate(self.rows[row]):
            if color == EMPTY:
                self.erase_cell(
                    self.board_left_padding + col,
                    self.board_top_padding + row
                )
            else:
                self.draw_cell(
                    self.board_left_padding + col,
                    self.board_top_padding + row,
                    self.colors[color]
                )


    def create_board(self):
        self.rows = []
        self.row_totals = []

        self.empty_row = [EMPTY for i in range(self.board_width)]

        for i in range(self.board_height):
            self.rows.append(self.empty_row.copy())
            self.row_totals.append(0)

        self.rows.append([WALL for i in range(self.board_width)])
        self.row_totals.append(0)

    def on_start(self):
        self.draw_screen(self.cell_color)
        self.new_tetro()
        self.start_timer()

    def draw_outline(self, x, y, w, h, color):
        for col in range(w):
            self.draw_cell(x + col, y, color, animate=self.animate)
            self.draw_cell(x + col, y + h - 1, color, animate=self.animate)

        for row in range(1, h - 1):
            self.draw_cell(x, y + row, color, animate=self.animate)
            self.draw_cell(x + w - 1, y + row, color, animate=self.animate)

    def draw_glyph(self, x1, y1, glyph, old_glyph, color):
        if glyph is old_glyph:
            return

        for y2, row in enumerate(glyph):
            for x2, pixel in enumerate(row):
                if pixel != old_glyph[y2][x2]:
                    if pixel:
                        self.draw_cell(
                            x1 + x2,
                            y1 + y2,
                            color,
                            animate=self.animate
                        )
                    else:
                        self.erase_cell(
                            x1 + x2,
                            y1 + y2,
                            animate=self.animate
                        )


    def erase_score(self):
        digits = list(map(int, str(self.score)[-3:]))

        if len(digits) > 2:
            self.draw_glyph(
                self.number_display_positions[2],
                self.number_display_y,
                NO_GLYPH,
                NUMBER_GLYPHS[digits.pop(0)],
                None
            )

        if len(digits) > 1:
            self.draw_glyph(
                self.number_display_positions[1],
                self.number_display_y,
                NO_GLYPH,
                NUMBER_GLYPHS[digits.pop(0)],
                None
            )

        self.draw_glyph(
            self.number_display_positions[0],
            self.number_display_y,
            NO_GLYPH,
            NUMBER_GLYPHS[digits.pop(0)],
            None
        )

        self.hundreds_glyph = NO_GLYPH
        self.tens_glyph = NO_GLYPH
        self.ones_glyph = NO_GLYPH

    def draw_score(self, color):
        digits = list(map(int, str(self.score)[-3:]))

        if len(digits) > 2:
            old_glyph = self.hundreds_glyph
            self.hundreds_glyph = NUMBER_GLYPHS[digits.pop(0)]
            self.draw_glyph(
                self.number_display_positions[2],
                self.number_display_y,
                self.hundreds_glyph,
                old_glyph, color
            )

        if len(digits) > 1:
            old_glyph = self.tens_glyph
            self.tens_glyph = NUMBER_GLYPHS[digits.pop(0)]
            self.draw_glyph(
                self.number_display_positions[1],
                self.number_display_y,
                self.tens_glyph,
                old_glyph, color
            )

        old_glyph = self.ones_glyph
        self.ones_glyph = NUMBER_GLYPHS[digits.pop(0)]
        self.draw_glyph(
            self.number_display_positions[0],
            self.number_display_y,
            self.ones_glyph,
            old_glyph, color
        )
        
    def draw_screen(self, color):
        # next tetro
        self.draw_outline(
            self.next_tetro_display_x - self.next_preview_odd,
            self.next_tetro_display_y,
            6 + self.next_preview_odd, 6,
            color
        )

        # stored tetro
        self.draw_outline(
            self.stored_tetro_display_x - self.stored_preview_odd,
            self.stored_tetro_display_y,
            6 + self.stored_preview_odd, 6,
            color
        )

        # tetro game screen
        self.draw_outline(
            self.left_padding, self.top_padding,
            self.board_width + 2, self.board_height + 2,
            color
        )

        self.draw_score(color)

    def on_timer(self, n_ticks):
        for n in range(n_ticks):
            if self.game_state == PLAYING:
                self.tick += 1
                self.hold_time += 1
                if self.hold_time >= self.min_hold_time:
                    self.move(self.x_vel)
                    if self.y_vel:
                        self.fall()

                if self.tick >= self.ticks_per_drop:
                    self.tick = 0
                    self.fall()

            elif self.game_state == DROPPING:
                if self.fall():
                    self.set_timer(self.fall_tick_speed)
                    self.game_state = PLAYING

        self.timer_tick()

    def reset(self):
        self.erase_tetro(animate=self.animate)
        self.erase_preview(animate=self.animate)
        for row in reversed(range(self.board_height)):
            if not self.row_totals[row]:
                break
            self.rows[row] = self.empty_row.copy()
            self.draw_row(row)
            self.row_totals[row] = 0

        self.game_state = PLAYING

        self.ticks_per_drop = self.default_ticks_per_drop
        self.level_cap = self.difficulty_rate
        self.difficulty = 0

        self.erase_next_tetro()
        self.next_tetro = self.get_random_tetro()

        self.erase_stored_tetro()
        if self.stored_preview_odd:
            self.convert_even_preview(
                self.stored_tetro_display_x,
                self.stored_tetro_display_y
            )
            self.stored_preview_odd = False

        self.stored_tetro = None

        self.erase_score()
        self.score = 0
        self.draw_screen(self.cell_color)

        self.new_tetro()
        self.set_timer(self.fall_tick_speed)
        self.start_timer()

    def on_key_up(self, key):
        if self.game_state == DEAD:
            return

        if key in LEFT_KEYS:
            if self.x_vel == -1:
                self.x_vel = 0

        elif key in RIGHT_KEYS:
            if self.x_vel == 1:
                self.x_vel = 0

        elif key in DOWN_KEYS:
            self.y_vel = 0

    def on_key_down(self, key):
        if self.game_state == DEAD:
            self.reset()
            return

        if key in ROTATE_KEYS:
            if self.game_state == PLAYING:
                self.rotate()

        elif key in DOWN_KEYS:
            self.hold_time = 0
            self.y_vel = 1

        elif key in LEFT_KEYS:
            self.hold_time = 0
            if self.game_state == PLAYING:
                self.move(-1)
            self.x_vel = -1

        elif key in RIGHT_KEYS:
            self.hold_time = 0
            if self.game_state == PLAYING:
                self.move(1)
            self.x_vel = 1

        elif key == PAUSE_KEY:
            if self.game_state == PAUSED:
                self.play()
            else:
                self.pause()

        elif key == DROP_KEY:
            if self.game_state == PLAYING:
                self.drop()

        elif key in STORE_KEYS:
            if self.game_state == PLAYING:
                self.store_tetro()

    def generate_next_tetro(self):
        self.erase_next_tetro()
        self.next_tetro = self.get_random_tetro()
        self.draw_next_tetro()

    def store_tetro(self):
        if not self.can_store:
            return

        if self.stored_tetro is None:
            new_tetro = self.next_tetro
            self.generate_next_tetro()

        else:
            collision = self.collision(
                self.x, self.y,
                self.stored_tetro,
                0
            )
            if collision:
                return

            new_tetro = self.stored_tetro

        self.erase_stored_tetro()
        self.stored_tetro = self.current_tetro
        self.draw_stored_tetro()
        self.erase_tetro(animate=self.animate)
        self.erase_preview(animate=self.animate)

        self.current_tetro = new_tetro
        self.rotation = 0
        self.x = self.board_width // 2 - 1
        self.y = -TETRO_HEIGHTS[self.current_tetro]

        self.find_preview()
        self.draw_preview(animate=self.animate)
        self.draw_tetro()

        self.can_store = False

    def drop(self):
        self.game_state = DROPPING
        self.set_timer(self.drop_tick_speed)

    def pause(self):
        self.stop_timer()
        self.old_game_state = self.game_state
        self.game_state = PAUSED

    def play(self):
        self.start_timer()
        self.game_state = self.old_game_state

if __name__ == "__main__":
    from config import config

    orange = color_mix(config["red"], config["yellow"], 0.5)
    cell_color = color_mix(config["background_color"], config["cell_color"], 0.75)

    grid = TetrisGrid(
        background_color = config["background_color"],
        cell_color       = cell_color,
        cyan             = config["cyan"],
        yellow           = config["blue"],
        magenta          = config["magenta"],
        green            = config["green"],
        blue             = config["blue"],
        red              = config["red"],
        orange           = orange,
        fps              = config["fps"]
    )
    grid.start()
