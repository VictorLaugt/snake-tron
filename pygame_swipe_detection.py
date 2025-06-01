import pygame
import sys

pygame.init()

# Config
WIDTH, HEIGHT = 400, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Swipe Detector")
clock = pygame.time.Clock()

# Couleurs
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)

# Police pour afficher le texte
font = pygame.font.SysFont(None, 48)

# Seuil pour détecter un swipe
SWIPE_THRESHOLD = 50

start_pos = None
swipe_direction = ""  # Contiendra la direction du dernier swipe

def detect_swipe(start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    if abs(dx) < SWIPE_THRESHOLD and abs(dy) < SWIPE_THRESHOLD:
        return None

    if abs(dx) > abs(dy):
        return "→ Droite" if dx > 0 else "← Gauche"
    else:
        return "↓ Bas" if dy > 0 else "↑ Haut"

# Boucle principale
running = True
while running:
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            start_pos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP:
            end_pos = pygame.mouse.get_pos()
            if start_pos:
                direction = detect_swipe(start_pos, end_pos)
                if direction:
                    swipe_direction = direction
                start_pos = None

    # Afficher la direction à l'écran
    if swipe_direction:
        text_surface = font.render(swipe_direction, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
