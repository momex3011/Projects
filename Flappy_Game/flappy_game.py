import pygame
import random
import sys

# --- Initialization ---
pygame.init()

# --- Game Constants ---
WIDTH, HEIGHT = 400, 600
FPS = 60

# --- Setup the Display ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# --- Load Assets ---
try:
    # Graphics
    BACKGROUND_IMG = pygame.image.load('assets/sprites/background-day.png').convert()
    BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (WIDTH, HEIGHT))
    
    BASE_IMG = pygame.image.load('assets/sprites/base.png').convert_alpha()
    BASE_IMG = pygame.transform.scale(BASE_IMG, (WIDTH, 100))

    PIPE_IMG = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
    PIPE_IMG = pygame.transform.scale(PIPE_IMG, (80, 400))
    
    # Bird frames for animation
    BIRD_FRAMES = [
        pygame.transform.scale(pygame.image.load('assets/sprites/bird1.png').convert_alpha(), (40, 30)),
        pygame.transform.scale(pygame.image.load('assets/sprites/bird2.png').convert_alpha(), (40, 30)),
        pygame.transform.scale(pygame.image.load('assets/sprites/bird3.png').convert_alpha(), (40, 30)),
    ]

    # Sounds and Music
    FLAP_SOUND = pygame.mixer.Sound('assets/audio/wing.wav')
    SCORE_SOUND = pygame.mixer.Sound('assets/audio/point.wav')
    HIT_SOUND = pygame.mixer.Sound('assets/audio/hit.wav')
    pygame.mixer.music.load('assets/audio/music.mp3')
    pygame.mixer.music.set_volume(0.3) # Lower volume so sounds are clear
    
except FileNotFoundError as e:
    print(f"Error: Asset not found - {e}")
    print("Please ensure the 'assets' folder is in the same directory as the game script.")
    sys.exit()

# --- Font ---
font = pygame.font.Font(None, 50)

# --- Game Classes ---
class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frames = BIRD_FRAMES
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(100, HEIGHT / 2))
        
        self.velocity = 0
        self.gravity = 0.25
        self.flap_strength = -7
        
        self.animation_time = pygame.time.get_ticks()

    def update(self):
        # Physics
        self.velocity += self.gravity
        self.rect.y += self.velocity
        
        # Keep bird on screen (but allow it to die by hitting top/bottom)
        if self.rect.top < 0: self.rect.top = 0
        
        # Animation
        self.animate()
        
        # Rotation
        self.rotate()

    def flap(self):
        self.velocity = self.flap_strength
        FLAP_SOUND.play()

    def animate(self):
        # Cycle through bird frames for flapping animation
        if pygame.time.get_ticks() - self.animation_time > 100:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]
            self.animation_time = pygame.time.get_ticks()

    def rotate(self):
        # Rotate the bird image based on its vertical velocity for a smooth look
        new_image = pygame.transform.rotozoom(self.image, -self.velocity * 3, 1)
        self.image = new_image
        self.rect = self.image.get_rect(center=self.rect.center)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        super().__init__()
        self.image = PIPE_IMG
        if position == 'top':
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect = self.image.get_rect(midbottom=(x, y))
        else: # bottom
            self.rect = self.image.get_rect(midtop=(x, y))
        
        self.passed = False # To track for scoring

    def update(self):
        self.rect.x -= 4
        if self.rect.right < 0:
            self.kill()

# --- Game Functions ---
def create_pipe_pair():
    gap_y = random.randint(200, 400)
    gap_height = 150
    top_pipe = Pipe(WIDTH + 50, gap_y - gap_height // 2, 'top')
    bottom_pipe = Pipe(WIDTH + 50, gap_y + gap_height // 2, 'bottom')
    return top_pipe, bottom_pipe

def draw_floor(floor_x):
    screen.blit(BASE_IMG, (floor_x, HEIGHT - 100))
    screen.blit(BASE_IMG, (floor_x + WIDTH, HEIGHT - 100))

def draw_text(text, x, y):
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def main_game():
    pygame.mixer.music.play(-1) # Loop music indefinitely
    
    bird = Bird()
    all_sprites = pygame.sprite.Group(bird)
    pipes = pygame.sprite.Group()

    floor_x = 0
    score = 0
    
    # Timer for spawning pipes
    SPAWNPIPE = pygame.USEREVENT
    pygame.time.set_timer(SPAWNPIPE, 1200) # Every 1.2 seconds

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
            if event.type == pygame.MOUSEBUTTONDOWN:
                bird.flap()
            if event.type == SPAWNPIPE:
                new_pipes = create_pipe_pair()
                pipes.add(new_pipes)
                all_sprites.add(new_pipes)

        # Update
        all_sprites.update()
        floor_x -= 4
        if floor_x <= -WIDTH:
            floor_x = 0

        # Collision Detection
        if pygame.sprite.spritecollide(bird, pipes, False) or bird.rect.bottom >= HEIGHT - 100:
            HIT_SOUND.play()
            pygame.mixer.music.stop()
            return score # Game Over, return score

        # Scoring
        for pipe in pipes:
            if not pipe.passed and pipe.rect.right < bird.rect.left:
                pipe.passed = True
                # Only score for one of the pipes in the pair
                if pipe.rect.bottom > HEIGHT / 2: 
                    score += 1
                    SCORE_SOUND.play()

        # Draw
        screen.blit(BACKGROUND_IMG, (0, 0))
        all_sprites.draw(screen)
        draw_floor(floor_x)
        draw_text(str(score), WIDTH / 2, 50)
        
        pygame.display.update()

def game_over_screen(score):
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return # Go back to the main game loop

        screen.blit(BACKGROUND_IMG, (0, 0))
        draw_text("Game Over", WIDTH / 2, HEIGHT / 3)
        draw_text(f"Score: {score}", WIDTH / 2, HEIGHT / 2)
        draw_text("Click or Press Space to Play Again", WIDTH / 2, HEIGHT * 2 / 3)
        pygame.display.update()

# --- Main Loop ---
while True:
    score = main_game()
    game_over_screen(score)