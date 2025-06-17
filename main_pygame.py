import pygame
import sys
import os
from typing import Tuple, List, Optional

# Importe tes classes existantes depuis le dossier src
from src.game import Game
from src.human_player import HumanPlayer
from src.ai_player import AIPlayer
from src.board import Board
from src.utils import get_coordinates 

# --- Constantes Pygame ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Bataille Navale - Pygame Edition"

# Couleurs (RVB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)
BLUE_WATER = (50, 150, 200) # Un bleu plus vibrant
DEEP_BLUE = (25, 75, 100) # Pour le fond ou les ombres
GREY_BOARD_LINES = (100, 100, 100) # Lignes de grille plus douces
RED_HIT = (255, 50, 50) # Un rouge vif pour les coups
WHITE_MISS = (150, 150, 150) # Un gris clair pour les manqués
GREEN_SHIP = (50, 200, 50) # Un vert vif pour les navires
HOVER_COLOR = (150, 200, 255) # Bleu clair pour le survol
TEXT_COLOR = (240, 240, 240) # Couleur du texte pour les messages

# Dimensions du plateau
BOARD_SIZE = 10 # 10x10
CELL_SIZE = 40 # Taille de chaque cellule en pixels

# Positions des plateaux
HUMAN_BOARD_X = 50
HUMAN_BOARD_Y = 150
AI_BOARD_X = 500 # Espacement pour le plateau de l'IA
AI_BOARD_Y = 150

# Zone des messages
MESSAGE_AREA_X = SCREEN_WIDTH // 2
MESSAGE_AREA_Y = 500

# Police
# Assurez-vous que le fichier 'PressStart2P-Regular.ttf' se trouve bien dans le dossier 'assets/fonts/'
# par rapport à l'emplacement où vous exécutez main_pygame.py.
FONT_PATH = os.path.join('assets', 'fonts', 'PressStart2P-Regular.ttf') 
DEFAULT_FONT_SIZE_SM = 16
DEFAULT_FONT_SIZE_MD = 24
DEFAULT_FONT_SIZE_LG = 36

