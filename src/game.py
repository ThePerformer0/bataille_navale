from .human_player import HumanPlayer
from .ai_player import AIPlayer
from typing import List, Tuple

class Game:
    """
    Orchestre le déroulement du jeu de Bataille Navale.
    Gère les joueurs, les tours, les tirs et les conditions de victoire.
    """
    def __init__(self, board_size: int = 10):
        """
        Initialise une nouvelle partie de Bataille Navale.

        Args:
            board_size (int): La taille des plateaux de jeu (par défaut 10x10).
        """
        self.board_size = board_size
        self.player_human = HumanPlayer("Joueur", board_size)
        self.player_ai = AIPlayer("IA", board_size)
        self.current_player = self.player_human # Le joueur humain commence
        self.opponent_player = self.player_ai

    def _switch_players(self):
        """
        Change le joueur courant pour le joueur suivant.
        """
        self.current_player, self.opponent_player = self.opponent_player, self.current_player
        print(f"\n--- C'est le tour de {self.current_player.name} ---")

    def _process_shot(self, player_shooting, target_player, shot_coord: Tuple[int, int]):
        """
        Traite un tir effectué par un joueur sur un autre.
        Met à jour les plateaux et gère le résultat du tir.

        Args:
            player_shooting (Player): Le joueur qui effectue le tir.
            target_player (Player): Le joueur dont le plateau est ciblé.
            shot_coord (Tuple[int, int]): Les coordonnées du tir.

        Returns:
            str: Le résultat du tir ('miss', 'hit', 'sunk', 'already_hit', 'invalid').
        """
        # Le plateau de l'adversaire reçoit le tir
        result = target_player.own_board.receive_shot(shot_coord)

        # Le tireur met à jour son propre plateau de cible en fonction du résultat
        r, c = shot_coord
        if result == 'hit' or result == 'sunk':
            player_shooting.target_board.grid[r][c] = 'X'
        elif result == 'miss':
            player_shooting.target_board.grid[r][c] = 'O'
        # Si 'already_hit' ou 'invalid', le board n'est pas mis à jour par le tireur (il doit resaisir)
        
        return result

    def start_game(self):
        """
        Démarre la boucle principale du jeu.
        """
        print("Bienvenue à la Bataille Navale !")

        # 1. Placement des navires
        self.player_human.place_ships()
        self.player_ai.place_ships()

        print("\n--- Tous les navires sont placés ! La bataille commence ! ---")
        
        # Boucle de jeu principale
        while not self.player_human.has_lost() and not self.player_ai.has_lost():
            
            self.current_player.display_boards() # Afficher les plateaux du joueur actuel

            shot_coord = None
            result = "invalid" # Initialiser avec une valeur qui garantit une première tentative
            
            # Boucle pour s'assurer d'un tir valide (pas déjà tiré, pas hors limites)
            while result == "invalid" or result == "already_hit":
                try:
                    shot_coord = self.current_player.get_shot_coordinates()
                    result = self._process_shot(self.current_player, self.opponent_player, shot_coord)
                    
                    if result == "invalid":
                        print("Coordonnées de tir invalides ou hors limites. Réessayez.")
                    elif result == "already_hit":
                        print("Vous avez déjà tiré à cet endroit. Réessayez.")
                    
                except Exception as e:
                    print(f"Une erreur est survenue lors de la saisie du tir : {e}. Réessayez.")
                    result = "invalid" # Force la re-saisie

            # Le message de "touché", "coulé", "manqué" est déjà géré par receive_shot/hit_part
            # Ici, on peut ajouter un récapitulatif si on veut
            print(f"Résultat du tir de {self.current_player.name} : {result.upper()} !")


            # Si l'IA a coulé un navire du joueur, le joueur doit le savoir
            if self.current_player is self.player_ai and result == "sunk":
                print(f"L'IA a coulé l'un de VOS navires !")
            
            # Si le joueur humain a coulé un navire de l'IA
            if self.current_player is self.player_human and result == "sunk":
                print(f"BRAVO ! Vous avez coulé un navire de l'IA !")

            # Vérifier si l'adversaire a perdu après le tir
            if self.opponent_player.has_lost():
                print(f"\nFELICITATIONS ! {self.current_player.name} a coulé tous les navires de {self.opponent_player.name} !")
                print(f"{self.current_player.name} GAGNE LA PARTIE !")
                break # Sortir de la boucle de jeu

            self._switch_players() # Passe au joueur suivant

        print("\n--- FIN DE LA PARTIE ---")
        # Afficher les plateaux finaux
        self.player_human.display_boards()
        self.player_ai.own_board.display(hide_ships=False) # Révèle le plateau de l'IA à la fin