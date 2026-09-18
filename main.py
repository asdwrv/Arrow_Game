import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 3
CELL_SIZE = 120
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
GRID_LEFT = (SCREEN_WIDTH - GRID_WIDTH) // 2
GRID_TOP = (SCREEN_HEIGHT - GRID_HEIGHT) // 2 + 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BOARD_BG = (60, 60, 70)
BLUE = (70, 130, 200)
RED = (220, 70, 70)
GREEN = (70, 200, 100)
ORANGE = (240, 140, 40)

# Arrow directions
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# Direction vectors: (d_row, d_col)
DIR_VECTORS = {
    UP:    (-1, 0),
    DOWN:  (1, 0),
    LEFT:  (0, -1),
    RIGHT: (0, 1)
}

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_WIN = 3

MAX_MISTAKES = 3
FPS = 60


# --- Helper Functions ---
def draw_text(surface, text, size, x, y, color=BLACK, center=True):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(text_surface, rect)


def draw_arrow(surface, cx, cy, direction, size=48, color=BLUE, alpha=255):
    """
    Draw an arrow at (cx, cy) pointing in the given direction.
    We directly define polygon vertices for each direction, so the visual
    direction always matches the logical direction.
    """
    arrow_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    s = size

    if direction == UP:
        points = [
            (s, s * 0.3),
            (s * 1.6, s * 1.5),
            (s, s * 1.1),
            (s * 0.4, s * 1.5),
        ]
    elif direction == DOWN:
        points = [
            (s, s * 1.7),
            (s * 0.4, s * 0.5),
            (s, s * 0.9),
            (s * 1.6, s * 0.5),
        ]
    elif direction == LEFT:
        points = [
            (s * 0.3, s),
            (s * 1.5, s * 0.4),
            (s * 1.1, s),
            (s * 1.5, s * 1.6),
        ]
    elif direction == RIGHT:
        points = [
            (s * 1.7, s),
            (s * 0.5, s * 0.4),
            (s * 0.9, s),
            (s * 0.5, s * 1.6),
        ]
    else:
        points = [(s, s), (s, s), (s, s)]

    pygame.draw.polygon(arrow_surf, (*color, alpha), points)
    pygame.draw.polygon(arrow_surf, (0, 0, 0, alpha), points, 3)

    surface.blit(arrow_surf, (cx - size, cy - size))


# --- Arrow Class ---
class Arrow:
    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction
        self.state = 'idle'
        self.offset_x = 0
        self.offset_y = 0
        self.shake_timer = 0
        self.shake_offset = 0
        self.fly_speed = 18
        self.fly_distance = 0
        self.alpha = 255

    def get_base_center(self):
        base_x = GRID_LEFT + self.col * CELL_SIZE + CELL_SIZE // 2
        base_y = GRID_TOP + self.row * CELL_SIZE + CELL_SIZE // 2
        return base_x, base_y

    def get_center(self):
        base_x, base_y = self.get_base_center()
        return base_x + self.offset_x, base_y + self.offset_y

    def update(self):
        if self.state == 'flying':
            dr, dc = DIR_VECTORS[self.direction]
            self.offset_x += dc * self.fly_speed
            self.offset_y += dr * self.fly_speed
            self.fly_distance += self.fly_speed
            self.alpha = max(0, 255 - int(self.fly_distance * 1.5))

            if self.alpha <= 0:
                return False
            cx, cy = self.get_center()
            if cx < -150 or cx > SCREEN_WIDTH + 150:
                return False
            if cy < -150 or cy > SCREEN_HEIGHT + 150:
                return False
            if self.fly_distance > 900:
                return False

        elif self.state == 'shaking':
            self.shake_timer += 1
            if self.shake_timer > 22:
                self.state = 'idle'
                self.shake_offset = 0
                self.shake_timer = 0
                self.offset_x = 0
                self.offset_y = 0
            else:
                amplitude = 9 * (1 - self.shake_timer / 22)
                self.shake_offset = math.sin(self.shake_timer * 1.8) * amplitude
                if self.direction in (UP, DOWN):
                    self.offset_x = self.shake_offset
                    self.offset_y = 0
                else:
                    self.offset_x = 0
                    self.offset_y = self.shake_offset
        return True

    def start_fly(self):
        self.state = 'flying'
        self.fly_distance = 0
        self.alpha = 255
        self.offset_x = 0
        self.offset_y = 0

    def start_shake(self):
        self.state = 'shaking'
        self.shake_timer = 0
        self.shake_offset = 0
        self.offset_x = 0
        self.offset_y = 0

    def is_idle(self):
        return self.state == 'idle'

    def draw(self, surface):
        cx, cy = self.get_center()
        draw_arrow(surface, cx, cy, self.direction, size=48, color=BLUE, alpha=self.alpha)


