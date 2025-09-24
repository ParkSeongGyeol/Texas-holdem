"""
족보 판정 알고리즘 - 문현준 담당
비트마스킹을 활용한 O(1) 족보 판정
"""

from typing import List, Tuple
from enum import Enum

from src.core.card import Card, Rank, Suit


class HandRank(Enum):
    """포커 족보 순위"""
    HIGH_CARD = (1, "하이카드")
    PAIR = (2, "원페어")
    TWO_PAIR = (3, "투페어")
    THREE_KIND = (4, "트리플")
    STRAIGHT = (5, "스트레이트")
    FLUSH = (6, "플러시")
    FULL_HOUSE = (7, "풀하우스")
    FOUR_KIND = (8, "포카드")
    STRAIGHT_FLUSH = (9, "스트레이트 플러시")
    ROYAL_FLUSH = (10, "로열 플러시")

    def __init__(self, value: int, korean_name: str):
        self.value = value
        self.korean_name = korean_name


class HandEvaluator:
    """핸드 평가기 - 비트마스킹 활용"""

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """
        7장의 카드에서 최고 족보 평가
        Returns: (족보, 키커들)
        """
        if len(cards) != 7:
            raise ValueError("7장의 카드가 필요합니다")

        # TODO: 비트마스킹을 활용한 족보 판정 알고리즘 구현 (문현준)
        # 1. C(7,5) = 21가지 조합 생성
        # 2. 각 조합에 대해 족보 판정
        # 3. 최고 족보 반환

        # 임시 구현
        return HandRank.HIGH_CARD, [14, 13, 12, 11, 10]

    @staticmethod
    def is_flush(cards: List[Card]) -> bool:
        """플러시 여부 확인"""
        # TODO: 비트마스킹으로 플러시 판정 (문현준)
        suits = [card.suit for card in cards]
        return len(set(suits)) == 1

    @staticmethod
    def is_straight(ranks: List[int]) -> bool:
        """스트레이트 여부 확인"""
        # TODO: 비트마스킹으로 스트레이트 판정 (문현준)
        sorted_ranks = sorted(set(ranks))
        if len(sorted_ranks) < 5:
            return False

        # 연속된 5장 확인
        for i in range(len(sorted_ranks) - 4):
            if sorted_ranks[i+4] - sorted_ranks[i] == 4:
                return True

        # A-2-3-4-5 스트레이트 (백스트레이트) 확인
        if sorted_ranks == [2, 3, 4, 5, 14]:
            return True

        return False

    @staticmethod
    def compare_hands(
        hand1: Tuple[HandRank, List[int]],
        hand2: Tuple[HandRank, List[int]]
    ) -> int:
        """
        두 핸드 비교
        Returns: 1 (hand1 승), -1 (hand2 승), 0 (무승부)
        """
        # TODO: 상세한 핸드 비교 로직 구현 (문현준)
        rank1, kickers1 = hand1
        rank2, kickers2 = hand2

        if rank1.value > rank2.value:
            return 1
        elif rank1.value < rank2.value:
            return -1
        else:
            # 같은 족보일 때 키커 비교
            for k1, k2 in zip(kickers1, kickers2):
                if k1 > k2:
                    return 1
                elif k1 < k2:
                    return -1
            return 0