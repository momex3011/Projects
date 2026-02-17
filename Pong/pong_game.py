import pygame
import random

# --- Constants ---
WIDTH = 900
HEIGHT = 600
FPS = 60
WIN_SCORE = 10

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50) # Darker gray for buttons
GREEN = (0, 150, 0) # Highlight color

# --- NEW: Difficulty Settings ---
# A dictionary to hold the parameters for each difficulty level
DIFFICULTY_SETTINGS = {
    "Easy": {
        "opponent_speed": 4,
        "ball_speed_increase": 1.05
    },
    "Normal": {
        "opponent_speed": 6,
        "ball_speed_increase": 1.1
    },
    "Hard": {
        "opponent_speed": 8,
        "ball_speed_increase": 1.15
    }
}
current_difficulty_settings = DIFFICULTY_SETTINGS["Normal"] # Default to Normal

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# --- Game Classes ---

class Paddle(pygame.sprite.Sprite):
    # (This class is unchanged)
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([10, 100])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Player(Paddle):
    # (This class is unchanged)
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self):
        pos = pygame.mouse.get_pos()
        self.rect.y = pos[1]
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

class Opponent(Paddle):
    # --- CHANGED: Now accepts a speed parameter ---
    def __init__(self, x, y, speed):
        super().__init__(x, y)
        self.speed = speed # Speed is now set based on difficulty

    def update(self, ball):
        if self.rect.centery < ball.rect.centery: self.rect.y += self.speed
        if self.rect.centery > ball.rect.centery: self.rect.y -= self.speed
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([10, 10])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self):
        self.rect.center = (WIDTH / 2, HEIGHT / 2)
        self.speed_x = random.choice([-5, 5])
        self.speed_y = random.choice([-5, 5])

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT: self.speed_y *= -1

    def bounce(self):
        self.speed_x *= -1
        # --- CHANGED: Speed increase now depends on difficulty ---
        increase = current_difficulty_settings["ball_speed_increase"]
        self.speed_x *= increase
        self.speed_y *= increase

# --- UI and Screen Functions ---
font_name = pygame.font.match_font('arial')
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    surf.blit(text_surface, text_rect)

def draw_court():
    screen.fill(BLACK)
    pygame.draw.line(screen, WHITE, (WIDTH / 2, 0), (WIDTH / 2, HEIGHT), 2)

# --- NEW: Overhauled Start Screen with Buttons ---
def show_start_screen():
    global current_difficulty_settings
    
    # Create button rectangles
    button_width = 150
    button_height = 50
    button_y = HEIGHT * 3 / 4
    
    easy_button = pygame.Rect(WIDTH/4 - button_width/2, button_y, button_width, button_height)
    normal_button = pygame.Rect(WIDTH/2 - button_width/2, button_y, button_width, button_height)
    hard_button = pygame.Rect(WIDTH*3/4 - button_width/2, button_y, button_width, button_height)

    waiting = True
    while waiting:
        clock.tick(FPS)
        
        # --- Event Handling for the menu ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse click
                    if easy_button.collidepoint(event.pos):
                        current_difficulty_settings = DIFFICULTY_SETTINGS["Easy"]
                        waiting = False
                    elif normal_button.collidepoint(event.pos):
                        current_difficulty_settings = DIFFICULTY_SETTINGS["Normal"]
                        waiting = False
                    elif hard_button.collidepoint(event.pos):
                        current_difficulty_settings = DIFFICULTY_SETTINGS["Hard"]
                        waiting = False

        # --- Drawing the menu ---
        screen.fill(BLACK)
        draw_text(screen, "PONG", 100, WIDTH / 2, HEIGHT / 4)
        draw_text(screen, "Select a Difficulty", 40, WIDTH / 2, HEIGHT / 2)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw Easy Button
        if easy_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, easy_button)
        else:
            pygame.draw.rect(screen, GRAY, easy_button)
        draw_text(screen, "Easy", 30, easy_button.centerx, easy_button.centery)

        # Draw Normal Button
        if normal_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, normal_button)
        else:
            pygame.draw.rect(screen, GRAY, normal_button)
        draw_text(screen, "Normal", 30, normal_button.centerx, normal_button.centery)

        # Draw Hard Button
        if hard_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, hard_button)
        else:
            pygame.draw.rect(screen, GRAY, hard_button)
        draw_text(screen, "Hard", 30, hard_button.centerx, hard_button.centery)
        
        pygame.display.flip()

def show_game_over_screen(winner):
    # (This function is unchanged)
    screen.fill(BLACK)
    draw_text(screen, "GAME OVER", 100, WIDTH / 2, HEIGHT / 4)
    draw_text(screen, f"{winner} wins!", 50, WIDTH / 2, HEIGHT / 2)
    draw_text(screen, "Click to Play Again", 30, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()

    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONUP: waiting = False

# --- Game State ---
STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
game_state = STATE_START

# --- Main Game Loop ---
running = True
while running:
    clock.tick(FPS)

    if game_state == STATE_START:
        show_start_screen()
        # --- Reset game objects WITH the selected difficulty ---
        player_score = 0
        opponent_score = 0
        
        player = Player(WIDTH - 20, HEIGHT / 2)
        opponent = Opponent(20, HEIGHT / 2, speed=current_difficulty_settings["opponent_speed"])
        ball = Ball()

        all_sprites = pygame.sprite.Group(player, opponent, ball)
        paddles = pygame.sprite.Group(player, opponent)
        
        game_state = STATE_PLAYING

    elif game_state == STATE_PLAYING:
        # (This part of the loop is unchanged)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        
        player.update()
        opponent.update(ball)
        ball.update()

        if pygame.sprite.spritecollide(ball, paddles, False): ball.bounce()
        if ball.rect.left <= 0: player_score += 1; ball.reset()
        if ball.rect.right >= WIDTH: opponent_score += 1; ball.reset()
        if player_score >= WIN_SCORE or opponent_score >= WIN_SCORE: game_state = STATE_GAMEOVER

        draw_court()
        all_sprites.draw(screen)
        draw_text(screen, str(opponent_score), 50, WIDTH / 4, 10)
        draw_text(screen, str(player_score), 50, WIDTH * 3 / 4, 10)
        pygame.display.flip()

    elif game_state == STATE_GAMEOVER:
        winner = "Player" if player_score > opponent_score else "Opponent"
        show_game_over_screen(winner)
        game_state = STATE_START

pygame.quit()