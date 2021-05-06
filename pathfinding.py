from draw_grid import DrawGrid
from threading import Thread
from keycodes import *


# algorithms
BREADTH_FIRST = 0
BEST_FIRST = 1
A_STAR = 2

# solving states
NOT_SOLVING = 0
SOLVING_ACTIVE = 1
SOLVING_PAUSED = 2
SOLVING_FINISHED = 3


class PathfindingGrid(DrawGrid):
    def __init__(
            self, background_color, grid_color, cell_color, trace_color,
            start_color, end_color, scan_color, scanned_color, grid_thickness,
            fps, default_algorithm=A_STAR):

        DrawGrid.__init__(
            self,
            n_columns=40,
            n_rows=40,
            cell_size=20,
            background_color=background_color,
            grid_color=grid_color,
            grid_thickness=grid_thickness,
            fps=fps
        )

        # rather than a high speed just having a low delay,
        # it can have a fairly low delay but combined with multiple iterations
        self.speed_index = 3
        self.iteration_delays     = [0.1, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]
        self.iterations_per_ticks = [  1,    1,    1,    2,    4,    8,   16,   32,   64,  128]
        self.set_timer(self.iteration_delays[self.speed_index])

        self.start_cell = None
        self.end_cell = None
        self.solving_state = NOT_SOLVING
        self.cell_color = cell_color
        self.queue = []
        self.explored_cells = {}
        self.thread = None

        self.algorithm = default_algorithm

        self.start_color = start_color
        self.end_color = end_color
        self.trace_color = trace_color
        self.scan_color = scan_color
        self.scanned_color = scanned_color

    @property
    def iteration_delay(self):
        return self.iteration_delays[self.speed_index]

    @property
    def iterations_per_tick(self):
        return self.iterations_per_ticks[self.speed_index]

    def is_special_cell(self, cell_x, cell_y):
        if (cell_x, cell_y) == self.start_cell:
            return True
        if (cell_x, cell_y) == self.end_cell:
            return True
        return False

    def on_mouse_event(self, cell_x, cell_y, button, pressed):
        if self.solving_state == SOLVING_ACTIVE:
            return

        if self.solving_state == SOLVING_PAUSED or \
                self.solving_state == SOLVING_FINISHED:
            self.solving_state = NOT_SOLVING
            self.clear_solve()

        if button == LEFT_MOUSE:
            self.on_left_mouse(cell_x, cell_y, pressed)

        elif button == RIGHT_MOUSE:
            self.on_right_mouse(cell_x, cell_y)

    def on_left_mouse(self, cell_x, cell_y, pressed):
        if self.is_special_cell(cell_x, cell_y):
            return

        if not pressed:
            if self.get_cell(cell_x, cell_y, return_bg=False):
                self.draw_delete_mode = True
            else:
                self.draw_delete_mode = False

        if self.draw_delete_mode:
            self.erase_cell(cell_x, cell_y, animate=True)
        else:
            self.draw_cell(cell_x, cell_y, self.cell_color, animate=True)

    def on_right_mouse(self, cell_x, cell_y):
        if not self.start_cell:
            self.start_cell = (cell_x, cell_y)
            self.draw_cell(cell_x, cell_y, self.start_color, animate=True)
        elif not self.end_cell:
            if self.start_cell == (cell_x, cell_y):
                self.erase_cell(cell_x, cell_y, animate=True)
                self.start_cell = None
            else:
                self.end_cell = (cell_x, cell_y)
                self.draw_cell(cell_x, cell_y, self.end_color, animate=True)
        else:
            self.erase_cell(*self.start_cell, animate=True)
            self.erase_cell(*self.end_cell, animate=True)
            self.start_cell = None
            self.end_cell = None

    def on_key_down(self, key):
        if key == KEY_SPACE:  # space
            if self.solving_state == SOLVING_PAUSED:
                self.solving_state = SOLVING_ACTIVE
                self.start_timer()
            elif self.solving_state == SOLVING_ACTIVE:
                if self.thread:
                    self.thread.join()
                self.stop_timer()
                self.solving_state = SOLVING_PAUSED
            else:
                self.solve()

        elif key == KEY_ESCAPE:  # escape
            if self.solving_state != NOT_SOLVING:
                self.solving_state = NOT_SOLVING
                self.clear_solve()

        elif key == KEY_DELETE:
            self.reset()

        elif KEY_A <= key <= KEY_C:
            if self.solving_state == SOLVING_ACTIVE:
                return

            if self.solving_state != NOT_SOLVING:
                self.clear_solve()
                self.solving_state = NOT_SOLVING

            if key == KEY_A:
                self.algorithm = BREADTH_FIRST
            elif key == KEY_B:
                self.algorithm = BEST_FIRST
            else:
                self.algorithm = A_STAR

        elif KEY_1 <= key <= KEY_9:
            self.speed_index = key - KEY_1
            self.set_timer(self.iteration_delay)

    def clear_solve(self):
        if self.thread:
            self.thread.join()
        self.stop_timer(process_thread_queue=False)
        del self.explored_cells[self.start_cell]
        for cell in self.explored_cells:
            self.erase_cell(*cell)
        self.queue = []
        self.explored_cells = {}

    def reset(self):
        if self.thread:
            self.thread.join()
        self.stop_timer(process_thread_queue=False)
        self.start_cell = None
        self.end_cell = None
        self.queue = []
        self.explored_cells = {}
        self.solving_state = NOT_SOLVING
        self.clear()

    def solve(self):
        if self.solving_state == SOLVING_ACTIVE or self.solving_state == SOLVING_PAUSED:
            return

        if not self.start_cell or not self.end_cell:
            return

        if self.solving_state == SOLVING_FINISHED:
            self.clear_solve()
        self.found_end_cell = False
        self.trace_cell = self.end_cell
        self.solving_state = SOLVING_ACTIVE
        self.start_timer()
        self.queue = [(self.start_cell, 0)]
        self.explored_cells = {self.start_cell: 1}

    def on_timer(self, n_ticks):
        self.thread = Thread(target=self.thread_func)
        self.thread.start()

    def thread_func(self):
        for i in range(self.iterations_per_tick):
            self.do_iteration()
        self.timer_tick()

    def do_iteration(self):
        if self.found_end_cell:
            self.backtrack()
        else:
            self.expand_search()

    def get_heuristic(self, cell):
        # y distance plus x distance
        return abs(cell[0] - self.end_cell[0]) + abs(cell[1] - self.end_cell[1])

    def evaluate_path(self, cell):
        if cell not in self.explored_cells:
            return False

        counter = self.explored_cells[cell]

        # found target cell, return true
        if counter == 1:
            self.stop_timer()
            self.solving_state = SOLVING_FINISHED
            return True

        # path is shorter than current chosen path
        if not self.smallest_counter or counter < self.smallest_counter:
            self.smallest_counter = counter
            self.chosen_cell = cell

        return False

    def backtrack(self):
        cell_x, cell_y = self.trace_cell
        self.smallest_counter = None
        self.chosen_cell = None

        # if any of the paths found the end node, we are done
        if self.evaluate_path((cell_x + 1, cell_y)) \
                or self.evaluate_path((cell_x - 1, cell_y)) \
                or self.evaluate_path((cell_x, cell_y + 1)) \
                or self.evaluate_path((cell_x, cell_y - 1)):
            self.stop_timer()
            self.solving_state = SOLVING_FINISHED
        else:
            self.thread_draw_cell(*self.chosen_cell, self.trace_color)
            self.trace_cell = self.chosen_cell

    def search_neighbour(self, cell):
        # cell has already been explored, return
        if cell in self.explored_cells:
            return

        # cell is found
        if cell == self.end_cell:
            self.found_end_cell = True
            return

        if not self.get_cell(*cell, return_bg=False):
            if self.algorithm == BREADTH_FIRST:
                # breadth-first does not use a heuristic,
                # it does first-come-first-serve
                # so we can just append the cell to the end of the queue
                self.queue.append((cell, 0))
            else:
                # both A* and best-first use a heuristic
                heuristic = self.get_heuristic(cell)

                if self.algorithm == A_STAR:
                    # difference between the two is that A*'s heuristic
                    # adds the path length to it
                    heuristic += self.counter

                # find where in the queue the cell belongs based on heuristic
                for i, (_, compared_heuristic) in enumerate(self.queue):
                    if compared_heuristic >= heuristic:
                        self.queue.insert(i, (cell, heuristic))
                        break
                else:
                    # otherwise, if the queue is empty, plop it on the end
                    self.queue.append((cell, heuristic))

            # save the path length so we can use it for backtracking later
            self.explored_cells[cell] = self.counter
            self.thread_draw_cell(*cell, self.scan_color)

    def expand_search(self):
        if not self.queue:
            self.solving_state = SOLVING_FINISHED
            self.stop_timer()
            return

        (cell_x, cell_y), heuristic = self.queue.pop(0)

        if (cell_x, cell_y) != self.start_cell:
            self.thread_draw_cell(cell_x, cell_y, self.scanned_color)

        self.counter = self.explored_cells[(cell_x, cell_y)] + 1

        self.search_neighbour((cell_x + 1, cell_y))
        self.search_neighbour((cell_x - 1, cell_y))
        self.search_neighbour((cell_x, cell_y + 1))
        self.search_neighbour((cell_x, cell_y - 1))


if __name__ == "__main__":
    from config import config
    from utils import color_mix

    light_yellow = color_mix(
        config["background_color"],
        config["yellow"],
        0.2
    )
    orange = color_mix(
        config["yellow"],
        config["red"],
        0.4
    )

    light_orange = color_mix(
        config["background_color"],
        orange,
        0.5
    ),

    grid = PathfindingGrid(
        background_color = config["background_color"],
        cell_color       = config["cell_color"],
        grid_color       = config["grid_color"],
        trace_color      = config["red"],
        start_color      = config["blue"],
        end_color        = config["green"],
        scanned_color    = light_yellow,
        scan_color       = light_orange,
        grid_thickness   = config["grid_thickness"],
        fps              = config["fps"]
    )
        
    grid.start()
