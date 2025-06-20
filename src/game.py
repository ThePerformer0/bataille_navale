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
        """
        # ... (le code existant pour le traitement du tir et mise à jour de target_board) ...
        result = target_player.own_board.receive_shot(shot_coord)

        r, c = shot_coord
        if result == 'hit' or result == 'sunk':
            player_shooting.target_board.grid[r][c] = 'X'
        elif result == 'miss':
            player_shooting.target_board.grid[r][c] = 'O'

        # Informer le joueur adverse du tir qu'il a reçu
        # Il faut que target_player soit une instance de AIPlayer pour cette logique
        if isinstance(target_player, AIPlayer):
            # La méthode `AIPlayer.analyze_opponent_shot` n'existe pas encore, nous allons la créer.
            target_player.process_shot_result(shot_coord, result)

        # NOUVEAU : Informer l'IA de son résultat de tir si c'est elle qui tire
        if isinstance(player_shooting, AIPlayer):
            player_shooting.process_shot_result(shot_coord, result)
            
        return result

    def start_game(self):
        """
        Démarre et gère le déroulement de la partie.
        """
        print("Début de la partie de Bataille Navale !")

        # Placement des navires
        self.player_human.place_ships()
        self.player_ai.place_ships()
        
        # NOUVEAU : Informer l'IA de ses propres placements pour ne pas tirer dessus
        if isinstance(self.player_ai, AIPlayer):
            self.player_ai.update_untried_coordinates_after_placement()


        print("\\nTous les navires sont placés. La partie commence !")
        input("Appuyez sur Entrée pour continuer...")

        # Boucle de jeu principale
        while not self.player_human.has_lost() and not self.player_ai.has_lost():
            
            self.current_player.display_boards() # Afficher les plateaux du joueur actuel

            shot_coord = None
            result = "invalid" 
            
            if isinstance(self.current_player, AIPlayer):
                # Passer les HP restants de l'adversaire (le joueur humain) à l'IA
                opponent_remaining_hp = self.opponent_player.get_remaining_ship_hp()
                shot_coord = self.current_player.get_shot_coordinates(opponent_remaining_hp=opponent_remaining_hp)
            else: # Joueur humain
                shot_coord = self.current_player.get_shot_coordinates()

            # Boucle pour s'assurer d'un tir valide
            while result == "invalid" or result == "already_hit":
                try:
                    # Le tir a déjà été obtenu ci-dessus, on l'utilise directement ici
                    if shot_coord is None: # Si get_shot_coordinates a retourné None (devrait pas arriver avec l'IA)
                         raise ValueError("Coordonnées de tir non obtenues.")

                    result = self._process_shot(self.current_player, self.opponent_player, shot_coord)
                    
                    if result == "invalid":
                        print("Coordonnées de tir invalides ou hors limites. Réessayez.")
                        # Pour l'IA, si elle a tiré invalide, cela ne devrait pas arriver après filtrage.
                        # Pour l'humain, il faut redemander.
                        if not isinstance(self.current_player, AIPlayer):
                            shot_coord = self.current_player.get_shot_coordinates() # Redemander à l'humain
                    elif result == "already_hit":
                        print("Vous avez déjà tiré à cet endroit. Réessayez.")
                        if not isinstance(self.current_player, AIPlayer):
                            shot_coord = self.current_player.get_shot_coordinates() # Redemander à l'humain
                    
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

        # Message final sur le gagnant
        if self.player_human.has_lost():
            print("\nLa partie est terminée. L'IA a gagné !")
        elif self.player_ai.has_lost():
            print("\nLa partie est terminée. Félicitations, vous avez gagné contre l'IA !")
        else:
            print("\nLa partie est terminée.")