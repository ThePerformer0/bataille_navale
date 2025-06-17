from .ship import Ship
from .utils import get_coordinates, is_valid_ship_placement
from typing import List, Tuple

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

    def display(self, hide_ships: bool = True):
        """
        Affiche le plateau de jeu dans la console.

        Args:
            hide_ships (bool): Si True, cache la position des navires non touchés ('S').
        """
        # Afficher les en-têtes de colonnes (A, B, C...)
        print("  " + " ".join([chr(65 + i) for i in range(self.size)]))
        for r in range(self.size):
            # Afficher le numéro de ligne (1, 2, 3...)
            row_display = [str(r + 1).ljust(2)] # Ajuste pour l'alignement
            for c in range(self.size):
                cell = self.grid[r][c]
                if hide_ships and cell == 'S':
                    row_display.append('~') # Cache les navires non touchés
                else:
                    row_display.append(cell)
            print(" ".join(row_display))

    def place_ship(self, ship, start_coord: Tuple[int, int], orientation: str) -> bool:
        """
        Tente de placer un navire sur le plateau.

        Args:
            ship (Ship): L'objet Ship à placer.
            start_coord (tuple): Les coordonnées (row, col) de la première case du navire.
            orientation (str): 'H' pour horizontal, 'V' pour vertical.

        Returns:
            bool: True si le navire a été placé avec succès, False sinon.
        """
        potential_coords = is_valid_ship_placement(self, start_coord, ship.length, orientation)

        if potential_coords is None:
            return False # Placement invalide (hors limites ou chevauchement)

        # Si le placement est valide, mettre à jour la grille et le navire
        for r, c in potential_coords:
            self.grid[r][c] = 'S'
        
        ship.coordinates = potential_coords # Associe les coordonnées au navire
        self.ships.append(ship) # Ajoute le navire à la liste des navires du plateau
        return True

    def receive_shot(self, shot_coord: Tuple[int, int]) -> str:
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
                # print(f"Vous avez coulé le {hit_ship.name} de {self.name} !") # Laisser la GUI gérer ça
                return "sunk"
            else:
                return "hit"
        elif cell_content == '~':
            # C'est de l'eau
            self.grid[r][c] = 'O' # 'O' pour manqué
            return "miss"
        else:
            # Déjà tiré ici ('X' ou 'O')
            return "already_hit"

    def get_all_shot_coords(self) -> List[Tuple[int, int]]:
        """
        Retourne une liste de toutes les coordonnées qui ont été ciblées sur ce plateau
        (qu'il y ait eu un coup ('X') ou un manqué ('O')).
        """
        shot_coords = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 'X' or self.grid[r][c] == 'O':
                    shot_coords.append((r, c))
        return shot_coords