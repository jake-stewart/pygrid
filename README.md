# PyGrid
An infinite, zoomable, pannable, resizable, multi-threaded grid written in python using pygame.

## Examples

### Game of Life
An implementation of Conway's Game of Life.

![gameoflife_screenshot](./screenshots/gameoflife.png)

#### Usage
* Run `gameoflife.py`.
* Draw cells with the left mouse, or erase them with the right mouse.
* The speed of the simulation can be changed with keys 1-9.
* The algorithm can be changed with keys a, b, or c, where the algorithms are breadth-first, best-first and A* respectively.
* The simulation can be paused and resumed with space, or cleared entirely with escape.
* The grid can be cleared with delete.

### Pathfinding
Visualization of three pathfinding algorithms. `pathfinding.py`

![pathfinding_screenshot](./screenshots/pathfinding.png)

#### Usage
* Run `pathfinding.py`.
* Draw a maze with the left mouse, then place two nodes using the right mouse. Press space to watch the algorithm find a path between the two.
* The speed of the simulation can be changed with keys 1-9.
* The algorithm can be changed with keys a, b, or c, where the algorithms are breadth-first, best-first and A* respectively.
* The simulation can be paused and resumed with space, or cleared entirely with escape.
* The grid can be cleared with delete.

### Tetris

![tetris_screenshot](./screenshots/tetris.png)

#### Usage
* Run `tetris.py`.
* Use WASD, arrow keys, or hjkl as movement controls.
* Press space to drop the current shape to the bottom.
* Press q to the current shape.
* Press any key to restart after you die.

### Snake

![snake_screenshot](./screenshots/snake.png)

#### Usage
* Run `snake.py`.
* Use WASD, arrow keys, or hjkl as movement controls.
* Press any key to restart after you die.
