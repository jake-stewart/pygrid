from draw_grid import DrawGrid
from keycodes import *

class PathfindingGrid(DrawGrid):

    def __init__(
            self, background_color, grid_color, cell_color, trace_color,
            start_color, end_color, scan_color, scanned_color, grid_percentage,
            fps):

        DrawGrid.__init__(
            self,
            n_columns=40,
            n_rows=40,
            cell_size=20,
            background_color=background_color,
            grid_color=grid_color,
            grid_percentage=grid_percentage,
            fps=fps
        )

        self.animation = (0.1, 1)
        # rather than a high speed just having a low delay,
        # it can have a fairly low delay but combined with multiple iterations
        self.speed_index = 3
        self.iteration_delays     = [0.1, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]
        self.iterations_per_ticks = [  1,    2,    4,   16,   32,   64,  128,  256, 1024]
        self.set_timer(self.iteration_delays[self.speed_index])

        self.start_cell = None
        self.end_cell = None
        self.paused = True
        self.resetting = False
        self.clearing = False
        self.solving_finished = False
        self.solving_started = False
        self.cell_color = cell_color
        self.queue = []
        self.explored_cells = {}
        self.walls = set()

        self.heuristics = [
            self.heuristic_dijkstra,
            self.heuristic_best_first,
            self.heuristic_a_star
        ]
        self.set_heuristic(0)

        self.start_color = start_color
        self.end_color = end_color
        self.trace_color = trace_color
        self.scan_color = scan_color
        self.scanned_color = scanned_color

    def set_heuristic(self, index):
        self.heuristic = self.heuristics[index]

    @property
    def iteration_delay(self):
        return self.iteration_delays[self.speed_index]

    @property
    def iterations_per_tick(self):
        return self.iterations_per_ticks[self.speed_index]

    def play(self):
        if self.solving_started:
            if self.solving_finished:
                # restart if finished
                self.solve()
            else:
                # otherwise resume
                self.paused = False
                self.start_timer(multithreaded=True)

        elif self.start_cell and self.end_cell:
            self.solve()

    def pause(self):
        self.stop_timer()

    def is_special_cell(self, cell_x, cell_y):
        if (cell_x, cell_y) == self.start_cell:
            return True
        if (cell_x, cell_y) == self.end_cell:
            return True
        return False

    def on_mouse_event(self, cell_x, cell_y, button, pressed):
        if not self.paused:
            return

        if self.solving_started:
            self.clear_solve()

        if button == LEFT_MOUSE:
            self.on_left_mouse(cell_x, cell_y, pressed)

        elif button == RIGHT_MOUSE:
            self.on_right_mouse(cell_x, cell_y)

    def on_left_mouse(self, cell_x, cell_y, pressed):
        if self.is_special_cell(cell_x, cell_y):
            return

        if not pressed:
            if (cell_x, cell_y) in self.walls:
                self.draw_delete_mode = True
            else:
                self.draw_delete_mode = False

        if self.draw_delete_mode:
            if (cell_x, cell_y) in self.walls:
                self.walls.remove((cell_x, cell_y))
                self.erase_cell(cell_x, cell_y, animation=self.animation)
        elif (cell_x, cell_y) not in self.walls:
            self.walls.add((cell_x, cell_y))
            self.draw_cell(cell_x, cell_y, self.cell_color, animation=self.animation)

    def on_right_mouse(self, cell_x, cell_y):
        if (cell_x, cell_y) in self.walls:
            self.walls.remove((cell_x, cell_y))
        if not self.start_cell:
            self.start_cell = (cell_x, cell_y)
            self.draw_cell(cell_x, cell_y, self.start_color, animation=self.animation)
        elif not self.end_cell:
            if self.start_cell == (cell_x, cell_y):
                self.erase_cell(cell_x, cell_y, animation=self.animation)
                self.start_cell = None
            else:
                self.end_cell = (cell_x, cell_y)
                self.draw_cell(cell_x, cell_y, self.end_color, animation=self.animation)
        else:
            self.erase_cell(*self.start_cell, animation=self.animation)
            self.erase_cell(*self.end_cell, animation=self.animation)
            self.start_cell = None
            self.end_cell = None

    def on_key_down(self, key):
        if key == KEY_SPACE:  # space
            if self.paused:
                self.play()
            else:
                self.pause()

        elif key == KEY_ESCAPE:  # escape
            if self.paused:
                self.clear_solve()
            else:
                self.clearing = True
                self.stop_timer()

        elif key == KEY_DELETE:
            if self.paused:
                self.reset()
            else:
                self.resetting = True
                self.stop_timer()

        elif KEY_A <= key <= KEY_C:
            if not self.paused:
                return

            self.clear_solve()
            self.set_heuristic(key - KEY_A)

        elif KEY_1 <= key <= KEY_9:
            self.speed_index = key - KEY_1
            self.set_timer(self.iteration_delay)

    def clear_solve(self):
        self.clearing = False
        self.solving_started = False
        self.solving_finished = False
        self.stop_timer()
        if self.explored_cells:
            del self.explored_cells[self.start_cell]
            for cell in self.explored_cells:
                self.erase_cell(*cell)
        self.queue = []
        self.explored_cells = {}

    def reset(self):
        self.walls = set()
        self.resetting = False
        self.start_cell = None
        self.end_cell = None
        self.queue = []
        self.explored_cells = {}
        self.solving_finished = False
        self.solving_started = False
        self.clear()

    def solve(self):
        if not self.start_cell or not self.end_cell:
            return

        if self.solving_finished:
            self.clear_solve()

        self.found_end_cell = False
        self.trace_cell = self.end_cell
        self.queue = [(self.start_cell, 0)]
        self.solving_started = True
        self.explored_cells = {self.start_cell: 1}
        self.paused = False
        self.start_timer(multithreaded=True)

    def on_timer_end(self):
        if self.resetting:
            self.reset()
        elif self.clearing:
            self.clear_solve()
        self.paused = True

    def on_timer(self, n_ticks):
        for i in range(self.iterations_per_tick):
            self.do_iteration()

    def do_iteration(self):
        if self.found_end_cell:
            self.backtrack()
        else:
            self.expand_search()

    def heuristic_best_first(self, cell):
        return abs(cell[0] - self.end_cell[0]) + \
            abs(cell[1] - self.end_cell[1])

    def heuristic_a_star(self, cell):
        return abs(cell[0] - self.end_cell[0]) + \
            abs(cell[1] - self.end_cell[1]) + self.counter
    
    def heuristic_dijkstra(self, cell):
        return self.counter

    def evaluate_path(self, cell):
        if cell not in self.explored_cells:
            return False

        counter = self.explored_cells[cell]

        # found target cell, return true
        if counter == 1:
            self.stop_timer()
            self.solving_finished = True
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
            self.solving_finished = True
        else:
            self.draw_cell(*self.chosen_cell, self.trace_color)
            self.trace_cell = self.chosen_cell

    def search_neighbour(self, cell):
        # cell has already been explored, return
        if cell in self.explored_cells:
            return

        # cell is found
        if cell == self.end_cell:
            self.found_end_cell = True
            return

        if cell not in self.walls:
            self.insert_on_heuristic(cell, self.heuristic(cell))

            # save the path length so we can use it for backtracking later
            self.explored_cells[cell] = self.counter
            self.draw_cell(*cell, self.scan_color)

    def insert_on_heuristic(self, cell, heuristic):
        if not self.queue:
            self.queue.append((cell, heuristic))

        # cells are inserted closer to the start of the array
        # we first find the bounds to perform binary search
        # more efficient than searching the entire array
        r_idx = 1
        l_idx = 0
        r_bound = len(self.queue)

        while r_idx < r_bound and self.queue[r_idx][1] < heuristic:
            l_idx = r_idx + 1
            r_idx *= 2

        r_idx = min(r_bound, r_idx)

        # binary search to find insert position (insert left)
        while l_idx < r_idx:
            m_idx = l_idx + (r_idx - l_idx) // 2
            if self.queue[m_idx][1] >= heuristic:
                r_idx = m_idx
            else:
                l_idx = m_idx + 1

        self.queue.insert(l_idx, (cell, heuristic))

    def expand_search(self):
        if not self.queue:
            self.solving_finished = True
            self.stop_timer()
            return

        (cell_x, cell_y), heuristic = self.queue.pop(0)

        if (cell_x, cell_y) != self.start_cell:
            self.draw_cell(cell_x, cell_y, self.scanned_color)

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
        grid_percentage  = config["grid_percentage"],
        fps              = config["fps"]
    )
        
    grid.start()
