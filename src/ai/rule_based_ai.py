from typing import List, Tuple

from src.core.card import Card
from src.ai.base_ai import AIPlayer, Position
from src.ai.strategies import TightStrategy, LooseStrategy

class RuleBasedAI(AIPlayer):

    def __init__(self, name: str, position: Position, strategy_type="tight"):
        if strategy_type == "tight":
            strategy = TightStrategy()
        else:
            strategy = LooseStrategy()

        super().__init__(name, position, strategy)

    def receive_hole_cards(self, cards: List[Card]):
        self.hole_cards = cards

    def act(
        self,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        opponents: List[AIPlayer]
    ):
        return self.make_decision(
            community_cards,
            pot,
            current_bet,
            opponents
        )

class AdaptiveRuleBasedAI(AIPlayer):
    def __init__(self, name: str, position: Position, base_mode="tight"):
        self.tight_strategy = TightStrategy()
        self.loose_strategy = LooseStrategy()

        if base_mode == "loose":
            strategy = self.loose_strategy
            self.current_mode = "loose"
        else:
            strategy = self.tight_strategy
            self.current_mode = "tight"

        super().__init__(name, position, strategy)

    def receive_hole_cards(self, cards: List[Card]):
        self.hole_cards = cards

    def act(self, community_cards, pot, current_bet, opponents):
        # 적응형 전략 스위칭
        self.choose_strategy()

        return super().make_decision(
            community_cards,
            pot,
            current_bet,
            opponents,
        )