# --- Game Class ---
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("One Arrow After Another")
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU
        self.level = 1
        self.mistakes = 0
        self.arrows = []
        self.flying_arrows = []
        self.message = ""

        # Levels: row 0 is TOP, row 2 is BOTTOM
        # UP = 0, DOWN = 1, LEFT = 2, RIGHT = 3
        #
        # Level 1:
        #   ↑  ↑  ↑
        #   ←  ↑  →
        #   ↓  ↓  ↓
        #
        # Level 2:
        #   ←  ↑  →
        #   ↑  ↓  ↑
        #   ←  ↓  ←
        #
        # Level 3:
        #   ↑  ↑  ↑
        #   ←  ↓  →
        #   ↓  ↓  ↓
        self.level_data = [
            # Level 1
            [
                [UP,    UP,    UP],
                [LEFT,  UP,    RIGHT],
                [DOWN,  DOWN,  DOWN]
            ],
            # Level 2
            [
                [LEFT,  UP,    RIGHT],
                [UP,    DOWN,  UP],
                [LEFT,  DOWN,  LEFT]
            ],
            # Level 3
            [
                [UP,    UP,    UP],
                [LEFT,  DOWN,  RIGHT],
                [DOWN,  DOWN,  DOWN]
            ]
        ]

    def reset_level(self, level):
        """Load arrows for the given level and reset mistakes."""
        self.arrows.clear()
        self.flying_arrows.clear()
        data = self.level_data[level - 1]
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                direction = data[r][c]
                if direction is not None:
                    self.arrows.append(Arrow(r, c, direction))
        self.mistakes = 0

    def restart_current_level(self):
        """
        Restart the current level without changing level number.
        - Reload arrows to initial state
        - Reset mistakes to 0
        - Clear all flying arrows immediately
        """
        self.reset_level(self.level)

    def start_game(self):
        """Start a brand-new game from Level 1."""
        self.level = 1
        self.mistakes = 0
        self.reset_level(self.level)
        self.state = STATE_PLAYING

    def next_level(self):
        self.level += 1
        if self.level > 3:
            self.state = STATE_WIN
            self.message = "You cleared all 3 levels!"
        else:
            self.reset_level(self.level)

    def is_path_clear(self, arrow):
        """
        Strict direction-only path check.
        """
        dr, dc = DIR_VECTORS[arrow.direction]

        r = arrow.row + dr
        c = arrow.col + dc

        while 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            for other in self.arrows:
                if other is arrow:
                    continue
                if other.row == r and other.col == c:
                    return False
            r += dr
            c += dc

        return True

    def check_click(self, pos):
        if self.state != STATE_PLAYING:
            return
        if len(self.flying_arrows) > 0:
            return

        for arrow in reversed(self.arrows):
            if not arrow.is_idle():
                continue
            cx, cy = arrow.get_center()
            rect = pygame.Rect(cx - 50, cy - 50, 100, 100)
            if rect.collidepoint(pos):
                if self.is_path_clear(arrow):
                    self.arrows.remove(arrow)
                    arrow.start_fly()
                    self.flying_arrows.append(arrow)
                else:
                    arrow.start_shake()
                    self.mistakes += 1
                    if self.mistakes >= MAX_MISTAKES:
                        self.state = STATE_GAME_OVER
                        self.message = "Too many mistakes!"
                return

    def update(self):
        for arrow in self.flying_arrows[:]:
            if not arrow.update():
                self.flying_arrows.remove(arrow)

        for arrow in self.arrows:
            arrow.update()

        if self.state == STATE_PLAYING:
            if len(self.arrows) == 0 and len(self.flying_arrows) == 0:
                self.next_level()

    def draw_grid(self):
        board_rect = pygame.Rect(GRID_LEFT - 6, GRID_TOP - 6, GRID_WIDTH + 12, GRID_HEIGHT + 12)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, (GRID_LEFT, GRID_TOP, GRID_WIDTH, GRID_HEIGHT))

        for i in range(GRID_SIZE + 1):
            x = GRID_LEFT + i * CELL_SIZE
            pygame.draw.line(self.screen, GRAY, (x, GRID_TOP), (x, GRID_TOP + GRID_HEIGHT), 2)
            y = GRID_TOP + i * CELL_SIZE
            pygame.draw.line(self.screen, GRAY, (GRID_LEFT, y), (GRID_LEFT + GRID_WIDTH, y), 2)

    def draw_ui(self):
        """Draw HUD: level, mistakes, and restart hint."""
        draw_text(self.screen, f"Level: {self.level} / 3", 40, SCREEN_WIDTH // 2, 40, BLACK)
        mistakes_text = f"Mistakes: {self.mistakes} / {MAX_MISTAKES}"
        color = RED if self.mistakes >= MAX_MISTAKES - 1 else BLACK
        draw_text(self.screen, mistakes_text, 34, SCREEN_WIDTH - 170, 40, color)

        # --- New: Restart hint in the bottom-left corner ---
        draw_text(
            self.screen,
            "Press F1 to Restart Level",
            26,
            170,
            SCREEN_HEIGHT - 25,
            ORANGE,
            center=True
        )

    def draw(self):
        self.screen.fill((240, 245, 250))

        if self.state == STATE_MENU:
            draw_text(self.screen, "ONE ARROW", 90, SCREEN_WIDTH // 2, 140, BLUE)
            draw_text(self.screen, "AFTER ANOTHER", 70, SCREEN_WIDTH // 2, 220, BLUE)
            draw_text(self.screen, "Click an arrow to shoot it out", 36, SCREEN_WIDTH // 2, 320, BLACK)
            draw_text(self.screen, "If blocked, it shakes and you lose a life", 30, SCREEN_WIDTH // 2, 370, DARK_GRAY)
            draw_text(self.screen, "Lose 3 times and game over", 30, SCREEN_WIDTH // 2, 410, DARK_GRAY)
            draw_text(self.screen, "Press any key to start", 42, SCREEN_WIDTH // 2, 500, GREEN)

        elif self.state == STATE_PLAYING:
            self.draw_grid()
            self.draw_ui()
            for arrow in self.arrows:
                arrow.draw(self.screen)
            for arrow in self.flying_arrows:
                arrow.draw(self.screen)

        elif self.state == STATE_GAME_OVER:
            draw_text(self.screen, "GAME OVER", 90, SCREEN_WIDTH // 2, 200, RED)
            draw_text(self.screen, self.message, 44, SCREEN_WIDTH // 2, 300, BLACK)
            # --- Changed: any key to restart ---
            draw_text(self.screen, "Press any key to restart", 44, SCREEN_WIDTH // 2, 440, BLUE)

        elif self.state == STATE_WIN:
            draw_text(self.screen, "YOU WIN!", 90, SCREEN_WIDTH // 2, 180, GREEN)
            draw_text(self.screen, self.message, 44, SCREEN_WIDTH // 2, 290, BLACK)
            # --- Changed: any key to restart ---
            draw_text(self.screen, "Press any key to restart", 44, SCREEN_WIDTH // 2, 440, BLUE)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    # --- Menu: any key starts the game ---
                    if self.state == STATE_MENU:
                        self.start_game()

                    # --- Playing: F1 restarts the current level ---
                    elif self.state == STATE_PLAYING:
                        if event.key == pygame.K_F1:
                            self.restart_current_level()

                    # --- Game Over / Win: any key restarts from Level 1 ---
                    elif self.state in (STATE_GAME_OVER, STATE_WIN):
                        self.start_game()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.state == STATE_PLAYING:
                        self.check_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# --- Entry Point ---
if __name__ == "__main__":
    game = Game()
    game.run()