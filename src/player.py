from abc import ABC, abstractmethod
from typing import List, Tuple
from .board import Board
from .ship import Ship

class Player(ABC):
    """
    Classe abstraite pour les joueurs (humain ou IA) dans le jeu de Bataille Navale.
    """
    def __init__(self, name: str, board_size: int = 10):
        self.name = name
        self.own_board = Board(board_size)
        self.target_board = Board(board_size) # Pour suivre les tirs sur l'adversaire
        
        # Définition des navires par défaut
        self.ships_to_place: List[Ship] = [
            Ship("Porte-avions", 5),
            Ship("Cuirassé", 4),
            Ship("Destroyer", 3),
            Ship("Sous-marin", 3),
            Ship("Patrouilleur", 2),
        ]

    @abstractmethod
    def place_ships(self):
        """Méthode abstraite pour le placement des navires."""
        pass

    @abstractmethod
    def get_shot_coordinates(self) -> Tuple[int, int]:
        """Méthode abstraite pour obtenir les coordonnées de tir."""
        pass

    def has_lost(self) -> bool:
        """
        Vérifie si le joueur a perdu tous ses navires.
        """
        return all(ship.is_sunk() for ship in self.ships_to_place)

    def display_boards(self):
        """
        Affiche les plateaux du joueur (son propre plateau et son plateau de cible).
        """
        print(f"\n--- Plateau de Flotte de {self.name} ---")
        self.own_board.display(hide_ships=False) # Affiche ses propres navires

        print(f"\n--- Plateau de Cible de {self.name} ---")
        self.target_board.display(hide_ships=True) # Cache les navires de l'adversaire

    def get_remaining_ship_hp(self) -> int:
        """
        Calcule le nombre total de parties de navires restantes pour le joueur.
        """
        total_hp = 0
        for ship in self.ships_to_place:
            total_hp += ship.length - len(ship.hits) # length - nombre de hits sur ce navire
        return total_hp