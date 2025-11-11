"""
몬테카를로 시뮬레이션 - 박우현 담당
승률 계산 및 병렬 처리
"""

import random
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from src.core.card import Card, Deck
from src.algorithms.hand_evaluator import HandEvaluator


class MonteCarloSimulator:
    """몬테카를로 시뮬레이션 클래스"""

    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations
        self.evaluator = HandEvaluator()


    def calculate_win_probability(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int = 1
    ) -> float:
        """
        승률 계산
        Returns: 0.0~1.0 사이의 승률
        """
        # TODO: 몬테카를로 시뮬레이션 구현 (박우현)
        # 1. 남은 카드로 가능한 시나리오 생성
        # 2. 각 시나리오에서 승부 결과 계산
        # 3. 승률 통계 산출

        wins = 0
        for _ in range(self.num_simulations):
            if self._simulate_hand(hole_cards, community_cards, num_opponents):
                wins += 1

        return wins / self.num_simulations

    def _simulate_hand(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> bool:
        """단일 핸드 시뮬레이션"""
        
        # TODO: 단일 시뮬레이션 로직 구현 (박우현)
        # 임시 구현: 랜덤 승부

          # 덱 초기화 및 남은 카드 계산
        deck = Deck()
        remaining_cards = [
            c for c in deck.cards if c not in hole_cards + community_cards
        ]
        random.shuffle(remaining_cards)

         # 상대방에게 홀카드 분배
        opponents = []
        for _ in range(num_opponents):
            opponents.append([remaining_cards.pop(), remaining_cards.pop()])

         # 남은 커뮤니티 카드 보충
        missing_count = 5 - len(community_cards)
        full_community = community_cards + [remaining_cards.pop() for _ in range(missing_count)]

         # 내 핸드 평가 
        my_rank = self.evaluator.evaluate_hand(hole_cards + full_community)

         # 상대방 핸드 평가 및 비교 
        for opp_cards in opponents:
            opp_rank = self.evaluator.evaluate_hand(opp_cards + full_community)
            if opp_rank > my_rank :
                return False  # 상대가 더 강함

        return True  # 내가 이김

    def parallel_simulation(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int = 1,
        num_threads: int = 4
    ) -> float:
        """병렬 처리를 통한 빠른 시뮬레이션"""
        # TODO: 병렬 처리 몬테카를로 구현 (박우현)
        simulations_per_thread = self.num_simulations // num_threads

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for _ in range(num_threads):
                future = executor.submit(
                    self._run_simulations,
                    hole_cards,
                    community_cards,
                    num_opponents,
                    simulations_per_thread
                )
                futures.append(future)

            total_wins = sum(future.result() for future in futures)

        return total_wins / self.num_simulations

    def _run_simulations(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int,
        num_sims: int
    ) -> int:
        """스레드별 시뮬레이션 실행"""
        wins = 0
        for _ in range(num_sims):
            if self._simulate_hand(hole_cards, community_cards, num_opponents):
                wins += 1
        return wins
    



if __name__ == "__main__":
    simulator = MonteCarloSimulator(num_simulations=1000)

    # 예시: 내 패 = A♠, K♠ / 커뮤니티 카드 3장
    hole_cards = [Card('A', '♠'), Card('K', '♠')]
    community_cards = [Card('Q', '♠'), Card('J', '♠'), Card('2', '♦')]

    win_rate_single = simulator.calculate_win_probability(
        hole_cards, community_cards, num_opponents=2
    )

    win_rate_parallel = simulator.parallel_simulation(
        hole_cards, community_cards, num_opponents=2, num_threads=4
    )

    print(f"단일 스레드 승률: {win_rate_single:.2%}")
    print(f"병렬 스레드 승률: {win_rate_parallel:.2%}")
