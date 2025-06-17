import random
from .player import Player
from .ship import Ship
from typing import Tuple, List

class AIPlayer(Player):
    """
    Implémentation d'un joueur IA simple.
    Place les navires aléatoirement et tire aléatoirement.
    """
    def __init__(self, name: str = "IA", board_size: int = 10):
        super().__init__(name, board_size)
        self.possible_shots: List[Tuple[int, int]] = []
        self._initialize_possible_shots()

    def _initialize_possible_shots(self):
        """Initialise la liste de toutes les coordonnées possibles pour les tirs."""
        for r in range(self.own_board.size):
            for c in range(self.own_board.size):
                self.possible_shots.append((r, c))
        random.shuffle(self.possible_shots) # Mélange pour des tirs aléatoires

    def place_ships(self):
        """
        Place les navires de l'IA aléatoirement sur son plateau.
        """
        print(f"\n{self.name} est en train de placer ses navires...")
        for ship in self.ships_to_place:
            placed = False
            while not placed:
                # Coordonnées de départ aléatoires
                start_row = random.randint(0, self.own_board.size - 1)
                start_col = random.randint(0, self.own_board.size - 1)
                start_coord = (start_row, start_col)

                # Orientation aléatoire
                orientation = random.choice(['H', 'V'])

                # Tente de placer le navire
                placed = self.own_board.place_ship(ship, start_coord, orientation)
                # Si le placement échoue, la boucle while continue pour trouver un autre emplacement
        print(f"Tous les navires de {self.name} ont été placés.")


    def get_shot_coordinates(self) -> Tuple[int, int]:
        """
        Génère des coordonnées de tir aléatoires pour l'IA.
        Évite de tirer sur des cases déjà tirées.

        Returns:
            Tuple[int, int]: Les coordonnées (row, col) du tir de l'IA.
        """
        while True:
            # Prend une coordonnée aléatoire de la liste des tirs possibles
            # Si la liste est vide (toutes les cases ont été tirées), cela lèvera une erreur.
            # Dans un vrai jeu, la partie devrait être terminée avant d'arriver là.
            if not self.possible_shots:
                # Ce cas ne devrait normalement pas arriver si le jeu gère bien la fin de partie.
                # Ou si l'IA n'a pas de coups valides restants.
                raise Exception("L'IA n'a plus de coups possibles !")

            shot_coord = self.possible_shots.pop(0) # Prend le premier élément (après mélange)
            r, c = shot_coord

            # Vérifie si la case n'a pas déjà été marquée sur sa grille de cible (par un coup précédent de l'IA)
            # Cette vérification est redondante si possible_shots est bien géré, mais sert de sécurité.
            if self.target_board.grid[r][c] == '~': # S'il n'y a pas d'info, c'est que la case n'a pas été tirée
                print(f"{self.name} tire à {chr(65 + c)}{r + 1}...")
                return shot_coord
            # Si la case était déjà tirée, on continue la boucle pour en trouver une nouvelle.
            # Normalement, avec un `pop(0)` sur une liste mélangée, on ne devrait pas avoir ce problème.