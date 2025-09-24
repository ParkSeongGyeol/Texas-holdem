from typing import List, Tuple

from base_ai import AIPlayer, Action
from strategies import Strategy, TightStrategy

class RuleBasedAI(AIPlayer):
    def __init__(self, name: str, chips: int = 1000, difficulty_level: int = 1, strategy: Strategy = None):
        super().__init__(name, chips, difficulty_level, strategy or TightStrategy())

    def analyze_hand_strength(self, hole_cards: List[str], community_cards: List[str]) -> float:
        ranks = {c[0] for c in (hole_cards + community_cards)}
        if "A" in ranks: return 0.8
        if "K" in ranks: return 0.6
        return 0.4

    def make_decision(
        self,
        community_cards: List[str],
        pot: int,
        current_bet: int,
        opponents: List,
    ) -> Tuple[Action, int]:
        if self.strategy:
            return self.strategy.decide(self, community_cards, pot, current_bet, opponents)
        return (Action.CHECK if current_bet == 0 else Action.FOLD, 0)