from typing import Tuple, List, Optional

def get_coordinates(input_str: str, board_size: int) -> Optional[Tuple[int, int]]:
    """
    Convertit une chaîne de caractères (ex: "A1") en coordonnées (row, col).
    """
    if len(input_str) < 2:
        return None

    col_str = input_str[0].upper()
    try:
        col = ord(col_str) - ord('A')
        row = int(input_str[1:]) - 1
    except ValueError:
        return None

    if 0 <= row < board_size and 0 <= col < board_size:
        return (row, col)
    else:
        return None

def is_valid_ship_placement(board, start_coord: Tuple[int, int], ship_length: int, orientation: str) -> List[Tuple[int, int]]:
    """
    Vérifie si un navire peut être placé à partir des coordonnées de départ et de l'orientation.
    Retourne la liste des coordonnées du navire si valide, sinon None.
    Modifié pour prendre le plateau et vérifier les chevauchements.
    """
    r_start, c_start = start_coord
    ship_coords = []

    for i in range(ship_length):
        if orientation == 'H':
            r, c = r_start, c_start + i
        else: # 'V'
            r, c = r_start + i, c_start

        # Vérifier si les coordonnées sont dans les limites du plateau
        if not (0 <= r < board.size and 0 <= c < board.size):
            return None # Hors limites

        # NOUVEAU : Vérifier si la case est déjà occupée par un autre navire ('S' ou 'X' pour touché)
        # Note: Un navire coulé ('X') doit aussi être considéré comme occupé pour un nouveau placement
        if board.grid[r][c] == 'S' or board.grid[r][c] == 'X':
            return None # Case déjà occupée

        ship_coords.append((r, c))

    return ship_coords # Retourne la liste des coordonnées si tout est valide