from draw_grid import DrawGrid
from collections import defaultdict
from keycodes import *


class GameOfLifeGrid(DrawGrid):
    def __init__(self, background_color, grid_color, cell_color, grid_thickness, fps):
        DrawGrid.__init__(
            self,
            [LEFT_MOUSE, RIGHT_MOUSE],
            background_color=background_color,
            grid_color=grid_color,
            grid_thickness=grid_thickness,
            fps=fps
        )

        self.paused = True
        self.cell_color = cell_color

        # rather than a high speed just having a low delay,
        # it can have a fairly low delay but combined with multiple iterations

        # the iterations_per_tick are odd to make the animations seem less blocky
        # this is because game of life repititions are generally even
        self.speed_index = 3
        self.iteration_delays     = [1, 0.5, 0.25, 0.1, 0.05, 0.04, 0.04, 0.04, 0.05]
        self.iterations_per_ticks = [1, 1,   1,    1,      1,    3,    5,    11,  15]

        self.set_timer(self.iteration_delay)

        self.change_list = []
        self.alive_cells = set()
        self.neighbours = defaultdict(int)

    @property
    def iteration_delay(self):
        return self.iteration_delays[self.speed_index]

    @property
    def iterations_per_tick(self):
        return self.iterations_per_ticks[self.speed_index]

    def on_mouse_event(self, cell_x, cell_y, button, pressed):
        if not self.paused:
            return

        if button == LEFT_MOUSE:
            if (cell_x, cell_y) not in self.alive_cells:
                self.draw_cell(cell_x, cell_y, self.cell_color, animate=True)
                self.add_cell(cell_x, cell_y)

        elif button == RIGHT_MOUSE:
            if (cell_x, cell_y) in self.alive_cells:
                self.erase_cell(cell_x, cell_y, animate=True)
                self.delete_cell(cell_x, cell_y)

    def do_iteration(self):
        cells_to_delete = set()
        cells_to_add = set()

        for cell_x, cell_y in self.change_list:
            for x in range(cell_x - 1, cell_x + 2):
                for y in range(cell_y - 1, cell_y + 2):

                    if (x, y) in self.alive_cells:
                        # alive cell without 2 or 3 neighbours = die
                        if not 2 <= self.neighbours[(x, y)] <= 3:
                            cells_to_delete.add((x, y))

                    elif self.neighbours[(x, y)] == 3:
                        # dead cell with 3 neighbours = born
                        cells_to_add.add((x, y))

        return cells_to_add, cells_to_delete

    def on_timer(self, n_ticks):
        for iteration in range(self.iterations_per_tick):
            cells_to_add, cells_to_delete = self.do_iteration()

            self.change_list = []

            for cell_x, cell_y in cells_to_add:
                self.add_cell(cell_x, cell_y)
                self.draw_cell(cell_x, cell_y, self.cell_color)

            for cell_x, cell_y in cells_to_delete:
                self.delete_cell(cell_x, cell_y)
                self.erase_cell(cell_x, cell_y)

    def add_cell(self, cell_x, cell_y):
        self.change_list.append((cell_x, cell_y))
        self.alive_cells.add((cell_x, cell_y))

        # when a new cell is introduced,
        # all of the surrounding cells gain a neighbour
        self.neighbours[(cell_x - 1, cell_y - 1)] += 1
        self.neighbours[(cell_x,     cell_y - 1)] += 1
        self.neighbours[(cell_x + 1, cell_y - 1)] += 1

        self.neighbours[(cell_x - 1, cell_y)]     += 1
        self.neighbours[(cell_x + 1, cell_y)]     += 1

        self.neighbours[(cell_x - 1, cell_y + 1)] += 1
        self.neighbours[(cell_x,     cell_y + 1)] += 1
        self.neighbours[(cell_x + 1, cell_y + 1)] += 1

    def delete_cell(self, cell_x, cell_y):
        self.alive_cells.remove((cell_x, cell_y))
        self.change_list.append((cell_x, cell_y))

        # when a cell is removed,
        # all of the surrounding cells lose a neighbour
        self.neighbours[(cell_x - 1, cell_y - 1)] -= 1
        self.neighbours[(cell_x,     cell_y - 1)] -= 1
        self.neighbours[(cell_x + 1, cell_y - 1)] -= 1

        self.neighbours[(cell_x - 1, cell_y)]     -= 1
        self.neighbours[(cell_x + 1, cell_y)]     -= 1

        self.neighbours[(cell_x - 1, cell_y + 1)] -= 1
        self.neighbours[(cell_x,     cell_y + 1)] -= 1
        self.neighbours[(cell_x + 1, cell_y + 1)] -= 1

    def on_key_down(self, key):
        if key == KEY_SPACE:
            if self.paused:
                if self.change_list:
                    self.play()
            else:
                self.pause()

        elif KEY_1 <= key <= KEY_9:
            self.speed_index = key - KEY_1
            if not self.paused:
                self.set_timer(self.iteration_delay)

        elif key == KEY_DELETE:
            self.reset()

    def reset(self):
        self.stop_timer()
        self.clear()
        self.change_list = []
        self.alive_cells = set()
        self.neighbours = defaultdict(int)
        self.paused = True

    def pause(self):
        self.stop_timer()
        self.paused = True

    def play(self):
        self.start_timer(multithreaded=True)
        self.paused = False

if __name__ == "__main__":
    from config import config

    grid = GameOfLifeGrid(
        background_color = config["background_color"],
        cell_color       = config["cell_color"],
        grid_color       = config["grid_color"],
        grid_thickness   = config["grid_thickness"],
        fps              = config["fps"]
    )
    grid.start()
