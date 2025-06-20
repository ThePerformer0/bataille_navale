# main_pygame.py

import pygame
import sys
import os
from typing import Tuple, List, Optional

# Importe tes classes existantes
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
TEXT_COLOR = (240, 240, 240) # Presque blanc pour le texte

# Taille des cellules
CELL_SIZE = 30 # Taille d'une cellule en pixels

# Positions des plateaux
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 100

HUMAN_BOARD_X = BOARD_OFFSET_X
HUMAN_BOARD_Y = BOARD_OFFSET_Y

AI_BOARD_X = SCREEN_WIDTH - (BOARD_OFFSET_X + 10 * CELL_SIZE) # 10 est la taille du board
AI_BOARD_Y = BOARD_OFFSET_Y

# Zone de messages
MESSAGE_AREA_X = SCREEN_WIDTH // 2
MESSAGE_AREA_Y = 50 # Au-dessus des plateaux

# Police
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Police.ttf')


class GUI:
    def __init__(self, game: Game):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        self.game = game

        try:
            self.font_lg = pygame.font.Font(FONT_PATH, 36)
            self.font_md = pygame.font.Font(FONT_PATH, 24)
            self.font_sm = pygame.font.Font(FONT_PATH, 18)
        except FileNotFoundError:
            print(f"Erreur: Le fichier de police '{FONT_PATH}' n'a pas été trouvé.")
            print("Veuillez vous assurer que le chemin est correct ou utilisez une police système.")
            self.font_lg = pygame.font.SysFont(None, 36)
            self.font_md = pygame.font.SysFont(None, 24)
            self.font_sm = pygame.font.SysFont(None, 18)
        
        self.current_message = ""
        self.current_ship_index = 0 # Pour suivre le placement des navires du joueur
        self.placement_orientation = 'H' # 'H' pour Horizontal, 'V' pour Vertical
        self.hover_coords = None # Coordonnées de la cellule survolée par la souris

        # Coordonnées du dernier tir de l'IA pour l'affichage
        self.last_ai_shot = None

    def _get_grid_coords(self, mouse_pos: Tuple[int, int], board_x: int, board_y: int) -> Optional[Tuple[int, int]]:
        """Convertit les coordonnées de la souris en coordonnées de grille (row, col) pour un plateau donné."""
        mouse_x, mouse_y = mouse_pos
        
        # Vérifier si la souris est sur le plateau
        if board_x <= mouse_x < board_x + self.game.board_size * CELL_SIZE and \
           board_y <= mouse_y < board_y + self.game.board_size * CELL_SIZE:
            
            col = (mouse_x - board_x) // CELL_SIZE
            row = (mouse_y - board_y) // CELL_SIZE
            return (row, col)
        return None

    def _draw_board(self, surface: pygame.Surface, board_obj: Board, start_x: int, start_y: int, hide_ships: bool = False):
        """Dessine un plateau de jeu."""
        # Dessiner la grille
        for r in range(board_obj.size):
            for c in range(board_obj.size):
                rect = pygame.Rect(start_x + c * CELL_SIZE, start_y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                cell_content = board_obj.grid[r][c]
                color = BLUE_WATER

                if cell_content == 'X':
                    color = RED_HIT # Navire touché
                elif cell_content == 'O':
                    color = WHITE_MISS # Tir manqué
                elif cell_content == 'S' and not hide_ships:
                    color = GREEN_SHIP # Navire (visible pour le propriétaire)

                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, GREY_BOARD_LINES, rect, 1) # Bordure de la cellule

                # Dessiner les coordonnées pour l'aide visuelle (lettres et chiffres)
                if c == 0:
                    row_label = self.font_sm.render(str(r + 1), True, TEXT_COLOR)
                    surface.blit(row_label, (start_x - 25, start_y + r * CELL_SIZE + CELL_SIZE // 4))
                if r == 0:
                    col_label = self.font_sm.render(chr(65 + c), True, TEXT_COLOR)
                    surface.blit(col_label, (start_x + c * CELL_SIZE + CELL_SIZE // 4, start_y - 25))

        # Dessiner les navires en cours de placement (si c'est le tour humain et en phase de placement)
        if self.game.game_state == "placement" and self.game.current_player is self.game.player_human and not hide_ships:
            self._draw_placement_preview()


    def _draw_placement_preview(self):
        """Dessine l'aperçu du navire en cours de placement."""
        if self.game.game_state != "placement" or self.game.current_player is not self.game.player_human:
            return

        current_ship = self.game.player_human.ships_to_place[self.current_ship_index]
        
        if self.hover_coords:
            hover_r, hover_c = self.hover_coords
            start_x = HUMAN_BOARD_X + hover_c * CELL_SIZE
            start_y = HUMAN_BOARD_Y + hover_r * CELL_SIZE

            temp_coords = []
            if self.placement_orientation == 'H':
                for i in range(current_ship.length):
                    if hover_c + i < self.game.board_size:
                        temp_coords.append((hover_r, hover_c + i))
            else: # 'V'
                for i in range(current_ship.length):
                    if hover_r + i < self.game.board_size:
                        temp_coords.append((hover_r + i, hover_c))
            
            # Vérifier si le placement temporaire est valide pour changer la couleur de l'aperçu
            is_valid = self.game.player_human.own_board.is_valid_placement_preview(
                current_ship, (hover_r, hover_c), self.placement_orientation
            )
            preview_color = GREEN_SHIP if is_valid else RED_HIT

            for r, c in temp_coords:
                if 0 <= r < self.game.board_size and 0 <= c < self.game.board_size:
                    rect = pygame.Rect(HUMAN_BOARD_X + c * CELL_SIZE, HUMAN_BOARD_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, preview_color, rect, 3) # Dessiner un cadre plus épais

    def _draw_message(self, surface: pygame.Surface, message: str, x: int, y: int, font: pygame.font.Font, color: Tuple[int, int, int] = TEXT_COLOR):
        """Dessine un message centré sur l'écran."""
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)

    def _handle_placement_events(self, event: pygame.event.Event):
        """Gère les événements pendant la phase de placement des navires."""
        if event.type == pygame.MOUSEMOTION:
            self.hover_coords = self._get_grid_coords(event.pos, HUMAN_BOARD_X, HUMAN_BOARD_Y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clic gauche
                if self.hover_coords and self.current_ship_index < len(self.game.player_human.ships_to_place):
                    current_ship = self.game.player_human.ships_to_place[self.current_ship_index]
                    
                    placed = self.game.player_human.own_board.place_ship(
                        current_ship, self.hover_coords, self.placement_orientation
                    )

                    if placed:
                        self.current_ship_index += 1
                        if self.current_ship_index < len(self.game.player_human.ships_to_place):
                            next_ship_name = self.game.player_human.ships_to_place[self.current_ship_index].name
                            self.current_message = f"{self.game.player_human.name}, placez votre {next_ship_name}."
                        else:
                            self.current_message = "Tous vos navires sont placés. Cliquez n'importe où pour commencer la partie !"
                            self.game.game_state = "pre_playing" # Nouvelle phase intermédiaire
                    else:
                        self.current_message = "Placement impossible. Chevauchement ou hors limite. Réessayez."
                elif self.game.game_state == "pre_playing":
                    self.game.game_state = "playing"
                    self.current_message = "La partie commence ! C'est votre tour."
                    # Assurez-vous que le joueur humain est bien le joueur actuel au début du jeu
                    self.game.current_player = self.game.player_human
                    self.game.opponent_player = self.game.player_ai

            elif event.button == 3: # Clic droit
                self.placement_orientation = 'V' if self.placement_orientation == 'H' else 'H'
                self.current_message = f"Orientation : {'Horizontale' if self.placement_orientation == 'H' else 'Verticale'}"

    def _handle_playing_events(self, event: pygame.event.Event):
        """Gère les événements pendant la phase de jeu (tirs)."""
        if event.type == pygame.MOUSEMOTION:
            self.hover_coords = self._get_grid_coords(event.pos, AI_BOARD_X, AI_BOARD_Y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clic gauche
                if self.hover_coords:
                    r, c = self.hover_coords
                    # Vérifier si la case a déjà été tirée
                    if self.game.player_human.target_board.grid[r][c] == '~': # Si c'est de l'eau non tirée
                        shot_result = self.game._process_shot(self.game.player_human, self.game.player_ai, self.hover_coords)
                        
                        # Mettre à jour le message en fonction du résultat du tir
                        if shot_result == "hit":
                            self.current_message = f"Vous avez TOUCHÉ un navire ennemi en {chr(65 + c)}{r + 1}!"
                        elif shot_result == "sunk":
                            self.current_message = f"Vous avez COULÉ un navire ennemi en {chr(65 + c)}{r + 1}!"
                        elif shot_result == "miss":
                            self.current_message = f"Vous avez MANQUÉ en {chr(65 + c)}{r + 1}."
                        
                        # Le changement de tour se fait dans _process_shot
                    else:
                        self.current_message = "Vous avez déjà tiré à cet endroit ! Choisissez une autre case."
                else:
                    self.current_message = "Cliquez sur la grille ennemie pour tirer !"
    
    def _draw_background_pattern(self):
        """
        Dessine un motif d'arrière-plan simple ou une couleur unie.
        """
        self.screen.fill(DEEP_BLUE)

    def run(self):
        running = True
        while running:
            # Gérer les événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    if self.game.game_state == "placement":
                        self._handle_placement_click(mouse_x, mouse_y, event.button)
                    elif self.game.game_state == "playing" and self.game.current_player is self.game.player_human:
                        # Clic du joueur humain pour tirer
                        if event.button == 1: # Clic gauche
                            # Vérifie si le clic est sur le plateau de l'IA (le plateau cible de l'humain)
                            cell_clicked = self._get_cell_from_mouse(mouse_x, mouse_y, AI_BOARD_X, AI_BOARD_Y)
                            if cell_clicked:
                                row, col = cell_clicked
                                shot_coord = (row, col)
                                # Traiter le tir de l'humain
                                result = self.game.player_human.shoot(self.game.player_ai, shot_coord)
                                if result == "invalid":
                                    self.current_message = "Cible déjà touchée ou hors limites. Réessayez."
                                else:
                                    self.current_message = f"Joueur a tiré en {chr(65 + col)}{row + 1}. Résultat: {result.upper()}!"
                                    # Le tour change dans game.py après _process_shot
                                    # Ici, nous devons passer le tour explicitement si le tir est valide
                                    if result in ["hit", "miss", "sunk"]:
                                        # Passer au tour de l'IA immédiatement après le tir valide du joueur
                                        self.game._switch_players() 
                                        print("GUI: Tir humain traité. C'est au tour de l'IA.")

                    # else: # Si le clic n'est pas géré par un état spécifique, ne rien faire
                    #     print(f"Clic ignoré en état {self.game.game_state} ou joueur non humain.")


            # Logique de jeu basée sur l'état
            if self.game.game_state == "placement":
                # Le joueur place ses navires
                # La logique est gérée par _handle_placement_click et met à jour current_placing_ship_index
                pass # Rien à faire ici dans la boucle principale, tout est par événement

            elif self.game.game_state == "playing":
                if self.game.current_player is self.game.player_ai:
                    # C'est le tour de l'IA
                    print("GUI: C'est le tour de l'IA. L'IA va tirer.")
                    self.current_message = "L'IA réfléchit à son prochain tir..."
                    pygame.display.flip() # Mettre à jour l'affichage pour montrer le message

                    pygame.time.wait(1000) # Petite pause pour voir le message

                    shot_coord_ai = self.game.player_ai.get_shot_coordinates()
                    print(f"IA tire en {chr(65 + shot_coord_ai[1])}{shot_coord_ai[0] + 1}")
                    result_ai = self.game.player_ai.shoot(self.game.player_human, shot_coord_ai)
                    self.current_message = f"L'IA a tiré en {chr(65 + shot_coord_ai[1])}{shot_coord_ai[0] + 1}. Résultat: {result_ai.upper()}!"
                    print(f"GUI: IA a tiré. Résultat: {result_ai}")

                    # L'IA a tiré, on passe au joueur suivant (l'humain)
                    self.game._switch_players()
                    print("GUI: Tir IA traité. C'est au tour de l'humain.")
                    pygame.time.wait(500) # Petite pause après le tir de l'IA
                    self.current_message = "C'est le tour de l'humain. Attente d'un clic." # Réinitialise le message pour l'humain


                elif self.game.current_player is self.game.player_human:
                    # C'est le tour de l'humain, on attend un clic (géré par l'événement MOUSEBUTTONDOWN)
                    print("GUI: C'est le tour de l'humain. Attente d'un clic.")
                    # Le message est déjà défini si un tir précédent a eu lieu, ou par défaut
                    if not self.current_message.startswith("Joueur a tiré"): # Évite de remplacer le message de résultat du tir
                        self.current_message = "C'est votre tour ! Cliquez sur le plateau ennemi pour tirer."

            # Vérifier la condition de fin de jeu
            if self.game.player_human.has_lost():
                self.current_message = "GAME OVER ! L'IA a coulé tous vos navires !"
                self.game.game_state = "game_over"
                running = False # Arrête la boucle du jeu après le message
                print("GUI: L'humain a perdu. Fin de partie.")
            elif self.game.player_ai.has_lost():
                self.current_message = "FELICITATIONS ! Vous avez coulé tous les navires de l'IA !"
                self.game.game_state = "game_over"
                running = False # Arrête la boucle du jeu après le message
                print("GUI: L'IA a perdu. Fin de partie.")


            # Dessiner tout
            self.screen.fill(DEEP_BLUE) # Fond de l'écran
            self._draw_background_pattern()

            # Dessiner le plateau du joueur humain
            self._draw_board(self.screen, self.game.player_human.own_board, HUMAN_BOARD_X, HUMAN_BOARD_Y, hide_ships=False)
            # Dessiner le plateau cible du joueur humain
            self._draw_board(self.screen, self.game.player_human.target_board, AI_BOARD_X, AI_BOARD_Y, hide_ships=True)

            if self.game.game_state == "placement":
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

        # Si le jeu est terminé, rester affiché un court instant avant de quitter
        if self.game.game_state == "game_over":
            pygame.time.wait(3000) # Attendre 3 secondes avant de quitter

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
    first_ship = gui.game.player_human.ships_to_place[0] if gui.game.player_human.ships_to_place else None
    if first_ship:
        gui.current_placing_ship = first_ship
        gui.current_message = f"Placez votre {first_ship.name} (taille: {first_ship.length})."
        gui.game.game_state = "placement"
    else:
        # Si pour une raison quelconque il n'y a pas de navires, passer directement en jeu
        gui.game.game_state = "playing"
        gui.current_message = "Tous les navires sont placés. Cliquez pour commencer le jeu."


    gui.run() # La boucle de jeu commence ici