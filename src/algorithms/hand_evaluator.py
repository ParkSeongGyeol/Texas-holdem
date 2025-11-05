"""
족보 판정 알고리즘 - 문현준 담당
C(7,5) 조합을 통한 족보 판정
"""

from typing import List, Tuple
from enum import Enum
from itertools import combinations

from src.core.card import Card, Rank


class HandRank(Enum):
    """포커 족보 순위"""
    HIGH_CARD = (1, "하이카드")
    ONE_PAIR = (2, "원페어")
    TWO_PAIR = (3, "투페어")
    THREE_OF_A_KIND = (4, "트리플")
    STRAIGHT = (5, "스트레이트")
    FLUSH = (6, "플러시")
    FULL_HOUSE = (7, "풀하우스")
    FOUR_OF_A_KIND = (8, "포카드")
    STRAIGHT_FLUSH = (9, "스트레이트 플러시")
    ROYAL_FLUSH = (10, "로열 플러시")

    def __init__(self, value: int, korean_name: str):
        self.value = value
        self.korean_name = korean_name


class HandEvaluator:
    """7장의 카드로 만들 수 있는 최상의 패를 평가하는 클래스"""

    RANK_VALUES = {rank.symbol: rank.numeric_value for rank in Rank}

    @staticmethod
    def evaluate_hand(seven_cards: List[Card]) -> Tuple[HandRank, List[Card]]:
        """7장의 카드 중 5장을 뽑아 만들 수 있는 최상의 조합을 찾습니다."""
        if len(seven_cards) != 7:
            raise ValueError("7장의 카드가 필요합니다.")

        best_hand_rank = HandRank.HIGH_CARD
        best_hand_cards = []
        best_hand_score = (0, [])

        for hand_combination in combinations(seven_cards, 5):
            current_rank, score_values = HandEvaluator._evaluate_5_card_hand(list(hand_combination))
            score = (current_rank.value, score_values)

            if score > best_hand_score:
                best_hand_score = score
                best_hand_rank = current_rank
                best_hand_cards = list(hand_combination)
        
        return best_hand_rank, best_hand_cards

    @staticmethod
    def _evaluate_5_card_hand(five_cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """5장의 카드로 패를 평가합니다."""
        suits = [c.suit for c in five_cards]
        ranks = sorted([HandEvaluator.RANK_VALUES[c.rank.symbol] for c in five_cards], reverse=True)

        counts = {v: ranks.count(v) for v in set(ranks)}
        count_values = sorted(counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight, straight_ranks = HandEvaluator._is_straight(ranks)

        if is_flush and is_straight and ranks[0] == 14: # Ace-high straight flush
            return HandRank.ROYAL_FLUSH, straight_ranks
        if is_flush and is_straight:
            return HandRank.STRAIGHT_FLUSH, straight_ranks
        if 4 in count_values:
            return HandRank.FOUR_OF_A_KIND, HandEvaluator._get_kickers(ranks, counts, [4, 1])
        if count_values == [3, 2]:
            return HandRank.FULL_HOUSE, HandEvaluator._get_kickers(ranks, counts, [3, 2])
        if is_flush:
            return HandRank.FLUSH, ranks
        if is_straight:
            return HandRank.STRAIGHT, straight_ranks
        if 3 in count_values:
            return HandRank.THREE_OF_A_KIND, HandEvaluator._get_kickers(ranks, counts, [3, 1, 1])
        if count_values == [2, 2, 1]:
            return HandRank.TWO_PAIR, HandEvaluator._get_kickers(ranks, counts, [2, 2, 1])
        if 2 in count_values:
            return HandRank.ONE_PAIR, HandEvaluator._get_kickers(ranks, counts, [2, 1, 1, 1])
        
        return HandRank.HIGH_CARD, ranks

    @staticmethod
    def _is_straight(ranks: List[int]) -> Tuple[bool, List[int]]:
        """스트레이트 여부를 확인하고, 스트레이트를 구성하는 랭크를 반환합니다."""
        rank_set = sorted(list(set(ranks)), reverse=True)
        if len(rank_set) < 5:
            return False, []

        # A-2-3-4-5 (Wheel) straight
        if set(ranks) >= {14, 2, 3, 4, 5}:
            return True, [5, 4, 3, 2, 1] # Ace is low

        for i in range(len(rank_set) - 4):
            if rank_set[i] - rank_set[i+4] == 4:
                straight_ranks = rank_set[i:i+5]
                return True, straight_ranks
        
        return False, []

    @staticmethod
    def _get_kickers(all_ranks: List[int], counts: dict, structure: List[int]) -> List[int]:
        """족보에 따른 키커를 정렬하여 반환합니다."""
        sorted_ranks = []
        # Group ranks by their counts (e.g., pairs, three of a kind)
        grouped_ranks = {count: [] for count in set(counts.values())}
        for rank, count in counts.items():
            grouped_ranks[count].append(rank)
        
        for count in structure:
            # Ranks within the same group should be sorted high to low
            ranks_for_count = sorted(grouped_ranks[count], reverse=True)
            sorted_ranks.extend(ranks_for_count)
            # Remove used ranks to avoid duplication
            for rank in ranks_for_count:
                grouped_ranks[count].remove(rank)

        return sorted_ranks
