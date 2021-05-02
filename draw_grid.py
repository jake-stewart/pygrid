from pygrid import PyGrid
import math

# adds drawing functionality
# when using a mouse, mouse events are sent periodically
# that means mouse events will not register for every cell
# this class figures out which cells the mouse traversed over
# and sends them to an on_mouse_event method

class DrawGrid(PyGrid):
    def __init__(self, draw_buttons=None, *args, **kwargs):
        PyGrid.__init__(self, *args, **kwargs)

        if draw_buttons is None:
            self._draw_buttons = [1]
        else:
            self._draw_buttons = draw_buttons

        self._origin = None
        self._button_down = None

    # when inheriting this class, use this method for all mouse events
    def on_mouse_event(self, cell_x, cell_y, button, pressed):
        pass

    def on_mouse_down(self, cell_x, cell_y, button):
        if button in self._draw_buttons:
            self._origin = (cell_x, cell_y)
            self._button_down = button

        self.on_mouse_event(cell_x, cell_y, button, False)

    def on_mouse_up(self, cell_x, cell_y, button):
        if button == self._button_down:
            self._button_down = None

    def on_mouse_motion(self, target_x, target_y):
        if not self._button_down:
            return

        # origin is the previous mouse event position
        origin_x, origin_y = self._origin

        angle = math.atan2(target_x - origin_x, target_y - origin_y)
        x_vel = math.sin(angle)
        y_vel = math.cos(angle)

        # if there is no x movement or no y movement, we do not need their respective vel
        if origin_x == target_x:
            x_vel = 0
        elif origin_y == target_y:
            y_vel = 0

        # initialize variables
        x = last_x = cell_x = origin_x
        y = last_y = cell_y = origin_y
        fill_x = True

        while True:
            if cell_x == target_x:
                if cell_y == target_y:
                    # both cells have reached their targets
                    # loop can end
                    break
                y += y_vel
            else:
                if cell_y != target_y:
                    y += y_vel
                x += x_vel

            # you can use int() instead of round(), but round() is smoother
            cell_x = round(x)
            cell_y = round(y)

            # avoid multiple mouse events over the same cell
            if cell_x == last_x and cell_y == last_y:
                continue

            # trigger a mouse event for a traversed cell
            self.on_mouse_event(cell_x, cell_y, self._button_down, True)

            # if the cell jumped diagonally, we want to fill it in
            # whether we fill the cell on the x axis or y axis is important
            # if we always fill one axis, it will look choppy
            # filling follows the rule: always fill y, unless y has had > 2 cells for the current x

            if last_x != cell_x and last_y != cell_y:
                if fill_x:
                    self.on_mouse_event(last_x, cell_y, self._button_down, True)
                else:
                    self.on_mouse_event(cell_x, last_y, self._button_down, True)
            else:
                fill_x = last_y == cell_y

            last_x = cell_x
            last_y = cell_y
        self._origin = (cell_x, cell_y)

if __name__ == "__main__":
    from config import config

    cell_color = config["cell_color"]

    def on_mouse_event(self, cell_x, cell_y, button, pressed):
        if button == 1:
            self.draw_cell(cell_x, cell_y, cell_color, animate=True)
        elif button == 3:
            self.erase_cell(cell_x, cell_y, animate=True)

    DrawGrid.on_mouse_event = on_mouse_event

    grid = DrawGrid(
        [1, 3],
        grid_color       = config["grid_color"],
        background_color = config["background_color"],
        grid_thickness   = config["grid_thickness"],
        fps              = config["fps"]
    )
    grid.start()

