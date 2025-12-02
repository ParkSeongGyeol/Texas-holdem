import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.algorithms.monte_carlo import MonteCarloSimulator
import random
from collections import defaultdict
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from src.core.card import Card, Deck, Suit, Rank 
from src.algorithms.hand_evaluator import HandEvaluator



def get_game_situation(phase_card_count: int) -> Tuple[List[Card], List[Card]]:
    """
    특정 페이즈에 맞는 랜덤한 상황(내 패, 커뮤니티 카드)을 생성합니다.
    """
    deck = Deck() # 덱 생성 및 셔플 (제공된 Deck 클래스)
    
    # 1. 내 패 2장 드로우
    hero_cards = [deck.deal(), deck.deal()]
    
    # 2. 커뮤니티 카드 드로우 (페이즈에 따라 3, 4, 5장)
    community_cards = []
    for _ in range(phase_card_count):
        community_cards.append(deck.deal())
        
    return hero_cards, community_cards

def run_comprehensive_analysis(
    num_samples_per_phase: int = 100,
    mc_sims_per_hand: int = 1000,
    num_opponents: int = 1
):
    """
    플랍, 턴, 리버 페이즈에 대해 시뮬레이션을 돌리고 통계를 집계합니다.
    (프리플랍 제외)
    """
    
    # 통계 저장소: stats[Phase][HandRank] = [Equity1, Equity2, ...]
    stats: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    
    evaluator = HandEvaluator()
    simulator = MonteCarloSimulator(num_simulations=mc_sims_per_hand)

    # 분석할 페이즈 정의 (이름, 커뮤니티 카드 수)
    # 프리플랍(0장) 제외
    phases = [
        ("Flop", 3),     # 커뮤니티 카드 3장
        ("Turn", 4),     # 커뮤니티 카드 4장
        ("River", 5)     # 커뮤니티 카드 5장
    ]
    
    print(f"=== 포커 승률 분석 시작 (샘플: {num_samples_per_phase}, MC회수: {mc_sims_per_hand}) ===")

    for phase_name, card_count in phases:
        print(f"\n>> [{phase_name}] 페이즈 분석 중...")
        
        for i in range(num_samples_per_phase):
            # 1. 상황 생성 (커뮤니티 카드가 무조건 존재하는 상황)
            hero_cards, community_cards = get_game_situation(card_count)
            
            # 2. '현재 시점'의 내 핸드 랭크 확인
            # 예: 플랍에서 내가 원페어인지, 하이카드인지 식별
            current_cards = hero_cards + community_cards
            
            current_rank, _, _ = evaluator.evaluate_hand(current_cards)
            rank_name = current_rank.name # "PAIR", "HIGH_CARD", "FLUSH" 등
            
            # 3. 몬테카를로 시뮬레이션 (끝까지 갔을 때 승률 계산)
            equity = simulator.parallel_simulation(
                hole_cards=hero_cards,
                community_cards=community_cards,
                num_opponents=num_opponents,
                num_threads=4 # CPU 코어 수에 맞게 조절
            )
            
            # 4. 결과 기록
            stats[phase_name][rank_name].append(equity)
            
            # 진행률 표시 (로그가 너무 많지 않게 조절)
            if (i + 1) % 20 == 0:
                print(f"   {i + 1}/{num_samples_per_phase} 핸드 처리 완료...")

    return stats

def print_statistics(stats):
    """분석 결과를 표 형태로 예쁘게 출력합니다."""
    
    # 프리플랍 제외한 순서
    phase_order = ["Flop", "Turn", "River"]
    
    print("\n" + "="*70)
    print(f"{'PHASE':<10} | {'HAND RANK (CURRENT)':<20} | {'AVG WIN RATE':<12} | {'SAMPLES':<8}")
    print("="*70)
    
    for phase in phase_order:
        if phase not in stats: continue
        
        # 해당 페이즈의 데이터 가져오기
        rank_data = stats[phase]
        
        # 승률 높은 순으로 정렬
        sorted_ranks = sorted(
            rank_data.items(),
            key=lambda item: sum(item[1]) / len(item[1]), # 평균 승률 기준 정렬
            reverse=True
        )
        
        for rank_name, equities in sorted_ranks:
            avg_win_rate = sum(equities) / len(equities) * 100
            count = len(equities)
            
            print(f"{phase:<10} | {rank_name:<20} | {avg_win_rate:6.2f}%      | {count:<8}")
        
        print("-" * 70)

if __name__ == "__main__":
    # 실행!
    # 주의: samples=100, sims=500이면 시간이 좀 걸립니다.
    # 테스트 할 때는 숫자를 줄여서 돌려보세요.
    result_stats = run_comprehensive_analysis(
        num_samples_per_phase=1000,   # 페이즈당 50가지 상황 테스트
        mc_sims_per_hand=10000,       # 각 상황당 500번 시뮬레이션 (정확도)
        num_opponents=1             # 1:1 Heads-up
    )
    
    print_statistics(result_stats)