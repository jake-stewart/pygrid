from pygrid import PyGrid
from keycodes import *
import random

UP_KEYS    = {KEY_UP,    KEY_K, KEY_W}
LEFT_KEYS  = {KEY_LEFT,  KEY_H, KEY_A}
DOWN_KEYS  = {KEY_DOWN,  KEY_J, KEY_S}
RIGHT_KEYS = {KEY_RIGHT, KEY_L, KEY_D}


# game modes
NOT_PLAYING = 0
PLAYING = 1
PAUSED = 2
DEAD = 3
DYING = 4
RESETTING = 5


class SnakeGrid(PyGrid):
    def __init__(self, width=16, height=16, start_length=4, delay=0.05, n_chances=5,
                 growth_rate=5, cell_size=45, grid_thickness=0, grid_color = (50, 50, 50),
                 background_color=(255, 255, 255), snake_color=(0, 255, 0),
                 food_color=(255, 0, 0), death_color=(0, 0, 255), fps=60):

        PyGrid.__init__(
            self,
            n_columns=width,
            n_rows=height,
            cell_size=cell_size,
            grid_thickness=grid_thickness,
            grid_color=grid_color,
            allowed_resize=False,
            allowed_pan=False,
            allowed_zoom=False,
            background_color=background_color,
            animation_duration=0.1,
            fps=fps
        )

        self.background_color = background_color
        self.growth_rate = 5
        self.snake_color = snake_color
        self.food_color = food_color
        self.death_color = death_color

        self.food_pos = (0, 0)

        self.animation_delay = 0.5
        self.delay = delay
        self.n_chances = n_chances

        self.width = width
        self.height = height
        self.n_cells = width * height

        self.game_state = NOT_PLAYING
        if start_length > width // 2 + 1:
            self.start_length = width // 2 + 1
        else:
            self.start_length = start_length

    def on_start(self):
        self.reset()

    def new_food(self):
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.tail_hash:
                break

        self.draw_cell(x, y, self.food_color, animate=True)
        self.food_cell = (x, y)

    def move(self):
        if self.chances == self.n_chances:
            tail = self.tail_queue.pop(0)
            if self.tail_queue[0] != tail:
                self.draw_cell(*tail, self.background_color)
                self.tail_hash.remove(tail)

        if self.direction[0]:
            x = (self.x + self.direction[0]) % self.width
            y = self.y
        else:
            x = self.x
            y = (self.y + self.direction[1]) % self.height

        # crash!
        if (x, y) in self.tail_hash:
            if not self.chances:
                self.die()

            self.chances -= 1
            self.next_direction = None
            return

        self.x = x
        self.y = y

        # reset chances since we are no longer crashing
        self.chances = self.n_chances
        
        self.tail_queue.append((x, y))
        self.tail_hash.add((x, y))
        self.draw_cell(x, y, self.snake_color)

        if (x, y) == self.food_cell:
            if len(self.tail_hash) == self.n_cells:
                self.win()
            else:
                self.eat_food()
            self.new_food()

        # allows user to press a key for a direction before the snake has moved
        self.last_direction = self.direction
        if self.next_direction:
            if not self.direction_clash(self.next_direction):
                self.direction = self.next_direction
            self.next_direction = None

    def win(self):
        # user probably expects a reward,
        # instead they get to restart LOL
        # at least the colours flip which is fun
        self.tail_hash = {(self.x, self.y)}
        self.tail_queue = [(self.x, self.y) for i in range(self.start_length)]
        self.snake_color, self.background_color = \
            self.background_color, self.snake_color

    def eat_food(self):
        last_tail = self.tail_queue[0]
        for i in range(self.growth_rate):
            self.tail_queue.insert(0, last_tail)

    def die(self):
        self.set_timer(self.animation_delay)
        self.game_state = DYING
        self.draw_cell(self.x, self.y, self.death_color, animate=True)

    def on_timer(self, n_ticks):
        if self.game_state == PLAYING:
            self.move()
        elif self.game_state == DYING:
            self.game_state = DEAD
            self.stop_timer()
        else:
            self.set_timer(self.delay)
            self.game_state = PLAYING
        self.timer_tick()

    def reset(self):
        if self.game_state == DEAD:
            for tail in self.tail_queue:
                self.draw_cell(*tail, self.background_color, animate=True)
            self.draw_cell(*self.food_cell, self.background_color, animate=True)

        self.game_state = RESETTING
        self.chances = self.n_chances

        self.tail_queue = []
        self.tail_hash = set()
        self.x = self.width // 2
        self.y = self.height // 2

        x = self.x - self.start_length
        y = self.y

        for i in range(self.start_length):
            x += 1
            self.tail_queue.append((x, y))
            self.tail_hash.add((x, y))
            self.draw_cell(x, y, self.snake_color, animate=True)

        self.next_direction = None
        self.direction_set = False
        self.direction = (1, 0)
        self.last_direction = self.direction
        self.new_food()

        self.set_timer(self.animation_delay)
        self.start_timer()

    def on_key_down(self, key):
        if self.game_state == DEAD:
            self.reset()
        
        elif self.game_state == PAUSED:
            if key == KEY_P or key == KEY_SPACE:
                self.play()

        elif self.game_state == PLAYING:
            if key in UP_KEYS:
                self.set_direction((0, -1))

            elif key in DOWN_KEYS:
                self.set_direction((0, 1))

            elif key in LEFT_KEYS:
                self.set_direction((-1, 0))

            elif key in RIGHT_KEYS:
                self.set_direction((1, 0))

            elif key == KEY_P or key == KEY_SPACE:
                self.pause()

            elif key == KEY_SPACE:
                self.tail_queue.insert(0, self.tail_queue[0])

    def set_direction(self, direction):
        if self.next_direction:
            self.next_direction = direction

        elif not self.direction_clash(direction):
            self.direction = direction
            self.next_direction = direction

    def direction_clash(self, direction):
        if self.last_direction[0]:
            return self.last_direction[0] == -direction[0]
        else:
            return self.last_direction[1] == -direction[1]

    def pause(self):
        self.stop_timer()
        self.game_state = PAUSED

    def play(self):
        self.start_timer()
        self.game_state = PLAYING

if __name__ == "__main__":
    from config import config

    grid = SnakeGrid(
        background_color = config["background_color"],
        grid_color       = config["grid_color"],
        grid_thickness   = config["grid_thickness"],
        snake_color      = config["green"],
        food_color       = config["blue"],
        death_color      = config["red"],
        fps              = config["fps"]
    )

    grid.start()
