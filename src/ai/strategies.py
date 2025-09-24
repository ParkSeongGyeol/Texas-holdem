from abc import ABC, abstractmethod
from typing import List, Tuple
from src.core.card import Card
from src.core.player import Player
from .base_ai import Action ,AIPlayer

class Strategy(ABC):
    @abstractmethod
    def decide(
        self,
        ai: AIPlayer,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        opponents: List[Player],
    ) -> Tuple[Action, int] : pass

class TightStrategy(Strategy): 
     def decide(self, ai, community_cards, pot, current_bet, opponents) : 
        strength = ai.analyze_hand_strength(ai.hole_cards, community_cards)
        if current_bet == 0:
            return (Action.RAISE, max(10, pot//4)) if strength >= 0.75 else (Action.CHECK, 0)
        if strength >= 0.75: return (Action.RAISE, max(current_bet*2, 20))
        if strength >= 0.50: return (Action.CALL, current_bet)
        return (Action.FOLD, 0)
    
class LooseStrategy(Strategy): 
     def decide(self, ai, community_cards, pot, current_bet, opponents) : 
        strength = ai.analyze_hand_strength(ai.hole_cards, community_cards)
        if current_bet == 0:
            return (Action.RAISE, max(10, pot//5)) if strength >= 0.60 else (Action.CHECK, 0)
        if strength >= 0.30: return (Action.CALL, current_bet)
        return (Action.FOLD, 0)