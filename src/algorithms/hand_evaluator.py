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

    def __new__(cls, value: int, korean_name: str):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.korean_name = korean_name
        return obj

    def __init__(self, value: int, korean_name: str):
        # __init__ is called after __new__, but we don't need to do anything here
        # because we set _value_ in __new__
        pass


class HandEvaluator:
    """7장의 카드로 만들 수 있는 최상의 패를 평가하는 클래스"""

    RANK_VALUES = {rank.symbol: rank.numeric_value for rank in Rank}

    @staticmethod
    def evaluate_hand(seven_cards: List[Card]) -> Tuple[HandRank, List[int], List[Card]]:
        """
        7장의 카드 중 5장을 뽑아 만들 수 있는 최상의 조합을 찾습니다.
        
        Returns:
            (HandRank, Kickers, BestHandCards)
            - HandRank: 족보 순위
            - Kickers: 타이 브레이킹을 위한 키커 목록 (높은 숫자 우선)
            - BestHandCards: 최상의 족보를 구성하는 5장의 카드
        """
        if len(seven_cards) != 7:
            raise ValueError("7장의 카드가 필요합니다.")

        best_hand_rank = HandRank.HIGH_CARD
        best_kickers = []
        best_hand_cards = []
        
        # (족보 순위, 키커) 튜플 비교용
        best_score_key = (-1, [])

        for hand_combination in combinations(seven_cards, 5):
            current_rank, kickers = HandEvaluator._evaluate_5_card_hand(list(hand_combination))
            
            # 비교: 족보 순위 우선, 그 다음 키커
            current_score_key = (current_rank.value, kickers)

            if current_score_key > best_score_key:
                best_score_key = current_score_key
                best_hand_rank = current_rank
                best_kickers = kickers
                best_hand_cards = list(hand_combination)
        
        return best_hand_rank, best_kickers, best_hand_cards

    @staticmethod
    def _evaluate_5_card_hand(five_cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """5장의 카드로 패를 평가합니다."""
        suits = [c.suit for c in five_cards]
        ranks = sorted([HandEvaluator.RANK_VALUES[c.rank.symbol] for c in five_cards], reverse=True)

        counts = {v: ranks.count(v) for v in set(ranks)}
        count_values = sorted(counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight, straight_ranks = HandEvaluator._is_straight(ranks)

        if is_flush and is_straight and straight_ranks[0] == 14: # 에이스 하이 스트레이트 플러시 (로열 플러시)
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

        # A-2-3-4-5 (Wheel) 스트레이트
        # 참고: Wheel에서 Ace는 1로 취급됩니다. 따라서 키커는 [5, 4, 3, 2, 1]이어야 합니다 (개념적으로)
        # 하지만 우리 랭크 시스템에서는 Ace가 14입니다.
        if set(ranks) >= {14, 2, 3, 4, 5}:
            return True, [5, 4, 3, 2, 1] # Ace는 낮은 값으로 취급
        for i in range(len(rank_set) - 4):
            if rank_set[i] - rank_set[i+4] == 4:
                straight_ranks = rank_set[i:i+5]
                return True, straight_ranks
        
        return False, []

    @staticmethod
    def _get_kickers(all_ranks: List[int], counts: dict, structure: List[int]) -> List[int]:
        """족보에 따른 키커를 정렬하여 반환합니다."""
        sorted_ranks = []
        # 개수별로 랭크 그룹화 (예: 페어, 트리플)
        grouped_ranks = {count: [] for count in set(counts.values())}
        for rank, count in counts.items():
            grouped_ranks[count].append(rank)
        
        for count in structure:
            # 같은 그룹 내의 랭크는 내림차순 정렬
            ranks_for_count = sorted(grouped_ranks[count], reverse=True)
            sorted_ranks.extend(ranks_for_count)
            # 중복 방지를 위해 사용된 랭크 제거
            # Note: Since we iterate through structure, we need to be careful not to remove if we need it again?
            # Actually structure like [2, 2, 1] means we take two pairs then one kicker.
            # The grouped_ranks[2] will have 2 items. We take all of them.
            
            # To be safe and correct for cases like Full House [3, 2] where we take from group 3 then group 2.
            # But what if structure is [2, 2, 1]? grouped_ranks[2] has 2 items.
            # We take the highest one first? No, for Two Pair we take both pairs.
            
            # Let's refine this logic.
            # We want to pull 'count' items from grouped_ranks[count]? No.
            # structure tells us the count of the cards we are looking for.
            # e.g. Two Pair: structure [2, 2, 1].
            # 1st '2': Find highest rank with count 2.
            # 2nd '2': Find next highest rank with count 2.
            # '1': Find highest rank with count 1.
            
            # However, for Two Pair, we might have 3 pairs in 7 cards? No, we are evaluating 5 cards here.
            # In 5 cards, Two Pair means exactly 2 ranks with count 2.
            
            # The current logic:
            # ranks_for_count = sorted(grouped_ranks[count], reverse=True)
            # sorted_ranks.extend(ranks_for_count)
            # This adds ALL ranks with that count.
            # For Two Pair [2, 2, 1], we process '2' first. grouped_ranks[2] has 2 items. We add both.
            # Then we process '2' again? We shouldn't.
            
            # Correct approach for 5-card evaluation:
            # The structure is just a hint for order, but since we are processing ALL ranks of a certain count at once,
            # we should iterate over unique counts in structure order?
            
            # Actually, for 5 cards, the counts are fixed per hand type.
            # e.g. Full House: counts are {3: [Rank1], 2: [Rank2]}.
            # structure [3, 2].
            # Loop 1 (3): take Rank1.
            # Loop 2 (2): take Rank2.
            
            # Two Pair: counts {2: [Rank1, Rank2], 1: [Rank3]}.
            # structure [2, 2, 1].
            # Loop 1 (2): take Rank1, Rank2.
            # Loop 2 (2): ... wait, we already took them.
            pass 

        # 5장 카드에 대한 단순화된 로직 (정확한 구성을 알고 있으므로):
        final_kickers = []
        
        # 중요도에 따라 개수 정렬 (보통 개수가 많을수록 중요하지만, 풀하우스는 3 > 2)
        # structure 인자는 우리가 관심 있는 개수의 순서를 알려줍니다.
        # 하지만 structure 내의 중복을 처리해야 합니다 (투페어 [2, 2, 1] 처럼).
        
        # 개수를 기반으로 재구성합니다.
        # 중요도 순으로 정렬된 랭크 리스트를 반환해야 합니다.
        
        # 개수(내림차순), 그 다음 랭크(내림차순)로 정렬
        # 이것은 풀하우스를 제외한 모든 경우에 작동합니까?
        # 풀하우스: 트리플, 그 다음 페어. (3, 2). 개수 정렬 작동함.
        # 포카드: (4, 1). 개수 정렬 작동함.
        # 트리플: (3, 1, 1). 개수 정렬 작동함.
        # 투페어: (2, 2, 1). 개수 정렬 작동함.
        # 원페어: (2, 1, 1, 1). 개수 정렬 작동함.
        # 하이카드: (1, 1, 1, 1, 1). 개수 정렬 작동함.
        
        # 따라서 (개수, 랭크)로 정렬한다면 'structure'가 굳이 필요하지 않습니다.
        
        items = []
        for rank, count in counts.items():
            items.append((count, rank))
            
        items.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        return [rank for count, rank in items for _ in range(count)]

