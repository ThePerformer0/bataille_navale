
class Ship:
    """
    Représente un navire individuel dans la Bataille Navale.

    Attributes:
        name (str): Le nom du navire (ex: "Porte-avions", "Cuirassé").
        length (int): La longueur du navire en nombre de cases.
        hits (list of bool): L'état des parties du navire.
                              True si une partie est touchée, False sinon.
        coordinates (list of tuple): Une liste de (row, col) où le navire est placé sur le plateau.
                                     Initialement vide, remplie lors du placement.
    """

    def __init__(self, name: str, length: int):
        """
        Initialise un nouveau navire.

        Args:
            name (str): Le nom du navire.
            length (int): La longueur du navire.
        """
        self.name = name
        self.length = length
        self.hits = [False] * length  # Toutes les parties du navire sont intactes au début
        self.coordinates = []         # Les coordonnées seront définies lors du placement

    def is_sunk(self) -> bool:
        """
        Vérifie si le navire est coulé.
        Un navire est coulé si toutes ses parties ont été touchées.

        Returns:
            bool: True si le navire est coulé, False sinon.
        """
        return all(self.hits) # 'all()' retourne True si tous les éléments de l'itérable sont True

    def hit_part(self, coordinate: tuple) -> bool:
        """
        Marque une partie du navire comme touchée si la coordonnée correspond à une partie du navire.

        Args:
            coordinate (tuple): La coordonnée (row, col) qui a été touchée.

        Returns:
            bool: True si une partie du navire a été touchée à cette coordonnée, False sinon.
        """
        try:
            # Trouve l'index de la coordonnée dans la liste des coordonnées du navire
            index = self.coordinates.index(coordinate)
            if not self.hits[index]: # Vérifie si la partie n'a pas déjà été touchée
                self.hits[index] = True
                print(f"Bateau {self.name} touché à {chr(65 + coordinate[1])}{coordinate[0] + 1}!")
                return True
            return False # Déjà touché ou ne correspond pas
        except ValueError:
            # La coordonnée ne fait pas partie de ce navire
            return False

    def __repr__(self) -> str:
        """
        Représentation textuelle de l'objet Ship, utile pour le débogage.
        """
        return f"{self.name}(Length: {self.length}, Sunk: {self.is_sunk()}, Hits: {self.hits}, Coords: {self.coordinates})"