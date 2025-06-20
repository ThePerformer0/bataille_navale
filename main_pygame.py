import pygame
import sys
import random
import os
from src.ai_player import AIPlayer

# Constantes
GRID_SIZE = 10
CELL_SIZE = 40
MARGIN = 30
GRID_GAP = 80
WINDOW_WIDTH = 2 * (GRID_SIZE * CELL_SIZE) + GRID_GAP + 2 * MARGIN
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + 2 * MARGIN + 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 149, 237)
GRAY = (200, 200, 200)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
NAVY = (0, 70, 140)
YELLOW = (255, 215, 0)

# Navires à placer (nom, taille, couleur)
SHIPS = [
    ("Porte-avions", 5, NAVY),
    ("Cuirassé", 4, BLUE),
    ("Destroyer", 3, GREEN),
    ("Sous-marin", 3, YELLOW),
    ("Patrouilleur", 2, RED),
]

# Initialisation de Pygame
pygame.init()

# Police personnalisée
FONT_PATH = "assets/fonts/Police.ttf"
FONT_SIZE = 28
font = pygame.font.Font(FONT_PATH, FONT_SIZE)
font_small = pygame.font.Font(FONT_PATH, 18)

# Création de la fenêtre
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Bataille Navale - Pygame")

# Fonctions d'affichage
def draw_gradient_background(surface, color_top, color_bottom):
    """Dessine un dégradé vertical du haut vers le bas."""
    for y in range(WINDOW_HEIGHT):
        ratio = y / WINDOW_HEIGHT
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))

