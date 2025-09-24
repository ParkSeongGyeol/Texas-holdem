"""
AI 인터페이스 - 박종호 담당
AI 기본 인터페이스 및 의사결정 시스템
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from enum import Enum

from src.core.card import Card
from src.core.player import Player


class Action(Enum):
    """플레이어 액션"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class AIPlayer(Player, ABC):
    """AI 플레이어 추상 클래스"""

    def __init__(self, name: str, chips: int = 1000, difficulty_level: int = 1):
        super().__init__(name, chips)
        self.difficulty_level = difficulty_level
        self.opponent_patterns = {}  # 상대 패턴 분석 데이터

    @abstractmethod
    def make_decision(
        self,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        opponents: List[Player]
    ) -> Tuple[Action, int]:
        """
        의사결정 메소드
        Returns: (액션, 베팅금액)
        """
        pass

    @abstractmethod
    def analyze_hand_strength(
        self,
        hole_cards: List[Card],
        community_cards: List[Card]
    ) -> float:
        """
        핸드 강도 분석
        Returns: 0.0~1.0 사이의 핸드 강도
        """
        pass

    def update_opponent_pattern(self, opponent: Player, action: Action, amount: int) -> None:
        """상대 패턴 업데이트"""
        # TODO: 상대 패턴 분석 로직 (박종호)
        if opponent.name not in self.opponent_patterns:
            self.opponent_patterns[opponent.name] = []

        self.opponent_patterns[opponent.name].append({
            'action': action,
            'amount': amount,
            'pot': 0  # 현재 팟 크기 기록 필요
        })