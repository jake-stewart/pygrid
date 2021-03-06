import math
import random
import sys
from collections import defaultdict
from utils import color_mix
from keycodes import MOUSE_SCROLL_UP, MOUSE_SCROLL_DOWN, MIDDLE_MOUSE
import threading

# ignore startup message
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

# timer thread status enum
TIMER_INACTIVE = 0
TIMER_ACTIVE   = 1
TIMER_ENDING   = 2

# animation index enum
ORIGINAL_COLOR = 0
CURRENT_COLOR = 1
TARGET_COLOR = 2
ANIMATION_TYPE = 3
PROGRESS = 4
DURATION = 5
DELETING = 6

class PyGrid:
    def __init__(self, n_rows=20, n_columns=20, width=0, height=0,
                 background_color=(255, 255, 255), grid_color=(50, 50, 50),
                 grid_fade_start=33, grid_fade_end=8, grid_percentage=0.1,
                 min_cell_size=4, cell_size=40, max_cell_size=1000,
                 pan_button=MIDDLE_MOUSE, fps=60, default_grid_alpha=255,
                 allowed_zoom=True, allowed_pan=True, allowed_resize=True):

        # grid demensions
        self._n_rows = n_rows
        self._n_columns = n_columns

        # user's location on grid (top left corner)
        self._pos_x = 0.0
        self._pos_y = 0.0

        # window dimensions
        self._width = width
        self._height = height

        # cell width/height
        self._cell_size = cell_size

        # user allowed to pan/zoom/resize grid?
        self._allowed_pan = allowed_pan
        self._allowed_zoom = allowed_zoom
        self._allowed_resize = allowed_resize

        self._pan_button = pan_button  # middle mouse to pan screen

        # cell size limits for zooming
        self._max_cell_size = max_cell_size
        self._min_cell_size = min_cell_size

        self._fps = fps
        self._frame_delta = int((1 / self._fps) * 900)

        self._background_color = background_color
        self._grid_color = grid_color
        self._grid_alpha = 255
        self._grid_default_alpha = default_grid_alpha
        self._color_key = (255, 0, 255)

        # mouse events are handled once per frame
        # avoids high DPI mouses causing lag
        self._mouse_moved = False
        self._mouse_position = (0, 0)  # latest mouse event pos this frame

        # stores the direction that the screen is panning, so that if the
        # direction changes, the flick trajectory wont break
        self._mouse_x_direction = 0
        self._mouse_y_direction = 0

        # only update screen if changes have occurred
        self._screen_changed = True

        self._timer_progress = 0
        self._timer_duration = 1000  # milliseconds

        # current velocity of the grid.
        # allows user to flick it around and have it slide
        self._x_vel = 0
        self._y_vel = 0

        # how fast the grid stops sliding
        self._friction = 5

        # since the grid is pixel precise,
        # slow movements can look choppy (one pixel at a time)
        # i played around and found that stopping at a speed of
        # 30 pixels/second is neither choppy or sudden
        self._min_vel = 30

        self._n_scroll_positions = 5
        self._scroll_positions = [
            [0, 0, 0] for i in range(self._n_scroll_positions)
        ]
        self._panning = False

        # the current cell the mouse is on
        # mouse events are only sent per cell
        self._last_cell = (-1, -1)

        # rows and columns have duplicated data
        # when panning a column, instead of checking every cell in that column
        # we iterate over a smaller number of chunks.
        # every cell in a chunk is drawn.
        self._chunk_size = 16
        self._rows = defaultdict(lambda: defaultdict(dict))
        self._columns = defaultdict(lambda: defaultdict(dict))


        # what percentage of a cell should be designated for the grid lines?
        self._grid_percentage = grid_percentage
        # what cell size does grid start to fade away?
        self._grid_fade_start = grid_fade_start
        # what cell size does grid disappear at?
        self._grid_fade_end = grid_fade_end

        self._animated_cells = {}

        self._animation_funcs = [
            [self._fade_animation, self._fade_animation],
            [self._grow_in_animation, self._grow_out_animation]
        ]

        self._generate_window_size()
        self._calc_offsets()
        self._calc_alt_offsets()

        # threading stuff
        self._timer_thread_busy = False
        self._timer_status = TIMER_INACTIVE
        self._timer_ended_in_thread = False
        self._timer_is_threaded = False
        self._main_thread = threading.currentThread()
        self._timer_event = threading.Event()
        self._draw_queue = []
        self._next_draw_queue = []
        self._timer_end_event = pygame.event.Event(pygame.USEREVENT)

        self.draw_cell = self._draw_cell_threadless
        self.erase_cell = self._erase_cell_threadless


        
    #
    # INTERFACE
    # if you were to extend pygrid, these are the methods you'd care about
    #

    def on_start(self):
        # called after grid.start() is called.
        # useful for drawing cells right away
        pass

    def on_timer(self):
        # called every time the timer ticks
        # see start_timer(), stop_timer(), and set_timer()
        pass

    def on_timer_end(self):
        # called when the timer ends
        # useful for multithreading since there is a delay between calling
        # self.stop_timer() and the timer actually processing while the current
        # thread finishes.
        pass

    def on_mouse_down(self, cell_x, cell_y, button):
        # called when mouse is clicked.
        # if a mouse button is reserved for panning or zooming then
        # this method will not be called.
        pass

    def on_mouse_up(self, cell_x, cell_y, button):
        # called when mouse is released.
        # if a mouse button is reserved for panning or zooming then
        # this method will not be called.
        pass

    def on_mouse_motion(self, cell_x, cell_y):
        # called when mouse moves into a new cell
        pass

    def on_key_up(self, key):
        # called when a key is pressed.
        pass

    def on_key_down(self, key):
        # called when a key is released.
        pass

    def clear(self):
        # delete all cells and wipe the screen
        self._draw_queue = []
        self._rows = defaultdict(lambda: defaultdict(dict))
        self._columns = defaultdict(lambda: defaultdict(dict))
        self._animated_cells = {}
        self._draw_screen()

    def get_cell(self, cell_x, cell_y, return_bg=True):
        # get the cell at point cell_x, cell_y
        # if return_bg is True, then the background color will be returned
        # when a cell doesn't exist, rather than None

        default_color = self._background_color if return_bg else None

        row = self._rows.get(cell_y, None)
        if row:
            chunk = row.get(cell_x // self._chunk_size, None)
            if chunk:
                return chunk.get(cell_x, default_color)

        return default_color

    def set_timer(self, duration):
        # duration is in seconds, multiply by 1000 for milliseconds
        self._timer_duration = duration * 1000

    def start_timer(self, multithreaded=False):
        if not self._timer_status == TIMER_INACTIVE:
            return
        self._timer_is_threaded = multithreaded
        self._timer_status = TIMER_ACTIVE
        self._timer_progress = 0
        if multithreaded:
            self.draw_cell = self._draw_cell_threaded
            self.erase_cell = self._erase_cell_threaded

            self._n_ticks = 1
            self._finish_animations()
            self._timer_thread_busy = True
            self._timer_event.clear()
            self._timer_thread = threading.Thread(target=self._timer_thread_func)
            self._timer_thread.start()

    def stop_timer(self):
        if not self._timer_status == TIMER_ACTIVE:
            return

        if self._timer_is_threaded:
            self.draw_cell = self._draw_cell_mixed
            self.erase_cell = self._erase_cell_mixed
            self._timer_event.set()
            self._timer_status = TIMER_ENDING
        else:
            self._timer_status = TIMER_INACTIVE

    def start(self):
        pygame.init()

        self._create_screen()
        self._apply_grid_effects()
        self._create_grid_lines()
        self._calc_n_rows()
        self._calc_n_columns()
        self._calc_render_zone()
        self.on_start()
        self._left_offset = self._grid_thickness // 2
        self._top_offset = self._grid_thickness // 2
        self._draw_screen()

        self._clock = pygame.time.Clock()
        delta = 0

        while True:
            self._handle_events()
            self._handle_mouse_motion()

            if self._x_vel or self._y_vel:
                self._apply_velocity(delta / 1000)

            if self._animated_cells:
                self._animate_cells(delta / 1000)

            if self._draw_queue:
                self._process_draw_queue()

            if self._timer_status == TIMER_ACTIVE:
                self._increment_timer(delta)

            if self._screen_changed:
                self._screen_changed = False
                pygame.display.flip()

            delta = self._clock.tick(self._fps)


    def _draw_screen(self):
        self._draw_rows_cells(0, self._n_rows)
        self._draw_grid()
        self._screen_changed = True

    def _calc_render_zone(self):
        self._render_bound_left = -self._width * 0.2
        self._render_bound_right = self._width * 1.2
        self._render_bound_top = -self._height * 0.2
        self._render_bound_bottom = self._height * 1.2

    def _in_render_zone(self, cell_x, cell_y):
        x = (cell_x - self._pos_x) * self._cell_size
        if self._render_bound_left < x < self._render_bound_right:

            y = (cell_y - self._pos_y) * self._cell_size
            if self._render_bound_top < y < self._render_bound_bottom:
                return True

        return False

    def _increment_timer(self, delta):
        self._timer_progress += delta
        if self._timer_progress >= self._timer_duration:
            if not self._timer_thread_busy and not self._draw_queue:
                self._n_ticks = int(self._timer_progress / self._timer_duration)
                self._timer_progress %= self._timer_duration
                if self._timer_is_threaded:
                    self._timer_thread_busy = True
                    self._timer_event.set()
                    self._timer_event.clear()
                else:
                    self.on_timer(self._n_ticks)

    def _timer_thread_func(self):
        while self._timer_status == TIMER_ACTIVE:
            self.on_timer(self._n_ticks)

            self._draw_queue = self._next_draw_queue
            self._next_draw_queue = []

            self._timer_thread_busy = False
            self._timer_event.wait()

        self.draw_cell = self._draw_cell_threadless
        self.erase_cell = self._erase_cell_threadless
        pygame.event.post(self._timer_end_event)
        self._timer_status = TIMER_INACTIVE

    def _process_draw_queue(self):
        max_tick = pygame.time.get_ticks() + self._frame_delta

        while pygame.time.get_ticks() < max_tick:
            for i in range(min(len(self._draw_queue), 100)):
                cell_x, cell_y, color = self._draw_queue.pop(0)
                self._draw_cell(cell_x, cell_y, color)

            if not self._draw_queue:
                self._screen_changed = True
                break

    def _generate_window_size(self):
        # if screen width and height is already set, use those
        if self._width and self._height:
            return

        # if a number of rows and columns are used, calculate window size to fit
        elif self._n_rows and self._n_columns:
            self._width = self._n_columns * self._cell_size - \
                int(self._grid_percentage * self._cell_size)
            self._height = self._n_rows * self._cell_size - \
                int(self._grid_percentage * self._cell_size)

        # otherwise, use 800x600
        else:
            self._width = 800
            self._height = 600

    def _create_screen(self):
        if self._allowed_resize:
            self._screen = pygame.display.set_mode(
                (self._width, self._height), pygame.RESIZABLE
            )
        else:
            self._screen = pygame.display.set_mode((self._width, self._height))

    def _draw_cell(self, cell_x, cell_y, color, draw_grid=True):
        x = (cell_x - math.floor(self._pos_x)) * \
            self._cell_size - self._left_offset
        y = (cell_y - math.floor(self._pos_y)) * \
            self._cell_size - self._top_offset

        pygame.draw.rect(
            self._screen,
            color,
            (x, y, self._cell_size, self._cell_size)
        )

        if draw_grid and self._grid_thickness:
            self._screen.blit(self._cell_borders, (x, y))

    def _add_cell(self, cell_x, cell_y, color):
        chunk_x, chunk_y = self._get_chunk(cell_x, cell_y)
        self._columns[cell_x][chunk_y][cell_y] = color
        self._rows[cell_y][chunk_x][cell_x] = color

    def _end_animation(self, cell_x, cell_y):
        try:
            del self._animated_cells[(cell_x, cell_y)]
        except KeyError:
            pass

    def _start_animation(self, cell_x, cell_y, target_color, duration, animation_type=0, erase_on_complete=False):
        current_animation = self._animated_cells.get((cell_x, cell_y), None)
        if current_animation:
            if current_animation[ORIGINAL_COLOR] == target_color:
                current_animation[ORIGINAL_COLOR], current_animation[TARGET_COLOR] = \
                    current_animation[TARGET_COLOR], target_color
                perc = max(0, 1 - current_animation[PROGRESS] / current_animation[DURATION])
                current_animation[PROGRESS] = duration * perc
                current_animation[DURATION] = duration
                current_animation[DELETING] = erase_on_complete
                return
            elif current_animation[TARGET_COLOR] == target_color:
                return

            else:
                original_color = current_animation[CURRENT_COLOR]

                self._animated_cells[(cell_x, cell_y)] = [
                    original_color, original_color, target_color,
                    animation_type, 0, duration, erase_on_complete
                ]
                return

        original_color = self.get_cell(cell_x, cell_y)
        if original_color != target_color:
            self._animated_cells[(cell_x, cell_y)] = [
                    original_color, original_color, target_color,
                    animation_type, 0, duration, erase_on_complete
                ]

    def _draw_cell_mixed(self, cell_x, cell_y, color, animate=False):
        if threading.current_thread() is self._main_thread:
            self._draw_cell_threadless(cell_x, cell_y, color, animate)
        else:
            self._draw_cell_threaded(cell_x, cell_y, color)

    def _draw_cell_threadless(self, cell_x, cell_y, color, animation=None):
        if animation:
            self._start_animation(cell_x, cell_y, color, *animation)
        else:
            self._end_animation(cell_x, cell_y)
            self._screen_changed = True
            self._add_cell(cell_x, cell_y, color)
            self._draw_cell(cell_x, cell_y, color)

    def _draw_cell_threaded(self, cell_x, cell_y, color):
        self._add_cell(cell_x, cell_y, color)
        if self._in_render_zone(cell_x, cell_y):
            self._next_draw_queue.append((cell_x, cell_y, color))

    def _erase_cell_mixed(self, cell_x, cell_y, animation=None):
        if threading.current_thread() is self._main_thread:
            self._erase_cell_threadless(cell_x, cell_y, animation)
        else:
            self._erase_cell_threaded(cell_x, cell_y)

    def _erase_cell_threadless(self, cell_x, cell_y, animation=None):
        if animation:
            self._start_animation(
                cell_x, cell_y,
                self._background_color,
                erase_on_complete=True,
                *animation
            )
        else:
            self._end_animation(cell_x, cell_y)
            self._screen_changed = True
            self._delete_cell(cell_x, cell_y)
            self._draw_cell(cell_x, cell_y, self._background_color)

    def _erase_cell_threaded(self, cell_x, cell_y):
        self._delete_cell(cell_x, cell_y)
        if self._in_render_zone(cell_x, cell_y):
            self._next_draw_queue.append((cell_x, cell_y, self._background_color))

    def _delete_cell(self, cell_x, cell_y):
        chunk_x, chunk_y = self._get_chunk(cell_x, cell_y)
        try:
            del self._columns[cell_x][chunk_y][cell_y]
            del self._rows[cell_y][chunk_x][cell_x]
        except KeyError:
            pass

    def _clear_region(self, x, y, w, h):
        pygame.draw.rect(
            self._screen,
            self._background_color,
            (x, y, w, h)
        )

    def _chunk_range(self, a, b):
        chunk_start = math.floor(a) // self._chunk_size
        chunk_end = math.ceil(
            (math.floor(a) + b / self._cell_size) / self._chunk_size
        ) + 1
        return chunk_start, chunk_end

    def _draw_rows_cells(self, row_start, row_span):
        self._clear_region(
            0,
            row_start * self._cell_size - self._top_offset,
            self._width,
            row_span * self._cell_size
        )

        chunk_start, chunk_end = self._chunk_range(self._pos_x, self._width)

        self.cell_y = math.floor(self._pos_y)
        for row_n in range(self.cell_y + row_start,
                           self.cell_y + row_start + row_span):
            row = self._rows.get(row_n, None)
            if not row:
                continue

            for chunk_n in range(chunk_start, chunk_end):
                chunk = row.get(chunk_n, None)
                if not chunk:
                    continue

                for column_n, cell in chunk.items():
                    self._draw_cell(
                        column_n, row_n,
                        cell,
                        draw_grid=False
                    )

    def _draw_columns_cells(self, column_start, column_span):
        self._clear_region(
            column_start * self._cell_size - self._left_offset,
            0,
            column_span * self._cell_size,
            self._height
        )

        chunk_start, chunk_end = self._chunk_range(self._pos_y, self._height)

        self.cell_x = math.floor(self._pos_x)
        for column_n in range(self.cell_x + column_start,
                              self.cell_x + column_start + column_span):
            column = self._columns.get(column_n, None)
            if not column:
                continue

            for chunk_n in range(chunk_start, chunk_end):
                chunk = column.get(chunk_n, None)
                if not chunk:
                    continue

                for row_n, cell in chunk.items():
                    self._draw_cell(
                        column_n, row_n,
                        cell, draw_grid=False
                    )

    def _draw_grid(self):
        if not self._grid_thickness:
            return

        x = -self._left_offset - self._grid_thickness + self._grid_thickness // 2
        y = -self._top_offset - self._grid_thickness + self._grid_thickness // 2

        # draw grid rows
        for row in range(self._n_rows + 1):
            self._screen.blit(self._grid_row, (-self._left_offset, y))
            y += self._cell_size

        # draw grid columns
        for column in range(self._n_columns + 1):
            self._screen.blit(self._grid_column, (x, 0))
            x += self._cell_size

    def _on_exit(self):
        if self._timer_status == TIMER_ACTIVE:
            self._timer_status = TIMER_INACTIVE
            self._timer_event.set()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._on_exit()

            elif event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # not sure why, but windows gives a different keycode
                # for mousewheel events depending on the scroll speed.
                if event.button > 5:
                    b = MOUSE_SCROLL_UP + event.button % 2
                    self._on_mouse_down(*event.pos, b)
                else:
                    self._on_mouse_down(*event.pos, event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(*event.pos, event.button)

            elif event.type == pygame.MOUSEMOTION:
                self._on_mouse_motion(*event.pos)

            elif event.type == pygame.KEYDOWN:
                self.on_key_down(event.key)

            elif event.type == pygame.KEYUP:
                self.on_key_up(event.key)

            # self._thread_end_event
            elif event.type == pygame.USEREVENT:
                self.on_timer_end()

            elif event.type == pygame.VIDEOEXPOSE:
                self._screen_changed = True


    def _calc_alt_offsets(self):
        self._right_offset = self._cell_size - \
            (self._width + self._left_offset) % self._cell_size
        self._bottom_offset = self._cell_size - \
            (self._height + self._top_offset) % self._cell_size

    def _calc_offsets(self):
        self._left_offset = math.floor((self._pos_x % 1) * self._cell_size)
        self._top_offset = math.floor((self._pos_y % 1) * self._cell_size)

    def _on_resize(self, w, h):
        self._width = w
        self._height = h

        # calculating left/top offset is not needed since pygame seems expand from bottom right
        # recalculating anyway, incase this is different per window manager/operating system
        self._calc_offsets()
        self._calc_alt_offsets()
        self._calc_n_columns()
        self._calc_n_rows()

        self._apply_grid_effects()
        self._create_grid_lines()
        self._calc_render_zone()
        self._draw_screen()

    def _on_mouse_down(self, x, y, button):
        if button == self._pan_button and self._allowed_pan:
            t = pygame.time.get_ticks()
            self._scroll_positions = [
                [x, y, t] for i in range(self._n_scroll_positions)
            ]
            self._mouse_x_direction = 0
            self._mouse_y_direction = 0
            self._x_vel = 0
            self._y_vel = 0
            self._panning = True

        elif button == MOUSE_SCROLL_UP and self._allowed_zoom:
            self._zoom(x, y, 1.1)

        elif button == MOUSE_SCROLL_DOWN and self._allowed_zoom:
            self._zoom(x, y, 0.9)

        else:
            self.on_mouse_down(*self._get_cell_at_point(x, y), button)

    def _on_mouse_up(self, x, y, button):
        if button == self._pan_button and self._allowed_pan:
            self._panning = False
            if self._mouse_moved:
                self._calculate_trajectory()
        else:
            self.on_mouse_up(*self._get_cell_at_point(x, y), button)

    def _on_mouse_motion(self, x, y):
        # rather than triggering a mouse motion event every time the mouse moves
        # send a mouse motion event of the latest mouse position per frame
        # this is to stop high dpi mouses sending tons of events
        # during a single frame, slowing the program
        self._mouse_position = (x, y)
        self._mouse_moved = True

    def _get_cell_at_point(self, x, y):
        return (
            math.floor(self._pos_x) + (x + self._left_offset) // self._cell_size,
            math.floor(self._pos_y) + (y + self._top_offset) // self._cell_size,
        )

    def _get_pos_at_point(self, x, y):
        return (
            self._pos_x + x / self._cell_size,
            self._pos_y + y / self._cell_size,
        )

    def _get_chunk(self, cell_x, cell_y):
        return cell_x // self._chunk_size, cell_y // self._chunk_size

    def _pan(self, x, y):
        # this method is complicated...
        # python is a pretty slow language, but the grid needs to be performant
        # so, instead of redrawing the entire screen every time it moves, we
        # just translate the pixels on the screen, and then redraw any cells and
        # grid lines introduced in this new area.

        # translating the pixels is very efficient since pygame is responsible for it
        # however, we want to translate both x and y at the same time rather than
        # panning x, drawing cells, then panning y

        # this means we first have to calculate the new positions and offsets for x and y
        # then we can draw the new cells for the introduced rows/columns
        # then only after all the cells are drawn, can we finally draw the grid lines between them
        # the grid lines have to be drawn after both rows and columns are drawn since drawing a column
        # would erase some row grid lines and vice versa


        # calculate how many pixels the grid has panned
        # this could be zero if the grid panned -1 > n > 1
        old_pos_y = self._pos_y
        self._pos_y += y / self._cell_size
        y_pan = math.floor(self._pos_y * self._cell_size) - \
            math.floor(old_pos_y * self._cell_size)

        old_pos_x = self._pos_x
        self._pos_x += x / self._cell_size
        x_pan = math.floor(self._pos_x * self._cell_size) - \
            math.floor(old_pos_x * self._cell_size)

        # if the pan is smaller than a pixel, no screen drawing will occur, return
        if not x_pan and not y_pan:
            return

        # translate/pan the screen the given amount
        # this will leave a portion of the screen needing to be drawn
        self._screen.scroll(-x_pan, -y_pan)

        # initialize variables
        # column/row start represents the nth visible column from the left/top of the screen
        # column/row span represents how many columns/rows from the initial one.
        # these will the the columns/rows that are drawn
        column_start = 0
        column_span = 0
        row_start = 0
        row_span = 0

        # calculate column start and column span if panning right
        if x_pan > 0:
            traversed_columns, self._left_offset = divmod(
                self._left_offset + x_pan, self._cell_size
            )
            self._n_columns -= traversed_columns
            column_span, self._right_offset = divmod(
                self._right_offset - x_pan, self._cell_size
            )
            self._n_columns -= column_span
            column_span = abs(column_span) + 1
            column_start = self._n_columns - column_span

        # calculate column start and column span if panning left
        elif x_pan < 0:
            traversed_columns, self._right_offset = divmod(
                self._right_offset - x_pan, self._cell_size
            )
            self._n_columns -= traversed_columns
            column_span, self._left_offset = divmod(
                self._left_offset + x_pan, self._cell_size
            )
            self._n_columns -= column_span
            column_span = abs(column_span) + 1

        # calculate row start and row span if panning down
        if y_pan > 0:
            traversed_rows, self._top_offset = divmod(
                self._top_offset + y_pan, self._cell_size
            )
            self._n_rows -= traversed_rows
            row_span, self._bottom_offset = divmod(
                self._bottom_offset - y_pan, self._cell_size
            )
            self._n_rows -= row_span
            row_span = abs(row_span) + 1
            row_start = self._n_rows - row_span

        # calculate row start and row span if panning up
        elif y_pan < 0:
            traversed_rows, self._bottom_offset = divmod(
                self._bottom_offset - y_pan, self._cell_size
            )
            self._n_rows -= traversed_rows
            row_span, self._top_offset = divmod(
                self._top_offset + y_pan, self._cell_size
            )
            self._n_rows -= row_span
            row_span = abs(row_span) + 1

        # now that the rows/columns needing to be drawn are found, draw them
        # the reason cells aren't drawn in the logic above is because drawing
        #     a column requires the updated row information and vice versa
        if x_pan:
            self._draw_columns_cells(column_start, column_span)
        if y_pan:
            self._draw_rows_cells(row_start, row_span)

        # time to draw the grid
        # the reason the grid isn't drawn along with the rows/columns is that
        # the rows and columns overlap in the corner. this means sometimes
        # cells in the corner would be missing a vertical or horizontal grid line
        if self._grid_thickness:
            if x_pan:
                # when panning left/right, we do not need to draw the entire
                # horizontal grid. we only need to draw a section of the horizontal
                # grid that covers the columns introducted since the existing
                # columns already have theirs
                self._draw_partial_rows_grids(
                    row_start, row_span,
                    column_start, column_span
                )
            else:
                # however, if there is no panning left/right, we can just draw the entire
                # horizontal grids rows for the introducted rows
                self._draw_rows_grids(row_start, row_span)

            if y_pan:
                # the same applies for vertical grids introduced rows.
                self._draw_partial_columns_grids(
                    column_start, column_span,
                    row_start, row_span
                )
            else:
                self._draw_columns_grids(column_start, column_span)

        # even though the mouse hasn't moved, its position on the grid has changed
        # this is justification for a mouse event
        self._mouse_moved = True
        self._screen_changed = True

    def _draw_columns_grids(self, column_start, column_span):
        x = -self._left_offset + column_start * self._cell_size
        for column in range(column_start, column_start + column_span):
            self._screen.blit(
                self._grid_column_left,
                (x, -self._top_offset)
            )
            self._screen.blit(
                self._grid_column_right,
                (x + self._grid_offset, -self._top_offset)
            )
            x += self._cell_size

    def _draw_rows_grids(self, row_start, row_span):
        y = -self._top_offset + row_start * self._cell_size
        for row in range(row_start, row_start + row_span):
            self._screen.blit(
                self._grid_row_top,
                (-self._left_offset, y)
            )
            self._screen.blit(
                self._grid_row_bottom,
                (-self._left_offset, y + self._grid_offset)
            )
            y += self._cell_size

    def _draw_partial_columns_grids(self, column_start, column_span,
                                   row_start, row_span):
        if row_start == 0:
            grid_offset = -self._column_grid_length + row_span \
                * self._cell_size - self._top_offset
        else:
            grid_offset = self._height - (row_span - 1) * self._cell_size \
                - (self._cell_size - self._bottom_offset)


        x = -self._left_offset

        for column in range(self._n_columns):
            if column_start <= column < column_start + column_span:
                self._screen.blit(
                    self._grid_column_left,
                    (x, -self._top_offset)
                )
                self._screen.blit(
                    self._grid_column_right,
                    (x + self._grid_offset, -self._top_offset)
                )
            else:
                self._screen.blit(
                    self._grid_column_left,
                    (x, grid_offset)
                )
                self._screen.blit(
                    self._grid_column_right,
                    (x + self._grid_offset, grid_offset)
                )

            x += self._cell_size

    def _draw_partial_rows_grids(self, row_start, row_span,
                                column_start, column_span):
        # prob
        if column_start == 0:
            grid_offset = -self._row_grid_length + column_span \
                * self._cell_size - self._left_offset
        else:
            grid_offset = self._width - (column_span - 1) * self._cell_size \
                - (self._cell_size - self._right_offset)


        y = -self._top_offset

        for row in range(self._n_rows):
            if row_start <= row < row_start + row_span:
                self._screen.blit(
                    self._grid_row_top,
                    (-self._left_offset, y)
                )
                self._screen.blit(
                    self._grid_row_bottom,
                    (-self._left_offset, y + self._cell_size - (self._grid_thickness - self._grid_thickness // 2))
                )
            else:
                self._screen.blit(
                    self._grid_row_top,
                    (grid_offset, y)
                )
                self._screen.blit(
                    self._grid_row_bottom,
                    (grid_offset, y + self._cell_size - (self._grid_thickness - self._grid_thickness // 2))
                )

            y += self._cell_size


    def _zoom(self, x, y, amount):
        pos_x, pos_y = self._get_pos_at_point(x, y)

        if amount > 1:
            if self._cell_size == self._max_cell_size:
                return
            self._cell_size = math.ceil(self._cell_size * amount)
            if self._cell_size > self._max_cell_size:
                self._cell_size = self._max_cell_size
        else:
            if self._cell_size == self._min_cell_size:
                return
            self._cell_size = math.floor(self._cell_size * amount)
            if self._cell_size < self._min_cell_size:
                self._cell_size = self._min_cell_size

        new_pos_x, new_pos_y = self._get_pos_at_point(x, y)

        self._pos_x += pos_x - new_pos_x
        self._pos_y += pos_y - new_pos_y

        self._calc_offsets()
        self._calc_alt_offsets()
        self._calc_n_rows()
        self._calc_n_columns()

        self._apply_grid_effects()
        self._create_grid_lines()
        self._draw_screen()

    def _calculate_trajectory(self):
        self._handle_mouse_motion()

        x, y, t = zip(*self._scroll_positions)

        dt = t[-1] - t[0]

        # avoid division by zero
        if not dt:
            return

        dt = 1000 / dt
        dx = x[0] - x[-1]
        dy = y[0] - y[-1]

        self._x_vel = dx * dt
        self._y_vel = dy * dt

    def _apply_velocity(self, delta):
        pan_x = self._x_vel * delta
        vel_lost = self._friction * pan_x
        self._x_vel -= math.copysign(vel_lost, self._x_vel)

        pan_y = self._y_vel * delta
        vel_lost = self._friction * pan_y
        self._y_vel -= math.copysign(vel_lost, self._y_vel)

        # both values stop at the same time to avoid sliding on only 1 axis
        if abs(self._x_vel) < self._min_vel \
                and abs(self._y_vel) < self._min_vel:
            self._x_vel = 0
            self._y_vel = 0

        self._pan(pan_x, pan_y)

    def _finish_animations(self):
        for (cell_x, cell_y), (_, _, target_color, _, _, _, deleting) in self._animated_cells.items():
            self._draw_cell(cell_x, cell_y, target_color)
            if deleting:
                self._delete_cell(cell_x, cell_y)
            else:
                self._add_cell(cell_x, cell_y, target_color)
        self._animated_cells = {}
        self._screen_changed = True

    def _grow_out_animation(self, cell_x, cell_y, original_color, color, perc):
        x = (cell_x - math.floor(self._pos_x)) * \
            self._cell_size - self._left_offset
        y = (cell_y - math.floor(self._pos_y)) * \
            self._cell_size - self._top_offset

        size = int(self._cell_size * (1 - perc))
        offset = (self._cell_size - size) // 2 

        pygame.draw.rect(
            self._screen,
            color,
            (x, y, self._cell_size, self._cell_size)
        )
        pygame.draw.rect(
            self._screen,
            original_color,
            (x + offset, y + offset, size, size)
        )

        self._screen.blit(self._cell_borders, (x, y))
        return color

    def _grow_in_animation(self, cell_x, cell_y, original_color, color, perc):
        x = (cell_x - math.floor(self._pos_x)) * \
            self._cell_size - self._left_offset
        y = (cell_y - math.floor(self._pos_y)) * \
            self._cell_size - self._top_offset

        pygame.draw.rect(
            self._screen,
            original_color,
            (x, y, self._cell_size, self._cell_size)
        )

        size = int(self._cell_size * perc)
        offset = (self._cell_size - size) // 2 
        pygame.draw.rect(
            self._screen,
            color,
            (x + offset, y + offset, size, size)
        )

        self._screen.blit(self._cell_borders, (x, y))
        return color

    def _fade_animation(self, cell_x, cell_y, original_color, color, perc):
        color = color_mix(original_color, color, perc)
        self._draw_cell(cell_x, cell_y, color)
        return color

    def _animate_cells(self, delta):
        for (cell_x, cell_y), anim in tuple(self._animated_cells.items()):
            perc = anim[PROGRESS] / anim[DURATION]

            if perc < 1:
                anim_type = anim[ANIMATION_TYPE]

                color = self._animation_funcs[anim[ANIMATION_TYPE]][anim[DELETING]](
                    cell_x, cell_y,
                    anim[ORIGINAL_COLOR],
                    anim[TARGET_COLOR],
                    perc
                )
                anim[PROGRESS] = anim[PROGRESS] + delta
                anim[CURRENT_COLOR] = color

            else:
                del self._animated_cells[(cell_x, cell_y)]
                self._draw_cell(cell_x, cell_y, anim[TARGET_COLOR])
                if anim[DELETING]:
                    self._delete_cell(cell_x, cell_y)
                else:
                    self._add_cell(cell_x, cell_y, anim[TARGET_COLOR])

        self._screen_changed = True

    def _calc_n_rows(self):
        # first, find out how many cells fit perfectly in the height
        # do this by removing the padding from top and bottom
        top_padding = (self._cell_size - self._top_offset) % self._cell_size
        bottom_padding = (self._cell_size - self._bottom_offset) % self._cell_size
        height_no_padding = self._height - top_padding - bottom_padding

        # divide by cell size to get the exact number
        self._n_rows = height_no_padding // self._cell_size

        # add on another row for cell(s) contained in top/bottom padding
        if self._top_offset:
            self._n_rows += 1

        if self._bottom_offset:
            self._n_rows += 1

    def _calc_n_columns(self):
        left_padding = (self._cell_size - self._left_offset) % self._cell_size
        right_padding = (self._cell_size - self._right_offset) % self._cell_size
        width_no_padding = self._width - left_padding - right_padding

        self._n_columns = width_no_padding // self._cell_size

        if self._left_offset:
            self._n_columns += 1

        if self._right_offset:
            self._n_columns += 1

    def _handle_mouse_motion(self):
        if not self._mouse_moved:
            return

        x, y = self._mouse_position

        dx, dy = pygame.mouse.get_rel()

        self._mouse_moved = False

        if self._panning:
            t = pygame.time.get_ticks()

            x_direction = math.copysign(1, dx)
            y_direction = math.copysign(1, dy)

            if x_direction and x_direction != self._mouse_x_direction:
                if self._mouse_x_direction:
                    for i in range(len(self._scroll_positions)):
                        self._scroll_positions[i][0] = x
                self._mouse_x_direction = x_direction

            if y_direction and y_direction != self._mouse_y_direction:
                if self._mouse_y_direction:
                    for i in range(len(self._scroll_positions)):
                        self._scroll_positions[i][1] = y
                self._mouse_y_direction = y_direction

            del self._scroll_positions[0]
            self._scroll_positions.append([x, y, t])
            self._pan(-dx, -dy)
            self._x_vel = 0
            self._y_vel = 0
        else:
            cell = self._get_cell_at_point(x, y)
            if cell != self._last_cell:
                self._last_cell = cell
                self.on_mouse_motion(*cell)

    def _apply_grid_effects(self):
        if not self._grid_percentage or self._cell_size <= self._grid_fade_end:
            self._grid_thickness = 0

        elif self._cell_size <= self._grid_fade_start:
            self._grid_thickness = int(self._cell_size * self._grid_percentage)

            progress = (self._cell_size - self._grid_fade_start) / (
                self._grid_fade_end - self._grid_fade_start
            )
            smooth_amount = 1 + (
                1 - (self._grid_thickness / self._cell_size / self._grid_percentage)
            )
            self._grid_alpha = (self._grid_default_alpha - progress * self._grid_default_alpha) * smooth_amount 

        else:
            self._grid_thickness = int(self._cell_size * self._grid_percentage)
            self._grid_alpha = self._grid_default_alpha

    def _create_grid_lines(self):
        n_rows = self._height // self._cell_size + 2
        n_columns = self._width // self._cell_size + 2

        self._column_grid_length = n_rows * self._cell_size
        self._row_grid_length = n_columns * self._cell_size

        self._grid_offset = self._cell_size - \
            (self._grid_thickness - self._grid_thickness // 2)

        # column grid lines
        self._grid_column = pygame.Surface(
            (self._grid_thickness, self._column_grid_length)
        )
        self._grid_column_left = pygame.Surface(
            (self._grid_thickness // 2, self._column_grid_length)
        )
        self._grid_column_right = pygame.Surface(
            (self._grid_thickness - self._grid_thickness // 2, self._column_grid_length)
        )

        # row grid lines
        self._grid_row_top = pygame.Surface(
            (self._row_grid_length, self._grid_thickness // 2)
        )
        self._grid_row_bottom = pygame.Surface(
            (self._row_grid_length, self._grid_thickness - self._grid_thickness // 2)
        )
        self._grid_row = pygame.Surface(
            (self._row_grid_length, self._grid_thickness)
        )

        # cell borders
        self._cell_borders = pygame.Surface((self._cell_size, self._cell_size))

        surfaces = (
            self._grid_row,
            self._grid_row_top,
            self._grid_row_bottom,
            self._grid_column,
            self._grid_column_left,
            self._grid_column_right,
            self._cell_borders
        )

        for surface in surfaces:
            surface.fill(self._grid_color)
            surface.set_colorkey(self._color_key)
            surface.set_alpha(self._grid_alpha)

        # cell borders
        pygame.draw.rect(
            self._cell_borders,
            self._color_key,
            (
                self._grid_thickness // 2,
                self._grid_thickness // 2,
                self._cell_size - self._grid_thickness,
                self._cell_size - self._grid_thickness
            )
        )

        # after every column, a dot is drawn in the color key
        # this dot will be transparent when the grid line is blitted
        # this avoids rows and columns grid lines overlapping
        # TODO more efficient
        for column in range(n_columns):
            rect = (
                column * self._cell_size - self._grid_thickness + self._grid_thickness // 2,
                0, self._grid_thickness, self._grid_thickness
            )
            pygame.draw.rect(
                self._grid_row_top,
                self._color_key, rect
            )
            pygame.draw.rect(
                self._grid_row_bottom,
                self._color_key, rect
            )
            pygame.draw.rect(
                self._grid_row,
                self._color_key, rect
            )

if __name__ == "__main__":
    test_grid = PyGrid()
    test_grid.start()
