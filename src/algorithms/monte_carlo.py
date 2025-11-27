import random
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
from src.core.card import Card, Deck, Suit, Rank 
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
        승률 계산 (단일 스레드)
        Returns: 0.0 ~ 1.0 사이의 승률
        """
        total_score = 0.0
        
        for _ in range(self.num_simulations):
            # 1.0(승), 0.5(무), 0.0(패) 점수를 바로 누적합니다.
            total_score += self._simulate_hand(hole_cards, community_cards, num_opponents)
        
        return total_score / self.num_simulations

    def _simulate_hand(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> float:
        """
        단일 핸드 시뮬레이션
        Returns: 1.0 (Win), 0.5 (Tie), 0.0 (Lose)
        """
        
        deck = Deck()
        
        # 이미 나와있는 카드(내 패 + 커뮤니티)를 덱에서 제거
        # Deck 클래스의 self.cards 리스트를 활용하여 남은 카드를 필터링합니다.
        known_cards = set(hole_cards + community_cards)
        
        # __eq__가 구현된 Card 클래스 덕분에 set과 list comprehension으로 필터링 가능
        remaining_cards = [c for c in deck.cards if c not in known_cards]
        random.shuffle(remaining_cards)

        # 상대방에게 홀카드 분배
        opponents_hands = []
        for _ in range(num_opponents):
            if len(remaining_cards) < 2: # 남은 카드가 부족하면 중단(안전장치)
                break
            op_card1 = remaining_cards.pop()
            op_card2 = remaining_cards.pop()
            opponents_hands.append([op_card1, op_card2])

        # 남은 커뮤니티 카드 보충 (총 5장이 되도록)
        current_community = community_cards[:] 
        missing_count = 5 - len(current_community) 
        
        for _ in range(missing_count):
            if remaining_cards:
                current_community.append(remaining_cards.pop()) 

        # 내 핸드 평가
        # evaluate_hand 반환값: (HandRank, Kickers, BestHandCards)
        my_rank, my_kickers, _ = self.evaluator.evaluate_hand(hole_cards + current_community)
        
        # 비교를 위해 (족보 값, 키커 리스트) 튜플 생성
        # HandRank Enum은 .value로 정수값 비교, Kickers는 리스트 자체로 사전순 비교 가능
        my_score_key = (my_rank.value, my_kickers)

        # 상대방 핸드 평가 및 승패 결정
        is_tie = False 
        
        for opp_hand in opponents_hands: 
            opp_rank, opp_kickers, _ = self.evaluator.evaluate_hand(opp_hand + current_community) 
            opp_score_key = (opp_rank.value, opp_kickers) 
            
            # 파이썬 튜플 비교: 첫 번째 요소(족보) 비교 -> 같으면 두 번째 요소(키커) 비교
            if opp_score_key > my_score_key:
                return 0.0  # 상대방 승리 (패배)
            elif opp_score_key == my_score_key:
                is_tie = True # 동점 발생 (잠재적 무승부)

        if is_tie:
            return 0.5 # 무승부
        else:
            return 1.0 # 승리

    def parallel_simulation(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int = 1,
        num_threads: int = 4
    ) -> float:
        """병렬 처리를 통한 빠른 시뮬레이션"""
        
        simulations_per_thread = self.num_simulations // num_threads
        remainder = self.num_simulations % num_threads

        futures = []
        total_score = 0.0

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i in range(num_threads):
                count = simulations_per_thread + (1 if i < remainder else 0)
                
                future = executor.submit(  
                    self._run_simulations, 
                    hole_cards,
                    community_cards,
                    num_opponents,
                    count
                )
                futures.append(future)

            for future in futures:
                total_score += future.result()

        return total_score / self.num_simulations

    def _run_simulations(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int,
        num_sims: int
    ) -> float:
        """스레드 내부에서 실행되는 시뮬레이션 루프"""
        local_score = 0.0
        for _ in range(num_sims):
            local_score += self._simulate_hand(hole_cards, community_cards, num_opponents)
        return local_score

if __name__ == "__main__":
    # 테스트 실행 코드
    simulator = MonteCarloSimulator(num_simulations=1000)
    
    # 제공된 Card 클래스는 Card(Suit, Rank) 생성자를 사용합니다.
    # 예시: 내 패 = A♠, K♠
    my_hole_cards = [
        Card(Suit.SPADES, Rank.ACE), 
        Card(Suit.SPADES, Rank.KING)
    ]
    
    # 커뮤니티 카드: Q♠, J♠, 2♦
    current_community = [
        Card(Suit.SPADES, Rank.QUEEN), 
        Card(Suit.SPADES, Rank.JACK), 
        Card(Suit.DIAMONDS, Rank.TWO)
    ]

    print(f"--- 시뮬레이션 시작 (횟수: {simulator.num_simulations}) ---")
    print(f"내 패: {my_hole_cards}")
    print(f"커뮤니티: {current_community}")
    
    # 1. 단일 스레드 실행
    win_rate_single = simulator.calculate_win_probability(
        my_hole_cards, current_community, num_opponents=1
    )
    print(f"단일 스레드 승률 (Equity): {win_rate_single:.2%}")

    # 2. 병렬 스레드 실행
    win_rate_parallel = simulator.parallel_simulation(
        my_hole_cards, current_community, num_opponents=1, num_threads=4
    )
    print(f"병렬 스레드 승률 (Equity): {win_rate_parallel:.2%}")