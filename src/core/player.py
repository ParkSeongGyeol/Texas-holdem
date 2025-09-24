"""
플레이어 클래스 - 박성결 담당
플레이어 상태 관리 및 게임 진행 로직
"""

from typing import List
from src.core.card import Card


class Player:
    """포커 플레이어 클래스"""

    def __init__(self, name: str, chips: int = 1000):
        self.name = name
        self.chips = chips
        self.hand: List[Card] = []
        self.current_bet = 0
        self.is_active = True
        self.has_folded = False
        self.is_all_in = False

    def receive_card(self, card: Card) -> None:
        """카드 받기"""
        self.hand.append(card)

    def bet(self, amount: int) -> int:
        """베팅 - 실제 베팅된 금액 반환"""
        if amount > self.chips:
            # All-in
            actual_bet = self.chips
            self.is_all_in = True
        else:
            actual_bet = amount

        self.chips -= actual_bet
        self.current_bet += actual_bet
        return actual_bet

    def fold(self) -> None:
        """폴드"""
        self.has_folded = True
        self.is_active = False

    def reset_for_new_hand(self) -> None:
        """새 핸드를 위한 플레이어 상태 리셋"""
        self.hand = []
        self.current_bet = 0
        self.has_folded = False
        self.is_all_in = False
        self.is_active = self.chips > 0

    def can_bet(self, amount: int) -> bool:
        """베팅 가능 여부 확인"""
        return self.chips >= amount and self.is_active and not self.has_folded

    def __str__(self) -> str:
        hand_str = ", ".join([str(card) for card in self.hand])
        return f"{self.name} ({self.chips} chips): {hand_str}"

    def __repr__(self) -> str:
        return f"Player(name={self.name}, chips={self.chips})"