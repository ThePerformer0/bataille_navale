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
        
        # Statistiques pour l'adaptation dynamique
        self.shots_fired: int = 0
        self.hits_achieved: int = 0
        self.ships_sunk: int = 0
        self.consecutive_misses: int = 0
        self.last_shot_result: Optional[str] = None
        
        # Paramètres adaptatifs
        self.aggression_level: float = 1.0  # 0.5 = conservateur, 2.0 = agressif
        self.parity_preference: float = 1.0  # Préférence pour la stratégie de parité

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
        L'IA place ses navires de manière stratégique pour maximiser ses chances de survie.
        """
        # Utilise une copie mélangée pour éviter de toujours placer les navires au même endroit
        ships_to_place_shuffled = list(self.ships_to_place)
        random.shuffle(ships_to_place_shuffled)

        # Stratégie de placement : éviter les patterns prévisibles
        # 1. Placer les gros navires en premier (plus difficiles à placer)
        # 2. Éviter les coins et les bords (souvent ciblés en premier)
        # 3. Créer des "zones mortes" pour tromper l'adversaire
        
        for ship in ships_to_place_shuffled:
            placed = False
            attempts = 0
            max_attempts = 1000  # Éviter les boucles infinies
            
            while not placed and attempts < max_attempts:
                attempts += 1
                
                # Stratégie de placement intelligente
                if ship.length >= 4:  # Gros navires
                    # Éviter les bords pour les gros navires
                    r = random.randint(2, self.own_board.size - 3)
                    c = random.randint(2, self.own_board.size - 3)
                else:  # Petits navires
                    # Plus de liberté pour les petits navires
                    r = random.randint(0, self.own_board.size - 1)
                    c = random.randint(0, self.own_board.size - 1)
                
                orientation = random.choice(['H', 'V'])
                
                # Vérifier si le placement est valide
                placed = self.own_board.place_ship(ship, (r, c), orientation)
                
                # Si pas placé après beaucoup d'essais, relâcher les contraintes
                if not placed and attempts > 500:
                    r = random.randint(0, self.own_board.size - 1)
                    c = random.randint(0, self.own_board.size - 1)
                    orientation = random.choice(['H', 'V'])
                    placed = self.own_board.place_ship(ship, (r, c), orientation)
        
        if attempts >= max_attempts:
            print(f"ATTENTION: Impossible de placer tous les navires de {self.name} !")
        
        print(f"Tous les navires de {self.name} sont placés. Préparez-vous !")
        # Note : Je n'affiche pas mon propre plateau, c'est un secret !

    def _get_occupied_own_coordinates(self) -> List[Tuple[int, int]]:
        """
        Je récupère la liste de toutes les coordonnées où se trouvent MES PROPRES navires.
        C'est pour être sûr de ne JAMAIS tirer sur moi-même. Ce serait bête, non ?
        """
        occupied_coords = []
        for ship in self.ships_to_place:
            occupied_coords.extend(ship.coordinates)
        return occupied_coords

    def update_untried_coordinates_after_placement(self):
        """
        Une fois que j'ai placé tous mes navires, je nettoie ma liste de cibles potentielles.
        Je retire toutes les cases où se trouvent MES PROPRES navires.
        Je ne vais quand même pas me saboter !
        """
        own_ship_coords = self._get_occupied_own_coordinates()
        self.untried_coordinates = [
            coord for coord in self.untried_coordinates 
            if coord not in own_ship_coords
        ]
        # Je mélange à nouveau, juste pour le plaisir.
        random.shuffle(self.untried_coordinates)

    def analyze_opponent_shot(self, shot_coord: Tuple[int, int], result: str):
        """
        Ah, l'adversaire a tiré ! Laissez-moi noter ça sur ma carte secrète.
        C'est super important pour ma stratégie future, croyez-moi !
        """
        r, c = shot_coord
        self.opponent_shots_made.append(shot_coord) # Je garde une trace de TOUS vos tirs

        # Et je mets à jour ma grille de suivi : X si touché, O si raté.
        if result == 'hit' or result == 'sunk':
            self.opponent_shot_tracking_grid[r][c] = 'X'
        elif result == 'miss':
            self.opponent_shot_tracking_grid[r][c] = 'O'
        # Si vous n'avez pas tiré dans une zone, elle reste 'U' (Untouched).
        # Et ça, c'est une information précieuse pour moi...

    def get_shot_coordinates(self, opponent_remaining_hp: Optional[int] = None) -> Tuple[int, int]:
        """
        C'est l'heure de mon coup ! Je vais décider où tirer.
        Ma logique est en plusieurs étapes, par ordre de priorité :

        1.  Je finis le navire que j'ai déjà bien entamé (mode "ciblage actif").
        2.  Si la partie est presque finie (vous avez peu de points de vie),
            je reviens sur n'importe quel autre navire que j'ai touché par le passé,
            pour l'achever (mode "fin de jeu").
        3.  Sinon, je pars à la "chasse" : je cherche de nouveaux navires,
            en privilégiant les zones où VOUS n'avez pas tiré (mode "chasse intelligente").
        """
        # Obtenir les coordonnées de mes propres navires pour éviter de me tirer dessus
        own_ship_coords = self._get_occupied_own_coordinates()

        # Priorité 1: Phase de ciblage active
        # Si j'ai des hits à traiter ET une série de hits en cours (ou que j'initialise une nouvelle série)
        while self.hits_to_process:
            # Si ma série de hits actuelle est vide OU que le premier hit de ma série n'est plus dans mes hits à traiter
            # (ça peut arriver si un bateau est coulé et que hits_to_process n'a pas été entièrement nettoyé,
            # ou si current_hit_series a été vidée et qu'il reste d'autres hits à explorer).
            if not self.current_hit_series or self.current_hit_series[0] not in self.hits_to_process:
                # Je me réinitialise pour cibler le premier hit non résolu.
                self.current_hit_series = [self.hits_to_process[0]]
                # Je cherche les voisins autour de ce hit, en évitant mes propres bateaux.
                self.potential_next_shots = [
                    coord for coord in self._get_surrounding_coordinates(self.hits_to_process[0][0], self.hits_to_process[0][1])
                    if coord in self.untried_coordinates and coord not in own_ship_coords
                ]
                random.shuffle(self.potential_next_shots)
                self.current_target_direction = None # Réinitialiser la direction car je change de cible "principale"

            # Si j'ai au moins deux hits dans ma série et que je n'ai plus de tirs potentiels,
            # c'est que je dois déduire la direction du navire pour continuer.
            if len(self.current_hit_series) >= 2 and not self.potential_next_shots:
                self._determine_and_extend_direction() # J'affine ma stratégie pour prolonger la ligne

            # Si après tout ça, ma liste de tirs potentiels est vide (j'ai tout exploré autour du hit initial
            # ou mes prolongements n'ont rien donné), je reprends autour du DERNIER hit de ma série.
            if not self.potential_next_shots:
                last_series_hit = self.current_hit_series[-1]
                self.potential_next_shots = [
                    coord for coord in self._get_surrounding_coordinates(last_series_hit[0], last_series_hit[1])
                    if coord in self.untried_coordinates and coord not in own_ship_coords # Toujours filtrer mes bateaux !
                ]
                random.shuffle(self.potential_next_shots)

            # Si j'ai des tirs potentiels, j'en prends un et je le joue.
            if self.potential_next_shots:
                shot_coord = self.potential_next_shots.pop(0)
                if shot_coord in self.untried_coordinates: # S'assurer que je ne l'ai pas déjà tiré par accident
                    self.untried_coordinates.remove(shot_coord)
                    print(f"{self.name} cible à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} (mode ciblage actif) !")
                    return shot_coord
                self.potential_next_shots = [] # Si le coup n'est plus valide, vider pour recalculer

            # Si je n'ai plus de tirs potentiels pour le hit en cours, ça veut dire que ce hit
            # ne m'a pas mené à couler un bateau (peut-être un coup isolé ou un navire coulé par un autre moyen).
            # Je le retire donc de ma liste de hits à traiter et je réinitialise ma série.
            if self.hits_to_process: # S'assurer qu'il y a quelque chose à pop
                 self.hits_to_process.pop(0)
            self.current_hit_series = []
            self.current_target_direction = None
            self.potential_next_shots = []

        # Priorité 2: Stratégie de fin de jeu (mon mode "finisher" !)
        # Si vous n'avez presque plus de vie ET qu'il me reste des hits "dormants" (navires touchés mais pas coulés).
        if opponent_remaining_hp is not None and opponent_remaining_hp <= self.endgame_threshold:
            # Je filtre les hits qui n'ont pas encore été traités et qui ne sont pas des bateaux coulés.
            dormant_hits = [
                h for h in self.hits_to_process if h not in self.sunk_ships_coords
            ]
            random.shuffle(dormant_hits) # Un peu d'aléatoire pour rester imprévisible

            if dormant_hits:
                # Je choisis le premier hit dormant et je le traite comme un nouveau point de départ.
                first_dormant_hit = dormant_hits[0]
                self.current_hit_series = [first_dormant_hit] # Je le mets dans ma série actuelle
                self.potential_next_shots = [
                    coord for coord in self._get_surrounding_coordinates(first_dormant_hit[0], first_dormant_hit[1])
                    if coord in self.untried_coordinates and coord not in own_ship_coords # Toujours mes propres bateaux... non !
                ]
                random.shuffle(self.potential_next_shots)

                if self.potential_next_shots:
                    shot_coord = self.potential_next_shots.pop(0)
                    if shot_coord in self.untried_coordinates:
                        self.untried_coordinates.remove(shot_coord)
                        print(f"{self.name} (MODE FIN DE JEU) cible un ancien hit à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} !")
                        return shot_coord
                    self.potential_next_shots = [] # Si le coup n'est plus valide

        # Priorité 3: Phase de chasse améliorée (je cherche de nouvelles cibles intelligemment)
        # Utiliser la grille de probabilités sophistiquée
        prob_grid = self._compute_probability_grid()
        
        # Trouver les cases avec la probabilité maximale
        max_prob = 0
        best_coords = []
        
        for r in range(self.own_board.size):
            for c in range(self.own_board.size):
                if (r, c) in self.untried_coordinates and (r, c) not in own_ship_coords:
                    if prob_grid[r][c] > max_prob:
                        max_prob = prob_grid[r][c]
                        best_coords = [(r, c)]
                    elif prob_grid[r][c] == max_prob and max_prob > 0:
                        best_coords.append((r, c))
        
        # Si on a des cases avec une probabilité élevée, les utiliser
        if best_coords and max_prob > 0:
            # Privilégier la parité parmi les meilleures cases
            parity_best = [(r, c) for (r, c) in best_coords if (r + c) % 2 == 0]
            candidates = parity_best if parity_best else best_coords
            shot_coord = random.choice(candidates)
            self.untried_coordinates.remove(shot_coord)
            print(f"{self.name} utilise la grille de probabilités avancée à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} !")
            return shot_coord
        
        # Si pas de probabilités élevées, utiliser la stratégie de parité optimisée
        optimal_parity_coords = self._get_optimal_parity_coordinates()
        if optimal_parity_coords:
            shot_coord = random.choice(optimal_parity_coords)
            self.untried_coordinates.remove(shot_coord)
            print(f"{self.name} utilise la stratégie de parité optimisée à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} !")
            return shot_coord
        
        # Fallback : tir aléatoire parmi les coordonnées non essayées
        available_coords = [coord for coord in self.untried_coordinates if coord not in own_ship_coords]
        if available_coords:
            shot_coord = random.choice(available_coords)
            self.untried_coordinates.remove(shot_coord)
            print(f"{self.name} utilise un tir aléatoire à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} !")
            return shot_coord
        
        # Si, par un miracle ou un bug, je n'ai plus aucune coordonnée à tirer,
        # c'est que quelque chose ne va pas.
        raise Exception("L'IA n'a plus de coups possibles ! (Tous les navires devraient être coulés ou jeu buggé)")

    def _get_surrounding_coordinates(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Retourne les coordonnées adjacentes (haut, bas, gauche, droite) d'une cellule."""
        coords = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # Haut, Bas, Gauche, Droite
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.own_board.size and 0 <= nc < self.own_board.size:
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
            if next_c_right < self.own_board.size and (last_hit[0], next_c_right) in self.untried_coordinates:
                self.potential_next_shots.append((last_hit[0], next_c_right))
            # Vers la gauche (à partir du premier hit de la série)
            next_c_left = self.current_hit_series[0][1] - 1
            if next_c_left >= 0 and (self.current_hit_series[0][0], next_c_left) in self.untried_coordinates:
                self.potential_next_shots.append((self.current_hit_series[0][0], next_c_left))
        elif self.current_target_direction == 'V':
            # Vers le bas
            next_r_down = last_hit[0] + 1
            if next_r_down < self.own_board.size and (next_r_down, last_hit[1]) in self.untried_coordinates:
                self.potential_next_shots.append((next_r_down, last_hit[1]))
            # Vers le haut (à partir du premier hit de la série)
            next_r_up = self.current_hit_series[0][0] - 1
            if next_r_up >= 0 and (next_r_up, self.current_hit_series[0][1]) in self.untried_coordinates:
                self.potential_next_shots.append((next_r_up, self.current_hit_series[0][1]))

        # Filtrez les tirs déjà faits ou hors limites
        self.potential_next_shots = [
            coord for coord in self.potential_next_shots
            if 0 <= coord[0] < self.own_board.size and 0 <= coord[1] < self.own_board.size and \
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

    def process_shot_result(self, shot_coord: Tuple[int, int], result: str):
        """
        Met à jour l'état interne de l'IA en fonction du résultat de son tir.
        Inclut l'adaptation dynamique de la stratégie basée sur les performances.
        """
        print(f"IA: Début process_shot_result pour {shot_coord}, résultat: {result}.")
        r, c = shot_coord
        
        # Mettre à jour les statistiques
        self.shots_fired += 1
        self.last_shot_result = result
        
        # Assurez-vous de retirer la coordonnée des tirs non essayés
        if shot_coord in self.untried_coordinates:
            self.untried_coordinates.remove(shot_coord)

        if result == 'hit':
            self.hits_achieved += 1
            self.consecutive_misses = 0  # Reset les misses consécutifs
            self.target_board.grid[r][c] = 'X'
            # Ajouter à hits_to_process si ce n'est pas déjà un doublon
            if shot_coord not in self.hits_to_process:
                self.hits_to_process.append(shot_coord)
            # Ajouter à current_hit_series pour la détection de ligne
            if shot_coord not in self.current_hit_series:
                self.current_hit_series.append(shot_coord)
            self.potential_next_shots = [] # Vider, car on va en regénérer des meilleurs

        elif result == 'miss':
            self.consecutive_misses += 1
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
            self.hits_achieved += 1
            self.ships_sunk += 1
            self.consecutive_misses = 0
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
        
        # Adaptation dynamique de la stratégie
        self._adapt_strategy()
            
        print(f"IA: Fin process_shot_result. Stats: {self.hits_achieved}/{self.shots_fired} hits, {self.ships_sunk} coulés.")

        # Dans tous les cas, ce coup a été joué, donc je le retire de ma liste de coups à essayer.
        if shot_coord in self.untried_coordinates:
            self.untried_coordinates.remove(shot_coord)

    def _compute_probability_grid(self) -> List[List[int]]:
        """
        Calcule une grille de probabilités sophistiquée pour optimiser la recherche de navires.
        Prend en compte les navires restants, les patterns de tir, et les contraintes géométriques.
        """
        size = self.own_board.size
        prob_grid = [[0 for _ in range(size)] for _ in range(size)]
        
        # Obtenir les navires non coulés et leurs tailles
        ships_left = []
        for ship in self.ships_to_place:
            if not ship.is_sunk():
                ships_left.append(ship.length)
        
        # Si aucun navire restant, retourner une grille vide
        if not ships_left:
            return prob_grid
        
        # Créer un ensemble des cases déjà tirées
        shot_cells = set()
        for r in range(size):
            for c in range(size):
                if self.target_board.grid[r][c] != '~':
                    shot_cells.add((r, c))
        
        # Pour chaque navire restant, calculer toutes les positions possibles
        for ship_length in ships_left:
            # Positions horizontales
            for r in range(size):
                for c in range(size - ship_length + 1):
                    positions = [(r, c + i) for i in range(ship_length)]
                    # Vérifier si toutes les positions sont valides
                    if all(pos not in shot_cells for pos in positions):
                        # Vérifier qu'aucune position n'est un miss ('O')
                        if all(self.target_board.grid[pos[0]][pos[1]] != 'O' for pos in positions):
                            # Augmenter la probabilité pour chaque position
                            for pos in positions:
                                prob_grid[pos[0]][pos[1]] += 1
            
            # Positions verticales
            for c in range(size):
                for r in range(size - ship_length + 1):
                    positions = [(r + i, c) for i in range(ship_length)]
                    # Vérifier si toutes les positions sont valides
                    if all(pos not in shot_cells for pos in positions):
                        # Vérifier qu'aucune position n'est un miss ('O')
                        if all(self.target_board.grid[pos[0]][pos[1]] != 'O' for pos in positions):
                            # Augmenter la probabilité pour chaque position
                            for pos in positions:
                                prob_grid[pos[0]][pos[1]] += 1
        
        # Bonus pour les cases adjacentes aux hits (stratégie de ciblage)
        for r in range(size):
            for c in range(size):
                if self.target_board.grid[r][c] == 'X':  # Hit
                    # Ajouter un bonus aux cases adjacentes
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < size and 0 <= nc < size:
                            if self.target_board.grid[nr][nc] == '~':  # Case non tirée
                                prob_grid[nr][nc] += 2  # Bonus pour les cases adjacentes
        
        # Pénalité pour les cases isolées (stratégie de parité)
        for r in range(size):
            for c in range(size):
                if prob_grid[r][c] > 0:
                    # Vérifier si la case est isolée (pas de navire adjacent possible)
                    isolated = True
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < size and 0 <= nc < size:
                            if prob_grid[nr][nc] > 0:
                                isolated = False
                                break
                    if isolated:
                        prob_grid[r][c] = max(0, prob_grid[r][c] - 1)  # Légère pénalité
        
        return prob_grid

    def _adapt_strategy(self):
        """
        Adapte la stratégie de l'IA en fonction de ses performances récentes.
        """
        if self.shots_fired < 5:  # Pas assez de données pour adapter
            return
        
        # Calculer le taux de réussite
        hit_rate = self.hits_achieved / self.shots_fired
        
        # Adapter le niveau d'agression
        if hit_rate < 0.2:  # Performance faible
            self.aggression_level = min(2.0, self.aggression_level + 0.1)
            print(f"IA: Performance faible ({hit_rate:.2f}), augmentation de l'agression à {self.aggression_level:.2f}")
        elif hit_rate > 0.6:  # Performance excellente
            self.aggression_level = max(0.5, self.aggression_level - 0.05)
            print(f"IA: Performance excellente ({hit_rate:.2f}), réduction de l'agression à {self.aggression_level:.2f}")
        
        # Adapter la préférence de parité
        if self.consecutive_misses >= 3:
            self.parity_preference = max(0.5, self.parity_preference - 0.1)
            print(f"IA: Miss consécutifs, réduction de la préférence de parité à {self.parity_preference:.2f}")
        elif self.last_shot_result == 'hit':
            self.parity_preference = min(1.5, self.parity_preference + 0.05)
            print(f"IA: Hit récent, augmentation de la préférence de parité à {self.parity_preference:.2f}")

    def _get_optimal_parity_coordinates(self) -> List[Tuple[int, int]]:
        """
        Retourne les coordonnées optimales basées sur la parité pour maximiser la couverture.
        Utilise une stratégie en damier optimisée pour trouver les navires plus efficacement.
        """
        even_coords = []
        odd_coords = []
        
        for r in range(self.own_board.size):
            for c in range(self.own_board.size):
                if (r + c) % 2 == 0:
                    even_coords.append((r, c))
                else:
                    odd_coords.append((r, c))
        
        # Filtrer les coordonnées déjà tirées
        even_available = [coord for coord in even_coords if coord in self.untried_coordinates]
        odd_available = [coord for coord in odd_coords if coord in self.untried_coordinates]
        
        # Retourner la liste avec le plus de coordonnées disponibles
        if len(even_available) >= len(odd_available):
            return even_available
        else:
            return odd_available
