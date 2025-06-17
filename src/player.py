from abc import ABC, abstractmethod
from .board import Board
from .ship import Ship
from typing import List, Tuple

class Player(ABC):
    """
    Classe de base abstraite pour un joueur de Bataille Navale.
    Définit l'interface commune pour les joueurs humains et IA.
    """
    def __init__(self, name: str, board_size: int = 10):
        self.name = name
        # Le plateau du joueur où il place ses propres navires
        self.own_board = Board(board_size, f"Flotte de {name}")
        # Le plateau de cible du joueur pour suivre les tirs sur l'adversaire
        self.target_board = Board(board_size, f"Cible de {name}")
        self.ships_to_place: List[Ship] = self._get_default_ships()
        self.sunk_ships_count = 0

    @abstractmethod
    def place_ships(self):
        """
        Méthode abstraite pour le placement des navires.
        Doit être implémentée par les sous-classes (Humain/IA).
        """
        pass

    @abstractmethod
    def get_shot_coordinates(self) -> Tuple[int, int]:
        """
        Méthode abstraite pour obtenir les coordonnées de tir.
        Doit être implémentée par les sous-classes.

        Returns:
            Tuple[int, int]: Les coordonnées (row, col) du tir.
        """
        pass

    def _get_default_ships(self) -> List[Ship]:
        """
        Retourne la liste standard des navires pour le jeu.
        """
        return [
            Ship("Porte-avions", 5),
            Ship("Cuirassé", 4),
            Ship("Croiseur", 3),
            Ship("Sous-marin", 3),
            Ship("Torpilleur", 2)
        ]

    def has_lost(self) -> bool:
        """
        Vérifie si le joueur a perdu (tous ses navires sont coulés).
        """
        # Vérifie si tous les navires sur son propre plateau sont coulés
        return all(ship.is_sunk() for ship in self.own_board.ships)

    def display_boards(self):
        """
        Affiche les deux plateaux du joueur (son propre plateau et son plateau de cible).
        """
        self.own_board.display(hide_ships=False)
        self.target_board.display(hide_ships=True) # Cache les navires de l'adversaire sur sa grille cible