class GUI:
    def __init__(self, game: Game):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.game = game
        self.clock = pygame.time.Clock()

        self.font_sm = self._load_font(FONT_PATH, DEFAULT_FONT_SIZE_SM)
        self.font_md = self._load_font(FONT_PATH, DEFAULT_FONT_SIZE_MD)
        self.font_lg = self._load_font(FONT_PATH, DEFAULT_FONT_SIZE_LG)

        self.running = True
        self.current_message = "Placez vos navires !"
        self.placement_ship_index = 0
        self.current_ship_orientation = 'H' # H for Horizontal, V for Vertical
        self.hover_coords = None # (row, col) of the cell currently hovered by mouse
        self.last_player_shot_coord = None
        self.last_ai_shot_coord = None
        self.last_ai_shot_result = None

        # Variables pour gérer le délai du tour de l'IA (pour éviter le gel)
        self.ai_turn_start_time = 0 
        self.ai_delay_ms = 1000 # 1 seconde de délai pour l'action de l'IA

    def _load_font(self, path, size):
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Attention: Police personnalisée '{path}' introuvable. Utilisation de la police par défaut.")
            return pygame.font.Font(None, size)

    def _get_grid_coords_from_pixel(self, pixel_x, pixel_y, board_start_x, board_start_y) -> Optional[Tuple[int, int]]:
        """
        Convertit les coordonnées en pixels en coordonnées de grille (row, col).
        Retourne None si hors plateau.
        """
        if not (board_start_x <= pixel_x < board_start_x + self.game.board_size * CELL_SIZE and
                board_start_y <= pixel_y < board_start_y + self.game.board_size * CELL_SIZE):
            return None # Hors des limites du plateau

        col = (pixel_x - board_start_x) // CELL_SIZE
        row = (pixel_y - board_start_y) // CELL_SIZE
        return (row, col)

    def _get_pixel_coords_from_grid(self, grid_coords: Tuple[int, int], board_start_x, board_start_y) -> Tuple[int, int]:
        """
        Convertit les coordonnées de grille (row, col) en coordonnées en pixels (x, y) du coin supérieur gauche.
        """
        r, c = grid_coords
        pixel_x = board_start_x + c * CELL_SIZE
        pixel_y = board_start_y + r * CELL_SIZE
        return (pixel_x, pixel_y)

    def _draw_board(self, surface, board_obj, start_x, start_y, hide_ships=False):
        # Dessine les lignes de la grille et les fonds de cellule
        for r in range(board_obj.size):
            for c in range(board_obj.size):
                pixel_x, pixel_y = self._get_pixel_coords_from_grid((r, c), start_x, start_y)
                
                # Dessine le fond de la cellule
                pygame.draw.rect(surface, BLUE_WATER, (pixel_x, pixel_y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(surface, GREY_BOARD_LINES, (pixel_x, pixel_y, CELL_SIZE, CELL_SIZE), 1) # Bordure

                cell_content = board_obj.grid[r][c]

                # Dessine les navires (pour le propre plateau du joueur humain)
                if not hide_ships and cell_content == 'S':
                    pygame.draw.rect(surface, GREEN_SHIP, (pixel_x + 2, pixel_y + 2, CELL_SIZE - 4, CELL_SIZE - 4))
                
                # Dessine les marqueurs pour les coups et les manqués (sur le plateau cible ou le propre plateau)
                if (r, c) in board_obj.get_all_shot_coords(): # Vérifie si la case a été tirée
                    # Si c'est le propre plateau de l'humain ET la dernière coordonnée tirée par l'IA, la faire clignoter
                    if board_obj is self.game.player_human.own_board and \
                       self.game.last_ai_shot_coord is not None and \
                       (r, c) == self.game.last_ai_shot_coord:
                        
                        result = self.game.last_ai_shot_result
                        current_time = pygame.time.get_ticks()
                        
                        center_x = pixel_x + CELL_SIZE // 2
                        center_y = pixel_y + CELL_SIZE // 2
                        
                        # Effet de clignotement pour le dernier tir de l'IA
                        if (current_time // 250) % 2 == 0: # Clignote toutes les 250ms
                            if result == 'hit' or result == 'sunk':
                                # Dessine un cercle blanc pour touché/coulé pendant le clignotement
                                pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), CELL_SIZE // 2 - 5, 0)
                            else: # Manqué
                                # Dessine un rectangle gris pour manqué pendant le clignotement
                                pygame.draw.rect(surface, (200, 200, 200), pygame.Rect(pixel_x, pixel_y, CELL_SIZE, CELL_SIZE), 3)
                    
                    # Dessine toujours un 'X' pour les coups et un 'O' pour les manqués (statique, sauf si c'est la case clignotante)
                    # Ceci est dessiné *après* l'effet de clignotement pour qu'il apparaisse lorsque ça ne clignote pas, ou comme base.
                    if cell_content == 'X':
                        pygame.draw.line(surface, RED_HIT, (pixel_x + 5, pixel_y + 5), (pixel_x + CELL_SIZE - 5, pixel_y + CELL_SIZE - 5), 3)
                        pygame.draw.line(surface, RED_HIT, (pixel_x + CELL_SIZE - 5, pixel_y + 5), (pixel_x + 5, pixel_y + CELL_SIZE - 5), 3)
                    elif cell_content == 'O':
                        pygame.draw.circle(surface, WHITE_MISS, (pixel_x + CELL_SIZE // 2, pixel_y + CELL_SIZE // 2), CELL_SIZE // 3, 3)

    def _draw_message(self, surface, message, x, y, font, color=TEXT_COLOR):
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)

    def _draw_placement_preview(self):
        if self.game.game_state == "placement" and self.placement_ship_index < len(self.game.player_human.ships_to_place):
            current_ship = self.game.player_human.ships_to_place[self.placement_ship_index]
            
            if self.hover_coords:
                start_r, start_c = self.hover_coords
                potential_coords = []
                
                if self.current_ship_orientation == 'H':
                    for i in range(current_ship.length):
                        if start_c + i < self.game.board_size:
                            potential_coords.append((start_r, start_c + i))
                else: # 'V'
                    for i in range(current_ship.length):
                        if start_r + i < self.game.board_size:
                            potential_coords.append((start_r + i, start_c))

                # Vérifie si le placement est valide (pas de chevauchement, dans les limites) pour la couleur de prévisualisation
                is_valid = True
                for r, c in potential_coords:
                    if not (0 <= r < self.game.board_size and 0 <= c < self.game.board_size) or \
                       self.game.player_human.own_board.grid[r][c] == 'S': # 'S' signifie qu'un navire est déjà là
                        is_valid = False
                        break
                
                preview_color = HOVER_COLOR if is_valid else RED_HIT

                for r, c in potential_coords:
                    if 0 <= r < self.game.board_size and 0 <= c < self.game.board_size:
                        pixel_x, pixel_y = self._get_pixel_coords_from_grid((r, c), HUMAN_BOARD_X, HUMAN_BOARD_Y)
                        pygame.draw.rect(self.screen, preview_color, (pixel_x + 1, pixel_y + 1, CELL_SIZE - 2, CELL_SIZE - 2), 3) # Dessine une bordure épaisse

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Gère les événements de la souris pour le placement et le tir
                if event.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                    # Vérifie si la souris survole le plateau du joueur humain pour le placement des navires
                    self.hover_coords = self._get_grid_coords_from_pixel(mouse_x, mouse_y, HUMAN_BOARD_X, HUMAN_BOARD_Y)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Clic gauche
                    mouse_x, mouse_y = event.pos
                    
                    if self.game.game_state == "placement":
                        clicked_coords = self._get_grid_coords_from_pixel(mouse_x, mouse_y, HUMAN_BOARD_X, HUMAN_BOARD_Y)
                        if clicked_coords:
                            if self.placement_ship_index < len(self.game.player_human.ships_to_place):
                                current_ship = self.game.player_human.ships_to_place[self.placement_ship_index]
                                placed = self.game.player_human.own_board.place_ship(current_ship, clicked_coords, self.current_ship_orientation)
                                if placed:
                                    self.placement_ship_index += 1
                                    self.current_message = f"Navire {current_ship.name} placé. Placez le suivant."
                                    if self.placement_ship_index == len(self.game.player_human.ships_to_place):
                                        self.current_message = "Tous vos navires sont placés ! La partie commence."
                                        self.game.game_state = "player_turn" # Passe à l'état de jeu
                                    else:
                                        next_ship = self.game.player_human.ships_to_place[self.placement_ship_index]
                                        self.current_message = f"Placez votre {next_ship.name} (taille {next_ship.length}). Clic droit pour changer l'orientation."
                                else:
                                    self.current_message = "Placement impossible. Chevauchement ou hors limites. Réessayez."
                            else:
                                self.current_message = "Tous vos navires sont déjà placés."

                    elif self.game.game_state == "player_turn" and self.game.current_player is self.game.player_human:
                        clicked_coords = self._get_grid_coords_from_pixel(mouse_x, mouse_y, AI_BOARD_X, AI_BOARD_Y)
                        if clicked_coords:
                            r, c = clicked_coords
                            # Vérifie si la case a déjà été tirée
                            if self.game.player_human.target_board.grid[r][c] == 'X' or \
                               self.game.player_human.target_board.grid[r][c] == 'O':
                                self.current_message = "Vous avez déjà tiré ici. Choisissez une autre case."
                            else:
                                # Traite le tir
                                shot_result = self.game._process_shot(self.game.player_human, self.game.player_ai, clicked_coords)
                                self.last_player_shot_coord = clicked_coords # Stocke le dernier tir pour d'éventuels effets
                                self.current_message = f"Votre tir en {chr(65+c)}{r+1} : {shot_result.upper()}!"
                                
                                # Vérifie la condition de victoire après le tir du joueur
                                if self.game.player_ai.has_lost():
                                    self.current_message = "FÉLICITATIONS ! Vous avez coulé tous les navires de l'IA ! VOUS GAGNEZ !"
                                    self.game.game_state = "game_over"
                                else:
                                    # Passe au tour de l'IA si le jeu n'est pas terminé
                                    self.game._switch_players()
                                    # Initialise le minuteur pour le tour de l'IA
                                    self.ai_turn_start_time = pygame.time.get_ticks() 
                                    self.current_message = "C'est au tour de l'IA..." # Message avant le délai

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # Clic droit pour l'orientation
                    if self.game.game_state == "placement":
                        self.current_ship_orientation = 'V' if self.current_ship_orientation == 'H' else 'H'
                        self.current_message = f"Orientation du navire: {'Vertical' if self.current_ship_orientation == 'V' else 'Horizontal'}. Clic gauche pour placer."

            # --- Logique de jeu par image ---
            if self.game.game_state == "ai_turn" and self.game.current_player is self.game.player_ai:
                current_time = pygame.time.get_ticks()
                
                # Exécute l'action de l'IA après le délai
                if current_time - self.ai_turn_start_time >= self.ai_delay_ms:
                    ai_shot_coord = self.game.player_ai.get_shot_coordinates()
                    shot_result = self.game._process_shot(self.game.player_ai, self.game.player_human, ai_shot_coord)
                    
                    self.last_ai_shot_coord = ai_shot_coord # Stocke le dernier tir de l'IA
                    self.last_ai_shot_result = shot_result # Stocke le résultat du dernier tir de l'IA
                    
                    r, c = ai_shot_coord
                    self.current_message = f"L'IA a tiré en {chr(65+c)}{r+1} : {shot_result.upper()}!"

                    # Vérifie la condition de victoire après le tir de l'IA
                    if self.game.player_human.has_lost():
                        self.current_message = "Dommage ! L'IA a coulé tous vos navires ! L'IA GAGNE !"
                        self.game.game_state = "game_over"
                    else:
                        self.game._switch_players() # Revient au joueur humain
                        self.current_message = "C'est à votre tour !"
                    self.ai_turn_start_time = 0 # Réinitialise le minuteur de l'IA pour le prochain tour de l'IA

            # --- Dessin ---
            self.screen.fill(DARK_GREY) # Fond sombre

            # Dessiner le plateau du joueur humain
            self._draw_board(self.screen, self.game.player_human.own_board, HUMAN_BOARD_X, HUMAN_BOARD_Y, hide_ships=False)
            # Dessiner le plateau cible du joueur humain
            self._draw_board(self.screen, self.game.player_human.target_board, AI_BOARD_X, AI_BOARD_Y, hide_ships=True)

            self._draw_placement_preview()

            # Dessiner les titres des plateaux
            human_title_surf = self.font_md.render("VOTRE FLOTTE", True, WHITE)
            human_title_rect = human_title_surf.get_rect(midtop=(HUMAN_BOARD_X + (self.game.board_size * CELL_SIZE) // 2, HUMAN_BOARD_Y - 40))
            self.screen.blit(human_title_surf, human_title_rect)

            ai_title_surf = self.font_md.render("FLOTTE ENNEMIE", True, WHITE)
            ai_title_rect = ai_title_surf.get_rect(midtop=(AI_BOARD_X + (self.game.board_size * CELL_SIZE) // 2, AI_BOARD_Y - 40))
            self.screen.blit(ai_title_surf, ai_title_rect)

            # Dessiner les messages
            self._draw_message(self.screen, self.current_message, MESSAGE_AREA_X, MESSAGE_AREA_Y, self.font_md)
            self._draw_message(self.screen, f"Tour: {self.game.current_player.name}", MESSAGE_AREA_X, MESSAGE_AREA_Y + 40, self.font_sm)

            # Instructions spécifiques au placement
            if self.game.game_state == "placement":
                self._draw_message(self.screen, "Clic droit pour changer l'orientation.", MESSAGE_AREA_X, MESSAGE_AREA_Y + 80, self.font_sm, (255, 255, 0)) # Jaune pour plus de visibilité

            pygame.display.flip()
            self.clock.tick(60) # Limite à 60 FPS

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = Game()
    gui = GUI(game)

    # L'IA place ses navires
    print("IA place ses navires...")
    game.player_ai.place_ships()
    print("Tous les navires de IA sont placés. Préparez-vous !")
    
    # Le placement du joueur humain commence via l'interface graphique
    first_ship = gui.game.player_human.ships_to_place[gui.placement_ship_index]
    gui.current_message = f"Placez votre {first_ship.name} (taille {first_ship.length}). Clic droit pour changer l'orientation."
    gui.game.game_state = "placement" # Définit l'état initial du jeu pour l'interface graphique
    
    gui.run()