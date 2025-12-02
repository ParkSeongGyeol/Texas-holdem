import time
from typing import List, Dict
from collections import defaultdict
from src.core.card import Card, Deck, Suit, Rank
from src.algorithms.hand_evaluator import HandEvaluator
from src.algorithms.monte_carlo import MonteCarloSimulator

# =========================================================
# [설정] 시뮬레이션 파라미터
# =========================================================
# 각 족보별로 몇 개의 샘플 상황을 만들 것인지
# (희귀 족보는 생성 자체가 오래 걸리므로 숫자를 작게 잡는 것을 추천)
SAMPLES_PER_RANK = 150  

# 각 샘플당 몬테카를로 시뮬레이션 횟수 (정확도)
MC_SIMULATIONS = 20000 

# 상황 생성 시 최대 재시도 횟수 (이 횟수 안에 해당 족보가 안 나오면 Skip)
MAX_GENERATION_ATTEMPTS = 50000 
# =========================================================

# 분석할 족보 목록 (낮은 순 -> 높은 순)
TARGET_RANKS = [
    "HIGH_CARD",
    "ONE_PAIR",
    "TWO_PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT",
    "FLUSH",
    "FULL_HOUSE",
    "FOUR_OF_A_KIND",
    "STRAIGHT_FLUSH"
]

# 분석할 페이즈 목록
TARGET_PHASES = ["Flop", "Turn", "River"]

def get_card_count(phase: str) -> int:
    if phase == "Flop": return 3
    elif phase == "Turn": return 4
    elif phase == "River": return 5
    return 0

def generate_specific_scenario(phase: str, target_rank: str) -> tuple:
    """
    무작위로 카드를 섞어 조건(phase, target_rank)에 맞는 상황을 찾습니다.
    (Rejection Sampling 방식)
    """
    evaluator = HandEvaluator()
    card_count = get_card_count(phase)
    
    for _ in range(MAX_GENERATION_ATTEMPTS):
        deck = Deck()
        hero_cards = [deck.deal(), deck.deal()]
        community_cards = [deck.deal() for _ in range(card_count)]
        
        # 족보 확인
        current_rank, _, _ = evaluator.evaluate_hand(hero_cards + community_cards)
        
        if current_rank.name == target_rank:
            return hero_cards, community_cards
            
    return None, None  # 실패 시 None 반환

def run_all_simulations():
    simulator = MonteCarloSimulator(num_simulations=MC_SIMULATIONS)
    
    # 결과 저장소: results[Phase][Rank] = 평균 승률
    results = defaultdict(dict)
    
    print(f"=== 포커 전수 조사 시뮬레이션 시작 ===")
    print(f"설정: 랭크별 샘플 {SAMPLES_PER_RANK}개, MC 시뮬레이션 {MC_SIMULATIONS}회")
    print(f"제한: 족보 생성 시도 {MAX_GENERATION_ATTEMPTS}회 초과 시 건너뜀")
    print("=" * 70)

    start_time = time.time()

    for phase in TARGET_PHASES:
        print(f"\n[[ {phase} Phase 분석 중... ]]")
        print(f"{'Rank Name':<20} | {'Found':<5} | {'Avg Win Rate':<15} | {'Note'}")
        print("-" * 65)
        
        for rank_name in TARGET_RANKS:
            equities = []
            
            # 샘플 수집 루프
            for _ in range(SAMPLES_PER_RANK):
                hero_cards, community_cards = generate_specific_scenario(phase, rank_name)
                
                if hero_cards:
                    # 시뮬레이션 실행
                    equity = simulator.parallel_simulation(
                        hole_cards=hero_cards,
                        community_cards=community_cards,
                        num_opponents=1,
                        num_threads=4
                    )
                    equities.append(equity)
                else:
                    # 생성 실패 (너무 희귀한 족보)
                    pass
            
            # 결과 집계 및 출력
            if equities:
                avg_equity = sum(equities) / len(equities) * 100
                results[phase][rank_name] = avg_equity
                note = ""
                if avg_equity > 90: note = "Very Strong"
                elif avg_equity < 30: note = "Weak"
                
                print(f"{rank_name:<20} | {len(equities):<5} | {avg_equity:6.2f}%        | {note}")
            else:
                print(f"{rank_name:<20} | 0     |   ---- %        | (Too Rare to Gen)")

    end_time = time.time()
    
    # === 최종 요약 리포트 ===
    print("\n" + "="*70)
    print("FINAL SUMMARY REPORT")
    print("="*70)
    print(f"{'Rank':<18} | {'Flop Win%':<12} | {'Turn Win%':<12} | {'River Win%':<12}")
    print("-" * 70)
    
    for rank in TARGET_RANKS:
        flop_rate = f"{results['Flop'].get(rank, 0):.1f}%" if rank in results['Flop'] else "-"
        turn_rate = f"{results['Turn'].get(rank, 0):.1f}%" if rank in results['Turn'] else "-"
        river_rate = f"{results['River'].get(rank, 0):.1f}%" if rank in results['River'] else "-"
        
        print(f"{rank:<18} | {flop_rate:<12} | {turn_rate:<12} | {river_rate:<12}")
        
    print("-" * 70)
    print(f"Total Runtime: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    run_all_simulations()