import random
from typing import Tuple, List, Optional
from .player import Player
from .ship import Ship 

class AIPlayer(Player):
    """
    Salut, c'est moi, l'IA ! Je suis là pour vous donner du fil à retordre à la Bataille Navale.
    Ma logique de tir est de plus en plus... machiavélique !
    Je combine la chasse (où chercher au début), le ciblage (quand j'ai touché un truc)
    et même des stratégies de psychologie inversée (enfin, j'essaie !) pour vous battre.
    """
    def __init__(self, name: str = "IA", board_size: int = 10):
        super().__init__(name, board_size)
        
        # Toutes les coordonnées que je n'ai pas encore tirées. C'est ma "to-do list" des cibles.
        self.untried_coordinates: List[Tuple[int, int]] = []
        self._initialize_untried_coordinates()

        # Ici, je garde une trace de tous les "hits" (coups au but) que j'ai faits
        # et que je n'ai pas encore "résolus" (c'est-à-dire que le bateau n'est pas coulé).
        # C'est ma liste de "chantiers ouverts".
        self.hits_to_process: List[Tuple[int, int]] = [] 
        
        # Quand je touche un bateau, je génère des tirs autour de lui.
        # Cette liste contient les prochains endroits logiques à viser.
        self.potential_next_shots: List[Tuple[int, int]] = [] 
        
        # Et ici, je note les coordonnées de tous les navires que j'ai déjà coulés.
        # Histoire de ne pas tirer sur les morts... ça ne sert à rien.
        self.sunk_ships_coords: List[Tuple[int, int]] = [] 

        # En mode "ciblage", je garde une trace de la direction (Horizontal ou Vertical)
        # pour essayer de couler le bateau plus vite. S'il n'y a pas de direction claire, c'est None.
        self.current_target_direction: Optional[str] = None 
        
        # C'est la série de coups consécutifs sur un MÊME bateau que je suis en train de couler.
        # C'est mon "fil d'Ariane" quand je suis sur une bonne piste.
        self.current_hit_series: List[Tuple[int, int]] = []

        # Ah, ma petite carte secrète ! Ici, je note où VOUS (l'adversaire) avez tiré sur MON plateau.
        # 'U' (Untouched) : Vous n'avez pas encore tiré ici (intéressant...).
        # 'X' (Hit) : Vous m'avez touché ici (aïe !).
        # 'O' (Miss) : Vous avez tiré ici et vous avez raté (hehe).
        self.opponent_shot_tracking_grid: List[List[str]] = [['U' for _ in range(board_size)] for _ in range(board_size)]
        
        # Une simple liste pour garder l'historique de tous vos tirs (utile pour certaines déductions futures, si j'en fais).
        self.opponent_shots_made: List[Tuple[int, int]] = []

        # Le seuil de "panique" (ou plutôt de "finisher").
        # Quand il ne vous reste plus que ce nombre de points de vie (ou moins),
        # L'IA passe en mode "fin de jeu" pour vous achever rapidement.
        self.endgame_threshold: int = 7 # Exemple: s'active quand l'adversaire a moins de 7 points de vie restants

    def _initialize_untried_coordinates(self):
        """
        J'initialise ma liste de toutes les cases possibles à viser.
        Pour l'instant, je les mets toutes, et je les mélangerai aléatoirement.
        Je filtrerai ensuite celles où j'ai MES PROPRES bateaux.
        """
        all_coords = []
        for r in range(self.own_board.size):
            for c in range(self.own_board.size):
                all_coords.append((r, c))
        random.shuffle(all_coords) # Un petit coup de dés pour commencer
        self.untried_coordinates = all_coords

    def place_ships(self):
        """
        Je place mes navires de manière aléatoire.
        Pas de triche ici, juste un peu de chance !
        """
        print(f"\n{self.name} place ses navires...")
        for ship in self.ships_to_place:
            placed = False
            while not placed:
                # Je choisis des coordonnées de départ au hasard
                r = random.randint(0, self.own_board.size - 1)
                c = random.randint(0, self.own_board.size - 1)
                start_coord = (r, c)

                # Je choisis une orientation au hasard (Horizontal ou Vertical)
                orientation = random.choice(['H', 'V'])
                
                # J'essaie de placer le navire. Le plateau vérifiera si c'est valide.
                placed = self.own_board.place_ship(ship, start_coord, orientation)
                # Si 'placed' est False, je boucle et j'essaie encore !
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
        # Je divise les cases non encore tirées en deux catégories :
        # 1. Celles où VOUS n'avez pas tiré sur MON plateau (potentiellement vos navires !)
        # 2. Celles où VOUS avez déjà tiré (moins probable que vos navires y soient).
        
        # Je filtre `untried_coordinates` pour ne pas inclure mes propres bateaux ici.
        # (Normalement, `update_untried_coordinates_after_placement` le fait déjà au début,
        # mais c'est une sécurité supplémentaire et pour les cas où cette méthode est appelée plus tard).
        available_untried_for_hunt = [coord for coord in self.untried_coordinates if coord not in own_ship_coords]

        # --- STRATÉGIE DE PROBABILITÉ ---
        prob_grid = self._compute_probability_grid()
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
        if best_coords:
            # On privilégie la parité si possible
            parity_best = [(r, c) for (r, c) in best_coords if (r + c) % 2 == 0]
            candidates = parity_best if parity_best else best_coords
            shot_coord = random.choice(candidates)
            self.untried_coordinates.remove(shot_coord)
            print(f"{self.name} utilise la grille de probabilités à {chr(65 + shot_coord[1])}{shot_coord[0] + 1} !")
            return shot_coord
        
        # Si, par un miracle ou un bug, je n'ai plus aucune coordonnée à tirer,
        # c'est que quelque chose ne va pas.
        raise Exception("L'IA n'a plus de coups possibles ! (Tous les navires devraient être coulés ou jeu buggé)")

    def _get_surrounding_coordinates(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Je génère les coordonnées des cases directement adjacentes (haut, bas, gauche, droite).
        C'est pour trouver la suite du bateau quand je l'ai touché.
        """
        coords = []
        possible_moves = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        for pr, pc in possible_moves:
            # Je m'assure que les coordonnées sont bien sur le plateau de jeu.
            if 0 <= pr < self.own_board.size and 0 <= pc < self.own_board.size:
                coords.append((pr, pc))
        return coords

    def _determine_and_extend_direction(self):
        """
        Quand j'ai touché un bateau au moins deux fois, j'essaie de deviner sa direction
        (horizontal ou vertical) pour viser plus efficacement.
        """
        if len(self.current_hit_series) < 2:
            return # J'ai besoin d'au moins deux hits pour deviner une direction !

        sorted_hits = sorted(self.current_hit_series) # Je trie mes hits pour faciliter l'analyse
        first_hit = sorted_hits[0]
        last_hit = sorted_hits[-1]

        potential_coords = []
        own_ship_coords = self._get_occupied_own_coordinates() # Encore une fois, pas de tir amical !

        if first_hit[0] == last_hit[0]: # Si les lignes sont les mêmes, c'est horizontal !
            self.current_target_direction = 'H'
            potential_coords = [
                (first_hit[0], min(h[1] for h in sorted_hits) - 1), # À gauche du premier hit
                (first_hit[0], max(h[1] for h in sorted_hits) + 1)  # À droite du dernier hit
            ]
        elif first_hit[1] == last_hit[1]: # Si les colonnes sont les mêmes, c'est vertical !
            self.current_target_direction = 'V'
            potential_coords = [
                (min(h[0] for h in sorted_hits) - 1, first_hit[1]), # Au-dessus du premier hit
                (max(h[0] for h in sorted_hits) + 1, first_hit[1])  # En dessous du dernier hit
            ]
        else: # Oups, mes hits ne sont ni purement horizontaux, ni purement verticaux (bug ou cas complexe)
            self.current_target_direction = None # Je ne peux pas déterminer la direction
            # Je reviens à la tactique de chercher autour du dernier hit, c'est plus sûr.
            potential_coords = self._get_surrounding_coordinates(last_hit[0], last_hit[1])

        # J'ajoute ces nouvelles coordonnées potentielles à ma liste de tirs à essayer,
        # en filtrant celles déjà tirées ou mes propres navires.
        self.potential_next_shots.extend([
            coord for coord in potential_coords 
            if coord in self.untried_coordinates and coord not in own_ship_coords
        ])
        random.shuffle(self.potential_next_shots) # Et je mélange, histoire de.
        
    # Mince alors, cette histoire d'autocompletion de code me connait déjà trop bien ! 
    # Genre, il copie mon language et tout ! 
    # je vais devoir devenir encore plus imprévisible 😂

    def process_shot_result(self, shot_coord: Tuple[int, int], result: str):
        """
        Mon tir a eu un résultat ! Je mets à jour mes connaissances.
        C'est mon moment d'apprentissage après chaque coup.
        """
        r, c = shot_coord
        
        if result == 'hit':
            self.target_board.grid[r][c] = 'X' # Je marque la cible comme touchée sur ma carte de l'adversaire
            # Si ce n'est pas déjà un hit que je suis en train de traiter dans hits_to_process, je l'ajoute.
            if shot_coord not in self.hits_to_process:
                self.hits_to_process.append(shot_coord)
            self.current_hit_series.append(shot_coord) # J'ajoute à ma série en cours
            self.potential_next_shots = [] # Je vide, je vais en regénérer des meilleurs

        elif result == 'miss':
            self.target_board.grid[r][c] = 'O' # Je marque la cible comme manquée
            # Pas besoin de faire grand-chose ici, la logique de get_shot_coordinates gérera la suite.

        elif result == 'sunk':
            self.target_board.grid[r][c] = 'X' # Le dernier coup qui a coulé est aussi un 'X'
            # Un navire a été coulé ! Victoire !
            # Je retire toutes les coordonnées de ce navire (de ma série actuelle) de mes hits à traiter.
            for hit in self.current_hit_series:
                if hit in self.hits_to_process:
                    self.hits_to_process.remove(hit)

            self.sunk_ships_coords.extend(self.current_hit_series) # J'ajoute ces coordonnées à ma liste de navires coulés
            self.current_hit_series = [] # Je vide ma série, ce navire est fini
            self.current_target_direction = None # Plus besoin de direction pour celui-ci
            self.potential_next_shots = [] # Et je vide mes tirs potentiels

        # Dans tous les cas, ce coup a été joué, donc je le retire de ma liste de coups à essayer.
        if shot_coord in self.untried_coordinates:
            self.untried_coordinates.remove(shot_coord)

    def _compute_probability_grid(self) -> List[List[int]]:
        """
        Calcule une grille de probabilités : pour chaque case, le nombre de façons dont un navire restant peut s'y trouver.
        """
        size = self.own_board.size
        prob_grid = [[0 for _ in range(size)] for _ in range(size)]
        # On considère uniquement les navires non coulés
        ships_left = [ship for ship in self.ships_to_place if not all(coord in self.sunk_ships_coords for coord in ship.coordinates)]
        # Cases déjà tirées (toutes les cases de la grille qui ne sont pas '~')
        forbidden = set()
        for r in range(size):
            for c in range(size):
                if self.target_board.grid[r][c] != '~':
                    forbidden.add((r, c))
        for ship in ships_left:
            length = ship.length if hasattr(ship, 'length') else len(ship.coordinates)
            # Horizontal
            for r in range(size):
                for c in range(size - length + 1):
                    positions = [(r, c + i) for i in range(length)]
                    if all(self.target_board.grid[x][y] != 'O' and (x, y) not in forbidden for (x, y) in positions):
                        for (x, y) in positions:
                            prob_grid[x][y] += 1
            # Vertical
            for c in range(size):
                for r in range(size - length + 1):
                    positions = [(r + i, c) for i in range(length)]
                    if all(self.target_board.grid[x][y] != 'O' and (x, y) not in forbidden for (x, y) in positions):
                        for (x, y) in positions:
                            prob_grid[x][y] += 1
        return prob_grid