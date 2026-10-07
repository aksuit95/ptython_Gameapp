"""Classic Tetris for beginners, based on README.md."""

import random
import sys

import pygame

COLS = 10
ROWS = 20
CELL = 30
SIDE = 140
WIDTH = COLS * CELL + SIDE
HEIGHT = ROWS * CELL
FPS = 60
DROP_MS = 500

BLACK = (0, 0, 0)
GRID = (40, 40, 40)
PANEL = (18, 18, 18)
WHITE = (240, 240, 240)
GHOST = (80, 80, 80)

COLORS = {
    "I": (0, 240, 240),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
    "O": (240, 240, 0),
    "S": (0, 240, 0),
    "T": (160, 0, 240),
    "Z": (240, 0, 0),
}

# Each shape is a list of rotation states. Cells are (x, y) in a 4x4 box.
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
}

SCORE_PER_LINE = 100


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.x = 3
        self.y = 0

    def cells(self, rotation=None, x=None, y=None):
        rot = self.rotation if rotation is None else rotation
        ox = self.x if x is None else x
        oy = self.y if y is None else y
        return [(ox + cx, oy + cy) for cx, cy in SHAPES[self.kind][rot % 4]]


def empty_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]


def valid(board, cells):
    for x, y in cells:
        if x < 0 or x >= COLS or y >= ROWS:
            return False
        if y >= 0 and board[y][x]:
            return False
    return True


def lock(board, piece):
    for x, y in piece.cells():
        if y < 0:
            continue
        board[y][x] = COLORS[piece.kind]


def clear_lines(board):
    kept = [row for row in board if any(cell == 0 for cell in row)]
    removed = ROWS - len(kept)
    for _ in range(removed):
        kept.insert(0, [0 for _ in range(COLS)])
    return kept, removed


def spawn():
    return Piece(random.choice(list(SHAPES)))


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = empty_board()
        self.piece = spawn()
        self.score = 0
        self.lines = 0
        self.over = not valid(self.board, self.piece.cells())
        self.drop_acc = 0

    def try_move(self, dx, dy):
        cells = self.piece.cells(x=self.piece.x + dx, y=self.piece.y + dy)
        if valid(self.board, cells):
            self.piece.x += dx
            self.piece.y += dy
            return True
        return False

    def rotate(self):
        nxt = (self.piece.rotation + 1) % 4
        if valid(self.board, self.piece.cells(rotation=nxt)):
            self.piece.rotation = nxt

    def tick_drop(self):
        if self.try_move(0, 1):
            return
        self._lock_and_continue()

    def soft_drop(self):
        if not self.try_move(0, 1):
            self._lock_and_continue()

    def _lock_and_continue(self):
        lock(self.board, self.piece)
        self.board, removed = clear_lines(self.board)
        self.lines += removed
        self.score += removed * SCORE_PER_LINE
        self.piece = spawn()
        if not valid(self.board, self.piece.cells()):
            self.over = True


def draw_cell(surface, x, y, color, origin=(0, 0)):
    ox, oy = origin
    rect = pygame.Rect(ox + x * CELL, oy + y * CELL, CELL, CELL)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, BLACK, rect, 1)


def draw(screen, font, game):
    screen.fill(BLACK)
    board_rect = pygame.Rect(0, 0, COLS * CELL, HEIGHT)
    pygame.draw.rect(screen, BLACK, board_rect)
    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(
                screen,
                GRID,
                pygame.Rect(x * CELL, y * CELL, CELL, CELL),
                1,
            )
            if game.board[y][x]:
                draw_cell(screen, x, y, game.board[y][x])

    if not game.over:
        for x, y in game.piece.cells():
            if y >= 0:
                draw_cell(screen, x, y, COLORS[game.piece.kind])

    panel = pygame.Rect(COLS * CELL, 0, SIDE, HEIGHT)
    pygame.draw.rect(screen, PANEL, panel)
    lines = [
        "TETRIS",
        "",
        f"Score",
        str(game.score),
        "",
        f"Lines",
        str(game.lines),
        "",
        "← → move",
        "↓ drop",
        "↑ rotate",
    ]
    if game.over:
        lines += ["", "GAME", "OVER", "", "R retry"]
    y = 24
    for text in lines:
        img = font.render(text, True, WHITE)
        screen.blit(img, (COLS * CELL + 12, y))
        y += 28
    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Python Tetris")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)
    game = Game()

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_r:
                game.reset()
                continue
            if game.over:
                continue
            if event.key == pygame.K_LEFT:
                game.try_move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                game.try_move(1, 0)
            elif event.key == pygame.K_DOWN:
                game.soft_drop()
            elif event.key == pygame.K_UP:
                game.rotate()

        if not game.over:
            game.drop_acc += dt
            while game.drop_acc >= DROP_MS and not game.over:
                game.drop_acc -= DROP_MS
                game.tick_drop()

        draw(screen, font, game)


if __name__ == "__main__":
    main()
