from typing import Union

def get_coordinates(input_str: str, board_size: int) -> Union[tuple, None]:
    """
    Convertit une chaîne de caractères de coordonnées (ex: "A1", "J10") en un tuple (row, col).
    Valide également si les coordonnées sont dans les limites du plateau.

    Args:
        input_str (str): La chaîne de caractères représentant les coordonnées.
        board_size (int): La taille du plateau de jeu (ex: 10).

    Returns:
        tuple | None: Un tuple (row, col) si les coordonnées sont valides, sinon None.
    """
    input_str = input_str.upper().strip()

    if not (1 < len(input_str) <= 3): # Ex: A1, B10
        return None

    # Extrait la colonne (lettre) et la ligne (chiffres)
    col_char = input_str[0]
    try:
        row_str = input_str[1:]
        row = int(row_str) - 1 # Convertit la ligne en index 0-basé
    except ValueError:
        return None

    # Convertit la lettre de colonne en index 0-basé (A=0, B=1, ...)
    col = ord(col_char) - ord('A')

    # Vérifie si les coordonnées sont dans les limites du plateau
    if not (0 <= row < board_size and 0 <= col < board_size):
        return None

    return (row, col)

def is_valid_ship_placement(board_grid: list, ship_coords: list, board_size: int) -> bool:
    """
    Vérifie si un placement de navire est valide sur la grille.
    Un placement est valide si:
    1. Toutes les coordonnées sont dans les limites du plateau.
    2. Aucune des coordonnées ne chevauche un navire existant ('S' ou 'X').

    Args:
        board_grid (list): La grille actuelle du plateau.
        ship_coords (list): La liste des tuples (row, col) que le navire occuperait.
        board_size (int): La taille du plateau.

    Returns:
        bool: True si le placement est valide, False sinon.
    """
    for r, c in ship_coords:
        # 1. Vérifier si les coordonnées sont dans les limites du plateau (redondant si get_coordinates est bien utilisé, mais bonne sécurité)
        if not (0 <= r < board_size and 0 <= c < board_size):
            print(f"DEBUG: Coordonnées hors limites: ({r}, {c})") # Pour le débogage
            return False
        # 2. Vérifier si la case est déjà occupée par un navire ('S') ou une partie touchée ('X')
        if board_grid[r][c] == 'S' or board_grid[r][c] == 'X':
            print(f"DEBUG: Chevauchement à ({r}, {c})") # Pour le débogage
            return False
    return True