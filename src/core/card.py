"""
카드 시스템 - 문현준 담당
Card/Deck 클래스 및 Fisher-Yates 셔플 알고리즘
"""

from enum import Enum
from typing import List
import random


class Suit(Enum):
    """카드 무늬"""
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class Rank(Enum):
    """카드 랭크"""
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __init__(self, numeric_value: int, symbol: str):
        self._numeric_value = numeric_value
        self._symbol = symbol

    @property
    def numeric_value(self) -> int:
        """카드의 숫자 값 (2-14)"""
        return self._numeric_value

    @property
    def symbol(self) -> str:
        """카드의 기호 표현"""
        return self._symbol


class Card:
    """포커 카드 클래스"""

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __str__(self) -> str:
        return f"{self.suit.value}{self.rank.symbol}"

    def __repr__(self) -> str:
        return f"Card({self.suit.name}, {self.rank.name})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))


class Deck:
    """포커 덱 클래스 - Fisher-Yates 셔플 알고리즘 구현"""

    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        """덱을 초기 상태로 리셋"""
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self) -> None:
        """Fisher-Yates 셔플 알고리즘 - O(n) 복잡도"""
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """카드 한 장 뽑기"""
        return self.cards.pop() if self.cards else None

    def is_empty(self) -> bool:
        """덱이 비어있는지 확인"""
        return len(self.cards) == 0

    def cards_left(self) -> int:
        """남은 카드 수"""
        return len(self.cards)