def draw_grid(surface, top_left, label):
    x0, y0 = top_left
    # Grille
    for i in range(GRID_SIZE + 1):
        # Lignes horizontales
        pygame.draw.line(surface, BLACK, (x0, y0 + i * CELL_SIZE), (x0 + GRID_SIZE * CELL_SIZE, y0 + i * CELL_SIZE), 2)
        # Lignes verticales
        pygame.draw.line(surface, BLACK, (x0 + i * CELL_SIZE, y0), (x0 + i * CELL_SIZE, y0 + GRID_SIZE * CELL_SIZE), 2)
    # Labels
    for i in range(GRID_SIZE):
        # Lettres colonnes
        letter = chr(65 + i)
        text = font_small.render(letter, True, BLACK)
        surface.blit(text, (x0 + i * CELL_SIZE + CELL_SIZE // 2 - text.get_width() // 2, y0 - 22))
        # Chiffres lignes
        num = str(i + 1)
        text = font_small.render(num, True, BLACK)
        surface.blit(text, (x0 - 22, y0 + i * CELL_SIZE + CELL_SIZE // 2 - text.get_height() // 2))
    # Titre grille
    label_text = font.render(label, True, BLUE)
    surface.blit(label_text, (x0 + GRID_SIZE * CELL_SIZE // 2 - label_text.get_width() // 2, y0 - 50))

def draw_ships(surface, ships, top_left):
    for ship in ships:
        r, c, length, orientation, color = ship
        for i in range(length):
            rr = r + i if orientation == 'V' else r
            cc = c + i if orientation == 'H' else c
            rect = pygame.Rect(
                top_left[0] + cc * CELL_SIZE + 2,
                top_left[1] + rr * CELL_SIZE + 2,
                CELL_SIZE - 4, CELL_SIZE - 4)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 2)

def is_valid_placement(ships, r, c, length, orientation):
    # Vérifie si le navire ne sort pas de la grille et ne chevauche pas un autre navire
    if orientation == 'H':
        if c + length > GRID_SIZE:
            return False
        coords = [(r, c + i) for i in range(length)]
    else:
        if r + length > GRID_SIZE:
            return False
        coords = [(r + i, c) for i in range(length)]
    for ship in ships:
        sr, sc, slen, sorient, _ = ship
        for i in range(slen):
            sr2 = sr + i if sorient == 'V' else sr
            sc2 = sc + i if sorient == 'H' else sc
            if (sr2, sc2) in coords:
                return False
    return True

def draw_shots(surface, shots, top_left):
    for (r, c, result) in shots:
        cx = top_left[0] + c * CELL_SIZE + CELL_SIZE // 2
        cy = top_left[1] + r * CELL_SIZE + CELL_SIZE // 2
        if result == 'miss':
            pygame.draw.circle(surface, BLUE, (cx, cy), CELL_SIZE // 4, 3)
        elif result == 'hit':
            pygame.draw.line(surface, RED, (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
            pygame.draw.line(surface, RED, (cx + 10, cy - 10), (cx - 10, cy + 10), 3)

# Coordonnées des deux grilles
player_grid_pos = (MARGIN, MARGIN + 60)
ai_grid_pos = (MARGIN + GRID_SIZE * CELL_SIZE + GRID_GAP, MARGIN + 60)

# Variables de placement
placed_ships = []  # (row, col, length, orientation, color)
current_ship_idx = 0
current_orientation = 'H'  # 'H' ou 'V'
placing_done = False

# Variables de tir
player_shots = []  # (row, col, 'hit' ou 'miss')
ai_shots = []      # (row, col, 'hit' ou 'miss')
shot_message = ""
shot_message_timer = 0

game_over = False
winner = None  # 'joueur' ou 'ia'

# Initialisation de l'IA avancée
ai_player = AIPlayer(name="IA", board_size=GRID_SIZE)
ai_player.place_ships()  # Placement automatique des navires IA
# On récupère les coordonnées des navires IA pour la détection des tirs
ai_ship_coords = set()
for ship in ai_player.ships_to_place:
    ai_ship_coords.update(ship.coordinates)

# Ajout : fonction pour obtenir toutes les coordonnées occupées par les navires du joueur
def get_player_ship_coords():
    coords = set()
    for r, c, length, orientation, color in placed_ships:
        for i in range(length):
            rr = r + i if orientation == 'V' else r
            cc = c + i if orientation == 'H' else c
            coords.add((rr, cc))
    return coords

# Création d'une grille du joueur pour l'IA (mise à jour après le placement)
def create_player_board():
    board = [['~' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for r, c, length, orientation, color in placed_ships:
        for i in range(length):
            rr = r + i if orientation == 'V' else r
            cc = c + i if orientation == 'H' else c
            board[rr][cc] = 'S'
    return board

# Boucle principale
running = True
while running:
    # Fond dégradé bleu (mer)
    draw_gradient_background(screen, (70, 130, 180), (25, 25, 112))

    screen.fill(WHITE)

    # Afficher les deux grilles
    draw_grid(screen, player_grid_pos, "Votre flotte")
    draw_grid(screen, ai_grid_pos, "Grille de l'IA")

    # Afficher les navires déjà placés
    draw_ships(screen, placed_ships, player_grid_pos)

    # Afficher les tirs du joueur sur la grille de l'IA
    draw_shots(screen, player_shots, ai_grid_pos)
    # Afficher les tirs de l'IA sur la grille du joueur
    draw_shots(screen, ai_shots, player_grid_pos)

    # Placement du navire courant
    if not placing_done and current_ship_idx < len(SHIPS):
        ship_name, ship_len, ship_color = SHIPS[current_ship_idx]
        # Position de la souris sur la grille du joueur
        mx, my = pygame.mouse.get_pos()
        grid_x, grid_y = player_grid_pos
        r = (my - grid_y) // CELL_SIZE
        c = (mx - grid_x) // CELL_SIZE
        # Afficher le navire en surbrillance si la souris est sur la grille
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            valid = is_valid_placement(placed_ships, r, c, ship_len, current_orientation)
            for i in range(ship_len):
                rr = r + i if current_orientation == 'V' else r
                cc = c + i if current_orientation == 'H' else c
                rect = pygame.Rect(
                    grid_x + cc * CELL_SIZE + 2,
                    grid_y + rr * CELL_SIZE + 2,
                    CELL_SIZE - 4, CELL_SIZE - 4)
                color = ship_color if valid else (180, 180, 180)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)
        # Afficher le nom et l'orientation
        info = f"Placer : {ship_name} (taille {ship_len}) - Orientation : {'Horizontale' if current_orientation == 'H' else 'Verticale'}"
        info_text = font_small.render(info, True, BLACK)
        screen.blit(info_text, (MARGIN, WINDOW_HEIGHT - 40))
    elif not placing_done:
        placing_done = True

    # Message de fin de placement
    if placing_done:
        done_text = font.render("Tous les navires sont placés !", True, GREEN)
        screen.blit(done_text, (WINDOW_WIDTH // 2 - done_text.get_width() // 2, WINDOW_HEIGHT - 50))
        # Afficher le message de tir si besoin
        if shot_message:
            msg = font_small.render(shot_message, True, BLACK)
            screen.blit(msg, (ai_grid_pos[0], ai_grid_pos[1] + GRID_SIZE * CELL_SIZE + 10))
        # Afficher le message de victoire
        if game_over:
            if winner == 'joueur':
                end_text = font.render("Félicitations, vous avez gagné !", True, GREEN)
            else:
                end_text = font.render("L'IA a gagné...", True, RED)
            screen.blit(end_text, (WINDOW_WIDTH // 2 - end_text.get_width() // 2, WINDOW_HEIGHT // 2 - end_text.get_height() // 2))

    # Titre principal
    title = font.render("Bataille Navale", True, BLACK)
    screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 10))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not placing_done and current_ship_idx < len(SHIPS):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_orientation = 'V' if current_orientation == 'H' else 'H'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                grid_x, grid_y = player_grid_pos
                r = (my - grid_y) // CELL_SIZE
                c = (mx - grid_x) // CELL_SIZE
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    if is_valid_placement(placed_ships, r, c, SHIPS[current_ship_idx][1], current_orientation):
                        placed_ships.append((r, c, SHIPS[current_ship_idx][1], current_orientation, SHIPS[current_ship_idx][2]))
                        current_ship_idx += 1
                        current_orientation = 'H'  # Reset orientation par défaut
        elif placing_done and not game_over:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                grid_x, grid_y = ai_grid_pos
                r = (my - grid_y) // CELL_SIZE
                c = (mx - grid_x) // CELL_SIZE
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    if not any((r, c) == (rr, cc) for (rr, cc, _) in player_shots):
                        if (r, c) in ai_ship_coords:
                            player_shots.append((r, c, 'hit'))
                            shot_message = f"Touché en {chr(65 + c)}{r + 1} !"
                        else:
                            player_shots.append((r, c, 'miss'))
                            shot_message = f"Manqué en {chr(65 + c)}{r + 1}."
                        shot_message_timer = pygame.time.get_ticks()
                        # Vérifier si le joueur a gagné
                        if all((coord in [(rr, cc) for (rr, cc, res) in player_shots if res == 'hit']) for coord in ai_ship_coords):
                            game_over = True
                            winner = 'joueur'
                        else:
                            # Riposte IA intelligente
                            # Mettre à jour la grille du joueur pour l'IA
                            player_board = create_player_board()
                            # L'IA choisit où tirer
                            ia_shot = ai_player.get_shot_coordinates()
                            ia_r, ia_c = ia_shot
                            # Déterminer le résultat du tir de l'IA
                            if player_board[ia_r][ia_c] == 'S':
                                ai_shots.append((ia_r, ia_c, 'hit'))
                                shot_message = f"L'IA a touché votre navire en {chr(65 + ia_c)}{ia_r + 1} !"
                                result = 'hit'
                                player_board[ia_r][ia_c] = 'X'
                            else:
                                ai_shots.append((ia_r, ia_c, 'miss'))
                                shot_message = f"L'IA a tiré en {chr(65 + ia_c)}{ia_r + 1} et a manqué."
                                result = 'miss'
                                player_board[ia_r][ia_c] = 'O'
                            shot_message_timer = pygame.time.get_ticks()
                            # L'IA apprend du résultat
                            ai_player.process_shot_result(ia_shot, result)
                            # Vérifier si l'IA a gagné
                            player_coords = get_player_ship_coords()
                            if all((coord in [(rr, cc) for (rr, cc, res) in ai_shots if res == 'hit']) for coord in player_coords):
                                game_over = True
                                winner = 'ia'
    # Effacer le message après 1,5s
    if shot_message and pygame.time.get_ticks() - shot_message_timer > 1500:
        shot_message = ""

pygame.quit()
sys.exit() 
