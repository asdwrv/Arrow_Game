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

# --- Colors (dark theme) ---
BACKGROUND = (20, 30, 50)       # deep navy background
CELL_BG = (50, 60, 80)          # dark gray cell
GRID_LINE = (150, 160, 180)     # light gray grid lines
BOARD_BORDER = (30, 40, 60)     # darker border around the board
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
BLUE = (70, 130, 200)
LIGHT_BLUE = (150, 200, 255)
RED = (230, 80, 80)
GREEN = (80, 220, 120)
YELLOW = (245, 210, 80)
ORANGE = (245, 150, 60)

# Arrow directions
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

DIR_VECTORS = {
    UP:    (-1, 0),
    DOWN:  (1, 0),
    LEFT:  (0, -1),
    RIGHT: (0, 1)
}

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_LEVEL_CLEAR = 2   # show "Level Clear!" for a moment
STATE_GAME_OVER = 3
STATE_WIN = 4

MAX_MISTAKES = 3
FPS = 60

# How long (in milliseconds) to show "Level Clear!" before advancing
LEVEL_CLEAR_DURATION = 1000


# --- Helper Functions ---
def draw_text(surface, text, size, x, y, color=WHITE, center=True):
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
    Blue fill with a bright white outline so it pops on the dark board.
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

    # Blue fill
    pygame.draw.polygon(arrow_surf, (*color, alpha), points)
    # White outline (bright, thick) to make the arrow stand out
    pygame.draw.polygon(arrow_surf, (255, 255, 255, alpha), points, 4)

    surface.blit(arrow_surf, (cx - size, cy - size))


