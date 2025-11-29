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

class AdaptiveRuleBasedAI(RuleBasedAI):
    # ... (상대 스타일 분석/스위칭 로직은 그대로) ...

    def __init__(self, name: str, position: Position, base_mode: str = "tight"):
        self.tight_strategy = TightStrategy()
        self.loose_strategy = LooseStrategy()

        # 초기 전략 선택
        if base_mode == "loose":
            strategy = self.loose_strategy
            self.current_mode = "loose"
        else:
            strategy = self.tight_strategy
            self.current_mode = "tight"