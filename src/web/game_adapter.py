import queue
import time
import asyncio
from typing import Optional, Tuple, List, Dict

from src.core.game import PokerGame, Action, GamePhase
from src.core.player import Player
from src.algorithms.monte_carlo import MonteCarloSimulator

class WebPokerGame(PokerGame):
    """
    Web-adapted PokerGame that uses queues for input/output 
    instead of console print/input.
    """
    def __init__(self, broadcast_callback, small_blind: int = 10, big_blind: int = 20):
        super().__init__(small_blind, big_blind)
        self.broadcast_callback = broadcast_callback  # Async function to send updates
        self.input_queues: Dict[str, queue.Queue] = {} # player_name -> Queue
        self.game_running = False
        self.monte_carlo = MonteCarloSimulator(num_simulations=1000)

    def add_player(self, name: str, chips: int = 1000) -> None:
        super().add_player(name, chips)
        self.input_queues[name] = queue.Queue()

    def log_action(self, message: str) -> None:
        """Override log_action to broadcast to web clients"""
        super().log_action(message)
        # We need to run the async callback from this synchronous method
        # This assumes log_action is called from the game thread
        self._broadcast_sync({"type": "action_log", "message": message})

    def display_game_state(self) -> None:
        """Override display_game_state to broadcast full state"""
        # Calculate win rates for all active players
        win_rates = {}
        active_players = self.get_active_players()
        
        # Only calculate if game is in progress and not showdown
        if self.current_phase != GamePhase.SHOWDOWN and len(active_players) > 1:
            # Note: This might be slow if done synchronously. 
            # For better performance, we could run this in parallel or use a smaller simulation count.
            # Here we use the parallel_simulation method from MonteCarloSimulator
            
            community_cards = self.community_cards
            for player in active_players:
                # We need to estimate opponents count (active players - self)
                opponents_count = len(active_players) - 1
                if opponents_count > 0:
                    win_rate = self.monte_carlo.parallel_simulation(
                        player.hand, 
                        community_cards, 
                        num_opponents=opponents_count,
                        num_threads=4
                    )
                    win_rates[player.name] = round(win_rate * 100, 1)

        # Construct state object
        state = {
            "type": "update_state",
            "pot": self.pot,
            "community": [self._serialize_card(c) for c in self.community_cards],
            "phase": self.current_phase.value,
            "players": []
        }

        for player in self.players:
            p_data = {
                "name": player.name,
                "chips": player.chips,
                "current_bet": player.current_bet,
                "is_active": player.is_active,
                "has_folded": player.has_folded,
                "is_all_in": player.is_all_in,
                "hand": [self._serialize_card(c) for c in player.hand], # Always send hand, frontend decides visibility
                "win_rate": win_rates.get(player.name, 0)
            }
            state["players"].append(p_data)

        self._broadcast_sync(state)

    def get_player_action(self, player: Player) -> Tuple[Action, int]:
        """Override get_player_action to wait for web input"""
        
        # 1. Notify frontend that it's this player's turn
        self._broadcast_sync({
            "type": "turn_change",
            "current_player": player.name,
            "available_actions": [a.value for a in self.get_available_actions(player)],
            "call_amount": self.current_bet - player.current_bet,
            "min_raise": self.min_raise
        })

        # 2. Wait for input from queue
        # If it's an AI player, we would call AI logic here.
        # For now, we assume all players added via add_player are human or handled via queue.
        # If we integrate AI, we check isinstance(player, AIPlayer)
        
        # Check if AI (Duck typing or name convention for now, or better: use AIPlayer class check)
        # Since we haven't imported AIPlayer here to avoid circular imports if not careful, 
        # let's assume if no queue exists, it might be AI? Or we explicitly handle AI in app.py
        
        if player.name not in self.input_queues:
             # Fallback or Error
             print(f"No input queue for {player.name}")
             return (Action.FOLD, 0)

        q = self.input_queues[player.name]
        try:
            # Wait indefinitely for action
            action_data = q.get() 
            # action_data should be {"action": "FOLD", "amount": 0}
            
            action_str = action_data.get("action")
            amount = int(action_data.get("amount", 0))
            
            if action_str == "FOLD":
                return (Action.FOLD, 0)
            elif action_str == "CHECK":
                return (Action.CHECK, 0)
            elif action_str == "CALL":
                # Calculate call amount
                call_amount = self.current_bet - player.current_bet
                return (Action.CALL, call_amount)
            elif action_str == "RAISE":
                return (Action.RAISE, amount)
            elif action_str == "ALL_IN":
                return (Action.ALL_IN, player.chips)
            else:
                # Default fallback
                return (Action.FOLD, 0)
                
        except Exception as e:
            print(f"Error getting action: {e}")
            return (Action.FOLD, 0)

    def _broadcast_sync(self, message: dict):
        """Helper to run async broadcast from sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no loop in current thread, we might need to pass the main loop
            # But usually this runs in a thread where there is no loop.
            # We need the loop where the websocket server is running.
            pass
            
        # We need to use the loop passed from the main thread?
        # Actually, asyncio.run_coroutine_threadsafe is the way.
        # We need a reference to the main event loop.
        pass 
        # For now, we will rely on the callback being a wrapper that handles thread safety
        # or we pass the loop to __init__
        
        if self.broadcast_callback:
            self.broadcast_callback(message)

    def _serialize_card(self, card):
        return {'rank': card.rank.symbol, 'suit': card.suit.name[0]}
