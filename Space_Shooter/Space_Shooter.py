import pygame
import random
import math

# --- Constants ---
WIDTH = 800
HEIGHT = 600
FPS = 60

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# --- Initialize Pygame and create window ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()

# --- Load Game Graphics ---
try:
    player_img = pygame.image.load("player.png").convert_alpha()
    enemy_img = pygame.image.load("enemy.png").convert_alpha()
    laser_img = pygame.image.load("laser.png").convert_alpha()
except pygame.error as e:
    print("Error loading one or more images! Make sure asset files are in the same folder.")
    print(e)
    exit()

# --- Game Classes (Player, Enemy, Laser) ---
# These classes remain exactly the same as before.

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(player_img, (50, 40))
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speed_x = 0
        self.shoot_delay = 250
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.speed_x = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT] or keystate[pygame.K_a]:
            self.speed_x = -8
        if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
            self.speed_x = 8
        
        self.rect.x += self.speed_x
        
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            laser = Laser(self.rect.centerx, self.rect.top)
            all_sprites.add(laser)
            lasers.add(laser)

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(enemy_img, (40, 30))
        self.rect = self.image.get_rect()

        # --- New properties for irregular movement ---
        # This is the invisible vertical line the enemy will follow
        self.center_x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speed_y = random.randrange(1, 3) # Make them a bit slower for better effect
        
        # Properties for the wave pattern
        self.angle = 0  # The current point in the sine wave cycle
        self.angle_speed = random.uniform(0.05, 0.1) # How fast it moves side-to-side
        self.amplitude = random.randrange(20, 50) # How far it moves side-to-side

    def update(self):
        # Move down the screen
        self.rect.y += self.speed_y
        
        # Calculate the new side-to-side position using a sine wave
        # math.sin() creates a smooth wave from -1 to 1.
        # We multiply by self.amplitude to control the width of the wave.
        offset = self.amplitude * math.sin(self.angle)
        self.rect.centerx = self.center_x + offset
        
        # Increase the angle to move along the sine wave
        self.angle += self.angle_speed
        
        # Respawn if it goes off screen
        if self.rect.top > HEIGHT + 10:
            # We just need to reset the y position and can keep the other properties
            self.rect.y = random.randrange(-100, -40)
            self.center_x = random.randrange(WIDTH - self.rect.width)

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(laser_img, (10, 25))
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speed_y = -10

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()

# --- UI and Screen Functions ---
font_name = pygame.font.match_font('arial')
def draw_text(surf, text, size, x, y, color=WHITE):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

def show_start_screen():
    screen.fill(GRAY)
    draw_text(screen, "SPACE SHOOTER", 64, WIDTH / 2, HEIGHT / 4)
    draw_text(screen, "Arrow Keys or A/D to Move", 22, WIDTH / 2, HEIGHT / 2)
    draw_text(screen, "Spacebar to Fire", 22, WIDTH / 2, HEIGHT / 2 + 30)
    draw_text(screen, "Press any key to begin", 18, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYUP:
                waiting = False

def show_game_over_screen(score):
    screen.fill(GRAY)
    draw_text(screen, "GAME OVER", 64, WIDTH / 2, HEIGHT / 4)
    draw_text(screen, f"Final Score: {score}", 28, WIDTH / 2, HEIGHT / 2)
    draw_text(screen, "Press 'R' to Restart or 'Q' to Quit", 22, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    waiting = False
                if event.key == pygame.K_r:
                    # To restart, we will exit this loop and let the main loop handle the reset
                    return True # Indicates a restart is requested
    return False # Indicates quit

# --- Game Setup Variables ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
lasers = pygame.sprite.Group()
player = Player()
score = 0

# --- Game State ---
# This is the new, important part!
STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
game_state = STATE_START

# --- Main Game Loop ---
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(FPS)
    
    if game_state == STATE_START:
        show_start_screen()
        # --- Reset the game for a fresh start ---
        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        lasers = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        for i in range(8):
            e = Enemy()
            all_sprites.add(e)
            enemies.add(e)
        score = 0
        game_state = STATE_PLAYING

    elif game_state == STATE_PLAYING:
        # --- Process Input (Events) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()

        # --- Update ---
        all_sprites.update()

        # Check for collisions: laser hitting an enemy
        hits = pygame.sprite.groupcollide(enemies, lasers, True, True)
        for hit in hits:
            score += 10
            e = Enemy()
            all_sprites.add(e)
            enemies.add(e)

        # Check for collisions: enemy hitting the player
        hits = pygame.sprite.spritecollide(player, enemies, False)
        if hits:
            game_state = STATE_GAMEOVER # Change state instead of quitting

        # --- Draw / Render ---
        screen.fill(GRAY)
        all_sprites.draw(screen)
        draw_text(screen, str(score), 18, WIDTH / 2, 10)
        pygame.display.flip()

    elif game_state == STATE_GAMEOVER:
        restart = show_game_over_screen(score)
        if restart:
            game_state = STATE_START # Go back to the start screen
        else:
            running = False # Exit the main loop to quit

pygame.quit()