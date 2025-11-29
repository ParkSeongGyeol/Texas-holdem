# src/ai/base_ai.py

from typing import List, Tuple
from abc import ABC, abstractmethod
from enum import Enum

from src.core.card import Card
from src.algorithms.hand_evaluator import HandEvaluator

class Position(Enum):
    SB = "sb"
    BB = "bb"


class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class AIPlayer(ABC):

    def __init__(self, name: str, position: Position, strategy):
        self.name = name
        self.position = position
        self.strategy = strategy

        self.hole_cards: List[Card] = []

        self.opponent_patterns = {}

    def card_to_code(self, card: Card) -> str:
        r = card.rank.symbol
        if r == "10":
            r = "T"
        return r + card.suit.value

    def to_codes(self, cards: List[Card]) -> List[str]:
        return [self.card_to_code(c) for c in cards]

  
    def hand_strength(self, hole_cards: List[Card], board_cards: List[Card]) -> float:
        """
        문자열 기반 evaluator / Card 기반 evaluator 양쪽에 대응 가능
        지금은 Card evaluator 점수 정규화 사용
        """

        try:
            seven = hole_cards + board_cards  # List[Card]

            rank, kickers, _ = HandEvaluator.evaluate_hand(seven)

            # Rank normalization (1~10 → 0~1)
            rank_score = (rank.value - 1) / 9

            kicker_score = 0.0
            if kickers:
                kicker_score = sum(k / 14 for k in kickers) / len(kickers)

            strength = rank_score * 0.8 + kicker_score * 0.2
            return max(0.0, min(1.0, strength))

        except:
            return 0.0


    def make_decision(
        self,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        opponents: List["AIPlayer"]
    ) -> Tuple[Action, int]:

        return self.strategy.decide(
            self,
            community_cards,
            pot,
            current_bet,
            opponents
        )

    def record_opponent_action(self, name: str, action: Action):
        if name not in self.opponent_patterns:
            self.opponent_patterns[name] = []
        self.opponent_patterns[name].append(action)