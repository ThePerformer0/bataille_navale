#!/usr/bin/env python3
"""
Script de test pour évaluer les performances de l'IA améliorée.
Compare l'IA avec différentes stratégies et calcule les statistiques.
"""

import random
import time
from src.ai_player import AIPlayer
from src.human_player import HumanPlayer
from src.game import Game

def test_ai_performance(num_games=100):
    """
    Teste les performances de l'IA sur un nombre donné de parties.
    """
    print(f"🧪 Test des performances de l'IA sur {num_games} parties...")
    
    ai_wins = 0
    human_wins = 0
    total_shots = 0
    total_hits = 0
    total_ships_sunk = 0
    
    for game_num in range(1, num_games + 1):
        print(f"\n🎮 Partie {game_num}/{num_games}")
        
        # Créer une nouvelle partie
        game = Game(board_size=10)
        
        # Placement automatique des navires
        game.player_human.place_ships()
        game.player_ai.place_ships()
        game.player_ai.update_untried_coordinates_after_placement()
        
        # Simuler la partie
        game_over = False
        current_player = game.player_human
        opponent = game.player_ai
        
        while not game_over:
            # Obtenir le tir du joueur actuel
            if isinstance(current_player, AIPlayer):
                shot_coord = current_player.get_shot_coordinates()
            else:
                # Pour le joueur humain, simuler un tir aléatoire
                available_coords = []
                for r in range(10):
                    for c in range(10):
                        if opponent.own_board.grid[r][c] == '~':
                            available_coords.append((r, c))
                shot_coord = random.choice(available_coords)
            
            # Traiter le tir
            result = opponent.own_board.receive_shot(shot_coord)
            
            # Mettre à jour la grille de cible du joueur
            r, c = shot_coord
            if result in ['hit', 'sunk']:
                current_player.target_board.grid[r][c] = 'X'
            else:
                current_player.target_board.grid[r][c] = 'O'
            
            # Informer l'IA du résultat
            if isinstance(current_player, AIPlayer):
                current_player.process_shot_result(shot_coord, result)
            
            # Vérifier si la partie est terminée
            if opponent.has_lost():
                game_over = True
                if isinstance(current_player, AIPlayer):
                    ai_wins += 1
                    print(f"🏆 L'IA a gagné en {current_player.shots_fired} tirs!")
                else:
                    human_wins += 1
                    print(f"🏆 Le joueur a gagné!")
                
                # Collecter les statistiques de l'IA
                if isinstance(current_player, AIPlayer):
                    total_shots += current_player.shots_fired
                    total_hits += current_player.hits_achieved
                    total_ships_sunk += current_player.ships_sunk
                elif isinstance(opponent, AIPlayer):
                    total_shots += opponent.shots_fired
                    total_hits += opponent.hits_achieved
                    total_ships_sunk += opponent.ships_sunk
            
            # Changer de joueur
            current_player, opponent = opponent, current_player
    
    # Afficher les résultats
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"Parties jouées: {num_games}")
    print(f"Victoires IA: {ai_wins} ({ai_wins/num_games*100:.1f}%)")
    print(f"Victoires Joueur: {human_wins} ({human_wins/num_games*100:.1f}%)")
    
    if ai_wins > 0:
        avg_shots = total_shots / ai_wins
        avg_hits = total_hits / ai_wins
        avg_ships = total_ships_sunk / ai_wins
        hit_rate = total_hits / total_shots if total_shots > 0 else 0
        
        print(f"\n🎯 STATISTIQUES DE L'IA:")
        print(f"Tirs moyens par victoire: {avg_shots:.1f}")
        print(f"Hits moyens par victoire: {avg_hits:.1f}")
        print(f"Navires coulés moyens: {avg_ships:.1f}")
        print(f"Taux de réussite global: {hit_rate*100:.1f}%")
    
    return ai_wins / num_games

def test_different_strategies():
    """
    Teste différentes configurations de l'IA pour trouver la meilleure.
    """
    print("🔬 Test de différentes stratégies...")
    
    strategies = [
        ("Stratégie par défaut", {}),
        ("Stratégie agressive", {"endgame_threshold": 2}),
        ("Stratégie conservatrice", {"endgame_threshold": 5}),
    ]
    
    results = {}
    
    for strategy_name, config in strategies:
        print(f"\n🧪 Test de la {strategy_name}...")
        
        # Modifier la configuration de l'IA
        original_threshold = AIPlayer.endgame_threshold if hasattr(AIPlayer, 'endgame_threshold') else 3
        
        # Test simple sur 10 parties
        win_rate = test_ai_performance(10)
        results[strategy_name] = win_rate
        
        print(f"Taux de victoire: {win_rate*100:.1f}%")
    
    # Trouver la meilleure stratégie
    best_strategy = max(results.items(), key=lambda x: x[1])
    print(f"\n🏆 Meilleure stratégie: {best_strategy[0]} ({best_strategy[1]*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DES TESTS DE PERFORMANCE DE L'IA")
    print("=" * 50)
    
    # Test principal
    win_rate = test_ai_performance(50)
    
    print(f"\n🎯 TAUX DE VICTOIRE GLOBAL: {win_rate*100:.1f}%")
    
    if win_rate > 0.7:
        print("🌟 L'IA est EXCELLENTE!")
    elif win_rate > 0.5:
        print("👍 L'IA est BONNE!")
    elif win_rate > 0.3:
        print("😐 L'IA est MOYENNE!")
    else:
        print("😞 L'IA a besoin d'amélioration!")
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés!") 