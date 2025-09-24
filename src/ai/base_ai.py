"""
AI 인터페이스 - 박종호 담당
AI 기본 인터페이스 및 의사결정 시스템
"""

#difficulty_level = AI 난이도 설정
#community_cards = 테이블에 깔린 카드 
#current_bet = 내가 배팅하려면 필요한 금액

from abc import ABC, abstractmethod
from typing import List, Tuple
from enum import Enum

class Action(Enum): #플레이어 액션
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class AIPlayer(ABC): #AI 인터페이스
    def __init__(self, name: str, chips: int = 1000, difficulty_level: int = 1, strategy = None):
        self.difficulty_level = difficulty_level
        self.strategy = strategy
        self.hole_cards: List[str] = []
        self.opponent_patterns = {}  # 상대 패턴 분석 데이터

    @abstractmethod #(액션, 금액) 
    def make_decision( 
        self,
        community_cards: List[str],
        pot: int,
        current_bet: int,
        opponents: List 
    ) -> Tuple[Action, int]:  
        pass

    @abstractmethod  #강도 0.0~1.0
    def analyze_hand_strength(
        self,
        hole_cards: List[str],
        community_cards: List[str]
    ) -> float:
        pass

    def update_opponent_pattern(self, opponent , action: Action, amount: int) -> None:    
        if opponent.name not in self.opponent_patterns:
            self.opponent_patterns[opponent.name] = []

        self.opponent_patterns[opponent.name].append({
            'action': action,
            'amount': amount,
            'pot': 0 
        })