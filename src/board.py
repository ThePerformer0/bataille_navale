from .ship import Ship
from .utils import get_coordinates, is_valid_ship_placement
from typing import Tuple

class Board:
    """
    Représente le plateau de jeu de la Bataille Navale.

    Attributes:
        size (int): La taille du plateau (ex: 10 pour 10x10).
        grid (list of list of str): La grille de jeu. Chaque cellule contient un symbole
                                    représentant son état (vide, navire, touché, manqué).
                                    - '~' : Eau (vide)
                                    - 'S' : Navire (pour l'affichage du joueur, ou masqué pour l'adversaire)
                                    - 'X' : Navire touché
                                    - 'O' : Tir dans l'eau
        name (str): Le nom du propriétaire du plateau (ex: "Joueur", "IA").
    """

    def __init__(self, size=10, name="Board"):
        """
        Initialise un nouveau plateau de jeu vide.

        Args:
            size (int): La taille de la grille (par défaut 10).
            name (str): Le nom de ce plateau.
        """
        self.size = size
        # Initialise la grille avec des tildes '~' pour représenter l'eau
        self.grid = [['~' for _ in range(size)] for _ in range(size)]
        self.ships = []  # Liste des objets Ship sur ce plateau
        self.name = name

    def display(self, hide_ships=False):
        """
        Affiche le plateau de jeu dans la console.

        Args:
            hide_ships (bool): Si True, cache les positions des navires ('S')
                               pour l'affichage du plateau de l'adversaire.
        """
        print(f"\n--- Plateau de {self.name} ---")
        # Affichage des en-têtes de colonnes (A, B, C...)
        print("  " + " ".join([chr(65 + i) for i in range(self.size)]))

        for r in range(self.size):
            # Affichage des numéros de ligne (1, 2, 3...)
            row_display = f"{r + 1:<2}" # <2 pour aligner à gauche sur 2 caractères
            for c in range(self.size):
                cell = self.grid[r][c]
                if hide_ships and cell == 'S':
                    row_display += '~ '  # Cache les navires pour l'adversaire
                else:
                    row_display += f"{cell} "
            print(row_display)
        print("-" * (self.size * 2 + 5)) # Ligne de séparation
        
        
    def place_ship(self, ship: Ship, start_coord: Tuple[int, int], orientation: str) -> bool:
        """
        Tente de placer un navire sur le plateau.
        """
        # Utiliser la fonction utilitaire améliorée pour obtenir et valider les coordonnées
        potential_coords = is_valid_ship_placement(self, start_coord, ship.length, orientation)

        if potential_coords is None:
            return False # Placement invalide (hors limites ou chevauchement)

        # Si valide, placer le navire
        for r, c in potential_coords:
            self.grid[r][c] = 'S' # Marque la case comme occupée par un navire

        ship.coordinates = potential_coords # Associe les coordonnées au navire
        self.ships.append(ship) # Ajoute le navire à la liste des navires sur ce plateau
        return True

    def receive_shot(self, shot_coord: tuple) -> str:
        """
        Gère un tir reçu à une coordonnée donnée.

        Args:
            shot_coord (tuple): Les coordonnées (row, col) du tir.

        Returns:
            str: Le résultat du tir ('miss', 'hit', 'sunk').
        """
        r, c = shot_coord

        # Vérifie si le tir est hors limites (devrait déjà être fait en amont, mais sécurité)
        if not (0 <= r < self.size and 0 <= c < self.size):
            return "invalid" # ou une autre erreur pour le gérer plus haut

        cell_content = self.grid[r][c]

        if cell_content == 'S':
            # C'est un navire, marquer comme touché
            self.grid[r][c] = 'X' # 'X' pour touché
            hit_ship = None
            for ship in self.ships:
                if shot_coord in ship.coordinates:
                    ship.hit_part(shot_coord) # Marque la partie du navire comme touchée
                    hit_ship = ship
                    break
            
            if hit_ship and hit_ship.is_sunk():
                print(f"Vous avez coulé le {hit_ship.name} de {self.name} !")
                return "sunk"
            else:
                return "hit"
        elif cell_content == '~':
            # C'est de l'eau
            self.grid[r][c] = 'O' # 'O' pour manqué
            return "miss"
        elif cell_content == 'X' or cell_content == 'O':
            # Case déjà touchée ou manquée
            return "already_hit" # Ou "invalid" pour signifier un coup redondant