def format_time(seconds):
    """Format seconds as MM:SS."""
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


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

        # Level clear animation timer
        self.level_clear_start_time = 0

        # Overall game timer
        self.game_start_time = 0
        self.total_time = 0.0    # frozen time shown on end screens

        # Levels: row 0 is TOP, row 2 is BOTTOM
        # UP = 0, DOWN = 1, LEFT = 2, RIGHT = 3
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
        """Restart the current level without changing level number."""
        self.reset_level(self.level)

    def start_game(self):
        """Start a brand-new game from Level 1."""
        self.level = 1
        self.mistakes = 0
        self.reset_level(self.level)
        self.game_start_time = pygame.time.get_ticks()
        self.total_time = 0.0
        self.state = STATE_PLAYING

    def is_path_clear(self, arrow):
        """Strict direction-only path check."""
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
                        # Freeze the timer for the game-over screen
                        self.total_time = (pygame.time.get_ticks() - self.game_start_time) / 1000.0
                        self.state = STATE_GAME_OVER
                        self.message = "Too many mistakes!"
                return

    def get_elapsed_time(self):
        """Return elapsed seconds since the game started (for the HUD)."""
        return (pygame.time.get_ticks() - self.game_start_time) / 1000.0

    def update(self):
        # Update flying arrows
        for arrow in self.flying_arrows[:]:
            if not arrow.update():
                self.flying_arrows.remove(arrow)

        # Update arrows on the grid (shaking)
        for arrow in self.arrows:
            arrow.update()

        # Detect level completion
        if self.state == STATE_PLAYING:
            if len(self.arrows) == 0 and len(self.flying_arrows) == 0:
                # Enter the "Level Clear!" state and start the timer
                self.state = STATE_LEVEL_CLEAR
                self.level_clear_start_time = pygame.time.get_ticks()

        # Handle the "Level Clear!" pause
        elif self.state == STATE_LEVEL_CLEAR:
            elapsed = pygame.time.get_ticks() - self.level_clear_start_time
            if elapsed >= LEVEL_CLEAR_DURATION:
                # Advance to the next level (or win)
                self.level += 1
                if self.level > 3:
                    self.total_time = (pygame.time.get_ticks() - self.game_start_time) / 1000.0
                    self.state = STATE_WIN
                    self.message = "You cleared all 3 levels!"
                else:
                    self.reset_level(self.level)
                    self.state = STATE_PLAYING

    def draw_grid(self):
        """Draw the board with the new dark theme."""
        # Board border
        board_rect = pygame.Rect(GRID_LEFT - 6, GRID_TOP - 6, GRID_WIDTH + 12, GRID_HEIGHT + 12)
        pygame.draw.rect(self.screen, BOARD_BORDER, board_rect, border_radius=12)

        # Cell backgrounds
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell_rect = pygame.Rect(
                    GRID_LEFT + c * CELL_SIZE,
                    GRID_TOP + r * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                pygame.draw.rect(self.screen, CELL_BG, cell_rect)

        # Grid lines (light gray)
        for i in range(GRID_SIZE + 1):
            x = GRID_LEFT + i * CELL_SIZE
            pygame.draw.line(self.screen, GRID_LINE, (x, GRID_TOP), (x, GRID_TOP + GRID_HEIGHT), 2)
            y = GRID_TOP + i * CELL_SIZE
            pygame.draw.line(self.screen, GRID_LINE, (GRID_LEFT, y), (GRID_LEFT + GRID_WIDTH, y), 2)

        # Outer edge of the board
        pygame.draw.rect(self.screen, GRID_LINE,
                         (GRID_LEFT, GRID_TOP, GRID_WIDTH, GRID_HEIGHT), 3)

    def draw_ui(self):
        """Draw HUD: level, mistakes, timer, restart hint."""
        # Level (center top)
        draw_text(self.screen, f"Level: {self.level} / 3", 40,
                  SCREEN_WIDTH // 2, 40, WHITE)

        # Mistakes (top right)
        mistakes_text = f"Mistakes: {self.mistakes} / {MAX_MISTAKES}"
        color = RED if self.mistakes >= MAX_MISTAKES - 1 else WHITE
        draw_text(self.screen, mistakes_text, 32,
                  SCREEN_WIDTH - 130, 40, color)

        # Timer (top left)
        elapsed = self.get_elapsed_time()
        draw_text(self.screen, f"Time: {format_time(elapsed)}", 32,
                  130, 40, WHITE)

        # Restart hint (bottom-left)
        draw_text(self.screen, "Press F1 to Restart Level", 24,
                  160, SCREEN_HEIGHT - 25, ORANGE, center=True)

    def draw_level_clear_overlay(self):
        """Big green 'Level Clear!' text in the middle."""
        # Semi-transparent dark overlay for contrast
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        # Big green text
        draw_text(self.screen, "Level Clear!", 110,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GREEN)

    def draw(self):
        self.screen.fill(BACKGROUND)

        if self.state == STATE_MENU:
            draw_text(self.screen, "ONE ARROW", 90, SCREEN_WIDTH // 2, 140, LIGHT_BLUE)
            draw_text(self.screen, "AFTER ANOTHER", 70, SCREEN_WIDTH // 2, 220, LIGHT_BLUE)
            draw_text(self.screen, "Click an arrow to shoot it out", 36, SCREEN_WIDTH // 2, 320, WHITE)
            draw_text(self.screen, "If blocked, it shakes and you lose a life", 30,
                      SCREEN_WIDTH // 2, 370, GRAY)
            draw_text(self.screen, "Lose 3 times and game over", 30,
                      SCREEN_WIDTH // 2, 410, GRAY)
            draw_text(self.screen, "Press any key to start", 42,
                      SCREEN_WIDTH // 2, 500, GREEN)

        elif self.state in (STATE_PLAYING, STATE_LEVEL_CLEAR):
            self.draw_grid()
            self.draw_ui()
            for arrow in self.arrows:
                arrow.draw(self.screen)
            for arrow in self.flying_arrows:
                arrow.draw(self.screen)

            if self.state == STATE_LEVEL_CLEAR:
                self.draw_level_clear_overlay()

        elif self.state == STATE_GAME_OVER:
            draw_text(self.screen, "GAME OVER", 90, SCREEN_WIDTH // 2, 160, RED)
            draw_text(self.screen, self.message, 40, SCREEN_WIDTH // 2, 250, WHITE)
            draw_text(self.screen, f"Time: {format_time(self.total_time)}", 44,
                      SCREEN_WIDTH // 2, 330, YELLOW)
            draw_text(self.screen, f"Level reached: {self.level} / 3", 34,
                      SCREEN_WIDTH // 2, 390, GRAY)
            draw_text(self.screen, "Press any key to restart", 44,
                      SCREEN_WIDTH // 2, 480, LIGHT_BLUE)

        elif self.state == STATE_WIN:
            draw_text(self.screen, "YOU WIN!", 90, SCREEN_WIDTH // 2, 150, GREEN)
            draw_text(self.screen, self.message, 40, SCREEN_WIDTH // 2, 240, WHITE)
            draw_text(self.screen, f"Total Time: {format_time(self.total_time)}", 50,
                      SCREEN_WIDTH // 2, 330, YELLOW)
            draw_text(self.screen, "All 3 levels cleared!", 34,
                      SCREEN_WIDTH // 2, 400, GRAY)
            draw_text(self.screen, "Press any key to restart", 44,
                      SCREEN_WIDTH // 2, 480, LIGHT_BLUE)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if self.state == STATE_MENU:
                        self.start_game()

                    elif self.state == STATE_PLAYING:
                        if event.key == pygame.K_F1:
                            self.restart_current_level()

                    elif self.state in (STATE_GAME_OVER, STATE_WIN):
                        self.start_game()
                    # Note: no key handling in STATE_LEVEL_CLEAR — let it play out

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.state == STATE_PLAYING:
                        self.check_click(event.pos)

            # Update (skip during the Level Clear pause; the timer handles it)
            if self.state in (STATE_PLAYING, STATE_LEVEL_CLEAR):
                self.update()

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# --- Entry Point ---
if __name__ == "__main__":
    game = Game()
    game.run()
