import random
from typing import Tuple, List, Optional
from .player import Player
from .ship import Ship 

class AIPlayer(Player):
    """
    Implémentation d'un joueur IA avec une logique de tir plus avancée (chasse et ciblage).
    """
    def __init__(self, name: str = "IA", board_size: int = 10):
        super().__init__(name, board_size)
        
        self.untried_coordinates: List[Tuple[int, int]] = []
        self._initialize_untried_coordinates()

        self.hits_to_process: List[Tuple[int, int]] = [] 
        self.potential_next_shots: List[Tuple[int, int]] = [] 
        self.sunk_ships_coords: List[Tuple[int, int]] = [] 

        self.current_target_direction: Optional[str] = None
        self.current_hit_series: List[Tuple[int, int]] = []

        # Grille pour suivre les tirs de l'adversaire sur le plateau de l'IA
        self.opponent_shot_tracking_grid: List[List[str]] = [['U' for _ in range(board_size)] for _ in range(board_size)]
        self.opponent_shots_made: List[Tuple[int, int]] = []

        self.endgame_threshold: int = 3 

    def _initialize_untried_coordinates(self):
        """
        Initialise la liste de toutes les coordonnées non encore tirées.
        Utilise une stratégie en damier pour la phase de recherche.
        """
        checkered_coords_even = [] # (r+c) % 2 == 0
        checkered_coords_odd = [] # (r+c) % 2 == 1

        for r in range(self.own_board.size):
            for c in range(self.own_board.size):
                if (r + c) % 2 == 0:
                    checkered_coords_even.append((r, c))
                else:
                    checkered_coords_odd.append((r, c))
        
        # Mélange les deux listes séparément pour introduire un peu d'aléatoire
        # mais toujours favoriser un pattern en damier
        random.shuffle(checkered_coords_even)
        random.shuffle(checkered_coords_odd)

        # L'IA commencera par les cases 'paires' pour une meilleure couverture initiale
        self.untried_coordinates = checkered_coords_even + checkered_coords_odd
        # Si on veut alterner, on peut faire:
        # self.untried_coordinates = [None] * (self.own_board.size * self.own_board.size)
        # i, j = 0, 0
        # for k in range(len(checkered_coords_even)):
        #     self.untried_coordinates[i] = checkered_coords_even[k]
        #     i += 2
        # for k in range(len(checkered_coords_odd)):
        #     self.untried_coordinates[j+1] = checkered_coords_odd[k]
        #     j += 2
        # (Cette alternance n'est pas strictement nécessaire pour la robustesse, le shuffle est suffisant)

    def place_ships(self):
        """
        L'IA place ses navires aléatoirement sur son plateau.
        """
        # Utilise une copie mélangée pour éviter de toujours placer les navires au même endroit
        ships_to_place_shuffled = list(self.ships_to_place)
        random.shuffle(ships_to_place_shuffled)

        for ship in ships_to_place_shuffled:
            placed = False
            while not placed:
                r = random.randint(0, self.own_board.size - 1)
                c = random.randint(0, self.own_board.size - 1)
                orientation = random.choice(['H', 'V'])
                placed = self.own_board.place_ship(ship, (r, c), orientation)
        # print(f"Tous les navires de l'IA sont placés.") # Décommenter pour le debug

    def _get_surrounding_coordinates(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Retourne les coordonnées adjacentes (haut, bas, gauche, droite) d'une cellule."""
        coords = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # Haut, Bas, Gauche, Droite
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                coords.append((nr, nc))
        return coords

    def _determine_and_extend_direction(self):
        """
        Détermine ou confirme la direction d'un navire touché et génère les tirs suivants.
        """
        print("IA: Début _determine_and_extend_direction.")
        if len(self.current_hit_series) < 2:
            # Pas assez de hits pour déterminer une direction claire
            # Ceci est géré par _generate_surrounding_shots si c'est le premier hit.
            return 

        # Triez la série pour garantir que les coordonnées sont dans l'ordre (pour déterminer la direction)
        self.current_hit_series.sort() 
        first_hit = self.current_hit_series[0]
        second_hit = self.current_hit_series[1]

        # Déterminer la direction
        if first_hit[0] == second_hit[0]: # Même ligne -> Horizontal
            self.current_target_direction = 'H'
        elif first_hit[1] == second_hit[1]: # Même colonne -> Vertical
            self.current_target_direction = 'V'
        else:
            # Si les hits ne sont ni sur la même ligne ni sur la même colonne,
            # c'est une situation inattendue pour une ligne droite de navire.
            # Cela pourrait signifier un bug, ou que hits_to_process n'est pas bien géré.
            # On réinitialise la direction et on tente autour du dernier hit.
            self.current_target_direction = None
            self._generate_surrounding_shots(self.current_hit_series[-1])
            return

        # Tenter d'étendre la série dans les deux directions (avant et après)
        self.potential_next_shots = []
        last_hit = self.current_hit_series[-1]
        
        # Extensions dans la direction déterminée
        if self.current_target_direction == 'H':
            # Vers la droite
            next_c_right = last_hit[1] + 1
            if next_c_right < self.board_size and (last_hit[0], next_c_right) in self.untried_coordinates:
                self.potential_next_shots.append((last_hit[0], next_c_right))
            # Vers la gauche (à partir du premier hit de la série)
            next_c_left = self.current_hit_series[0][1] - 1
            if next_c_left >= 0 and (self.current_hit_series[0][0], next_c_left) in self.untried_coordinates:
                self.potential_next_shots.append((self.current_hit_series[0][0], next_c_left))
        elif self.current_target_direction == 'V':
            # Vers le bas
            next_r_down = last_hit[0] + 1
            if next_r_down < self.board_size and (next_r_down, last_hit[1]) in self.untried_coordinates:
                self.potential_next_shots.append((next_r_down, last_hit[1]))
            # Vers le haut (à partir du premier hit de la série)
            next_r_up = self.current_hit_series[0][0] - 1
            if next_r_up >= 0 and (next_r_up, self.current_hit_series[0][1]) in self.untried_coordinates:
                self.potential_next_shots.append((next_r_up, self.current_hit_series[0][1]))

        # Filtrez les tirs déjà faits ou hors limites
        self.potential_next_shots = [
            coord for coord in self.potential_next_shots
            if 0 <= coord[0] < self.board_size and 0 <= coord[1] < self.board_size and \
               self.target_board.grid[coord[0]][coord[1]] == '~' # Assure que ce n'est pas déjà tiré
        ]
        random.shuffle(self.potential_next_shots) # Mélange pour un peu d'aléatoire
        print("IA: Fin _determine_and_extend_direction.")

    def _generate_surrounding_shots(self, hit_coord: Tuple[int, int]):
        """Génère les tirs autour d'une coordonnée touchée (utilisé pour le premier hit d'un navire)."""
        print(f"IA: Début _generate_surrounding_shots pour {hit_coord}.")
        r, c = hit_coord
        potential_coords = self._get_surrounding_coordinates(r, c)
        
        # Filtre et ajoute aux tirs potentiels
        self.potential_next_shots.extend([
            coord for coord in potential_coords 
            if coord in self.untried_coordinates # Doit être une coordonnée non encore essayée
            and self.target_board.grid[coord[0]][coord[1]] == '~' # Ne pas tirer sur des cases déjà connues
        ])
        random.shuffle(self.potential_next_shots)
        print("IA: Fin _generate_surrounding_shots.")


    def get_shot_coordinates(self) -> Tuple[int, int]:
        """
        Détermine les coordonnées du prochain tir de l'IA.
        """
        print("IA: Début de get_shot_coordinates.") # DEBUG POINT 1

        # Stratégie de ciblage (Hunting)
        if self.hits_to_process:
            print(f"IA: En mode ciblage. Hits à traiter: {len(self.hits_to_process)}") # DEBUG POINT 2
            
            self.hits_to_process = list(set(self.hits_to_process))
            self.current_hit_series = list(set(self.current_hit_series))
            
            if not self.potential_next_shots or \
               (len(self.current_hit_series) > 0 and self.current_hit_series[-1] not in self.hits_to_process):
                
                print("IA: Régénération des potential_next_shots.") # DEBUG POINT 3
                if len(self.current_hit_series) == 1:
                    self._generate_surrounding_shots(self.current_hit_series[0])
                    print(f"IA: Généré autour de {self.current_hit_series[0]}. Potential: {self.potential_next_shots}") # DEBUG POINT 4
                elif len(self.current_hit_series) > 1:
                    self._determine_and_extend_direction()
                    print(f"IA: Déterminé et étendu la direction. Potential: {self.potential_next_shots}") # DEBUG POINT 5
                elif self.hits_to_process:
                    self.current_hit_series.append(self.hits_to_process[0])
                    self._generate_surrounding_shots(self.hits_to_process[0])
                    print(f"IA: Commencé nouvelle série depuis hits_to_process. Potential: {self.potential_next_shots}") # DEBUG POINT 6

            # Tenter de trouver un tir valide parmi les potentiels
            while self.potential_next_shots:
                shot = self.potential_next_shots.pop(0)
                r, c = shot
                print(f"IA: Essai de tir potentiel: {shot}. Contenu: {self.target_board.grid[r][c]}") # DEBUG POINT 7
                if 0 <= r < self.board_size and 0 <= c < self.board_size and \
                   self.target_board.grid[r][c] == '~' and \
                   shot in self.untried_coordinates:
                    print(f"IA: Tir ciblé valide trouvé: {shot}") # DEBUG POINT 8
                    return shot
                print(f"IA: Tir potentiel {shot} invalide ou déjà fait.") # DEBUG POINT 9
            
            print("IA: Potential_next_shots épuisés pour la série actuelle. Réinitialisation.") # DEBUG POINT 10
            self.current_hit_series = []
            self.current_target_direction = None
            self.potential_next_shots = []

        # Stratégie de chasse (Searching)
        print("IA: En mode chasse.") # DEBUG POINT 11
        
        self.untried_coordinates = [
            coord for coord in self.untried_coordinates 
            if self.target_board.grid[coord[0]][coord[1]] == '~'
        ]

        if not self.untried_coordinates:
            print("IA: Plus de coordonnées à essayer. Fin de partie?") # DEBUG POINT 12
            return (-1, -1)
        
        checkered_coords = []
        for r, c in self.untried_coordinates:
            if (r + c) % 2 == 0:
                checkered_coords.append((r, c))
        
        if checkered_coords:
            shot = random.choice(checkered_coords)
            print(f"IA: Tir de chasse (damier): {shot}") # DEBUG POINT 13
        else:
            shot = random.choice(self.untried_coordinates)
            print(f"IA: Tir de chasse (aléatoire): {shot}") # DEBUG POINT 14
        
        print("IA: Fin de get_shot_coordinates.") # DEBUG POINT 15
        return shot


    def process_shot_result(self, shot_coord: Tuple[int, int], result: str):
        """
        Met à jour l'état interne de l'IA en fonction du résultat de son tir.
        Ceci est crucial pour que l'IA apprenne et adapte sa stratégie.
        """
        print(f"IA: Début process_shot_result pour {shot_coord}, résultat: {result}.")
        r, c = shot_coord
        
        # Assurez-vous de retirer la coordonnée des tirs non essayés
        if shot_coord in self.untried_coordinates:
            self.untried_coordinates.remove(shot_coord)

        if result == 'hit':
            self.target_board.grid[r][c] = 'X'
            # Ajouter à hits_to_process si ce n'est pas déjà un doublon
            if shot_coord not in self.hits_to_process:
                self.hits_to_process.append(shot_coord)
            # Ajouter à current_hit_series pour la détection de ligne
            if shot_coord not in self.current_hit_series:
                self.current_hit_series.append(shot_coord)
            self.potential_next_shots = [] # Vider, car on va en regénérer des meilleurs

        elif result == 'miss':
            self.target_board.grid[r][c] = 'O'
            # Si on a manqué alors qu'on était en mode ciblage/extension
            # et que potential_next_shots est vide ou que la direction n'est plus viable
            # Il faut peut-être invalider la direction actuelle si le miss brise une série
            if self.current_target_direction:
                # Si le miss est adjacent à la current_hit_series mais ne l'étend pas
                # cela signifie que cette direction est bloquée pour ce navire.
                # On réinitialise la direction et on vide les tirs potentiels.
                # La logique pour revenir aux autres hits_to_process se fera dans get_shot_coordinates
                # lors du prochain appel.
                self.current_target_direction = None
                self.potential_next_shots = []
                # Et on retire le dernier hit de la série si elle ne peut plus être prolongée
                # et qu'il n'y a plus d'autres hits à explorer
                if len(self.current_hit_series) == 1 and self.current_hit_series[0] in self.hits_to_process:
                    self.hits_to_process.remove(self.current_hit_series[0])
                self.current_hit_series = [] # Vider la série actuelle car la direction est brisée

        elif result == 'sunk':
            self.target_board.grid[r][c] = 'X' 
            # Quand un navire est coulé, retirer toutes les coordonnées de hits_to_process
            # qui faisaient partie de la série coulé (current_hit_series)
            for hit in self.current_hit_series:
                if hit in self.hits_to_process:
                    self.hits_to_process.remove(hit)

            self.sunk_ships_coords.extend(self.current_hit_series)
            self.current_hit_series = [] 
            self.current_target_direction = None 
            self.potential_next_shots = [] 
            
        print(f"IA: Fin process_shot_result.") 

    def update_untried_coordinates_after_placement(self):
        """
        Met à jour untried_coordinates pour retirer les cases où l'IA a placé ses propres navires.
        À appeler une fois, après que tous les navires de l'IA aient été placés.
        (Normalement, l'IA ne tire pas sur son propre plateau, mais c'est une bonne pratique).
        """
        # Pour une IA, cette fonction n'est pas strictement nécessaire pour la logique de tir,
        # car elle tire sur le target_board (plateau de l'adversaire), pas sur son own_board.
        # Mais si une IA devait se "souvenir" de son propre placement pour une raison quelconque,
        # ou pour éviter des bugs conceptuels, elle pourrait être utile.
        # Pour le moment, on ne la modifie pas car elle n'est pas appelée dans le flux de jeu actuel.
        pass