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

        self.opponent_stats = {
            "vpip": 0,       # voluntarily put money in pot
            "pfr": 0,        # preflop raiser
            "aggression": 0, # postflop bet/raise
            "hands": 0
        }

    def card_to_code(self, card: Card) -> str:
        r = card.rank.symbol
        if r == "10":
            r = "T"
        return r + card.suit.value

    def to_codes(self, cards: List[Card]) -> List[str]:
        return [self.card_to_code(c) for c in cards]

  
    def hand_strength(self, hole_cards: List[Card], board_cards: List[Card]) -> float:

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
        
    def update_opponent_stats(self, opponents_actions):
        s = self.opponent_stats
        s["hands"] += 1

        if opponents_actions.get("preflop_called"): 
            s["vpip"] += 1

        if opponents_actions.get("preflop_raised"):
            s["pfr"] += 1
            s["vpip"] += 1

        if opponents_actions.get("postflop_aggressive"):
            s["aggression"] += 1

    # -----------------------
    # ✔ 적응형: 상대 스타일 분석
    # -----------------------
    def classify_opponent(self):
        s = self.opponent_stats
        if s["hands"] < 8:
            return "unknown"

        vpip_rate = s["vpip"] / s["hands"]
        pfr_rate = s["pfr"] / s["hands"]

        if vpip_rate < 0.20:
            return "tight"
        elif vpip_rate > 0.40:
            return "loose"
        else:
            return "neutral"

    # -----------------------
    # ✔ 적응형: 전략 스위칭
    # -----------------------
    def choose_strategy(self):
        style = self.classify_opponent()

        if style == "tight":
            self.strategy = self.loose_strategy
            self.current_mode = "loose"

        elif style == "loose":
            self.strategy = self.tight_strategy
            self.current_mode = "tight"

        else:
            # 기본 유지
            self.current_mode = self.current_mode

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