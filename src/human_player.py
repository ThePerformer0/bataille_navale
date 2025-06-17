from .player import Player
from .ship import Ship
from .utils import get_coordinates
from typing import Tuple, List

class HumanPlayer(Player):
    """
    Implémentation d'un joueur humain.
    Gère la saisie utilisateur pour le placement des navires et les tirs.
    """
    def __init__(self, name: str, board_size: int = 10):
        super().__init__(name, board_size)

    def place_ships(self):
        """
        Permet au joueur humain de placer ses navires manuellement.
        """
        print(f"\n{self.name}, placez vos navires !")
        self.own_board.display(hide_ships=False)

        for ship in self.ships_to_place:
            placed = False
            while not placed:
                print(f"\nPlacement du {ship.name} (taille: {ship.length}).")
                
                # Obtenir les coordonnées de départ
                start_input = input("Entrez les coordonnées de départ (ex: A1): ").strip()
                start_coord = get_coordinates(start_input, self.own_board.size)

                if start_coord is None:
                    print("Coordonnées invalides. Réessayez.")
                    continue

                # Obtenir l'orientation
                orientation = input("Orientation (H pour Horizontal, V pour Vertical): ").strip().upper()
                if orientation not in ['H', 'V']:
                    print("Orientation invalide. Utilisez 'H' ou 'V'.")
                    continue

                # Tenter de placer le navire
                placed = self.own_board.place_ship(ship, start_coord, orientation)
                if not placed:
                    print("Placement impossible. Le navire chevauche un autre ou sort du plateau. Réessayez.")
                
                self.own_board.display(hide_ships=False) # Afficher après chaque tentative

        print(f"\nTous les navires de {self.name} ont été placés.")


    def get_shot_coordinates(self) -> Tuple[int, int]:
        """
        Demande au joueur humain de saisir les coordonnées de son tir.
        Gère la validation de l'entrée.

        Returns:
            Tuple[int, int]: Les coordonnées (row, col) validées du tir.
        """
        while True:
            shot_input = input(f"\n{self.name}, entrez les coordonnées de votre tir (ex: B5): ").strip()
            shot_coord = get_coordinates(shot_input, self.target_board.size)
            
            if shot_coord is None:
                print("Coordonnées de tir invalides. Réessayez.")
            else:
                # Vérifier si la cible a déjà été tirée
                r, c = shot_coord
                if self.target_board.grid[r][c] == 'X' or self.target_board.grid[r][c] == 'O':
                    print("Vous avez déjà tiré à cet endroit. Choisissez une autre coordonnée.")
                else:
                    return shot_coord