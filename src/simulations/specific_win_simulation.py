import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import time
from typing import List, Tuple, Dict
from src.core.card import Card, Deck, Suit, Rank
from src.algorithms.hand_evaluator import HandEvaluator
from src.algorithms.monte_carlo import MonteCarloSimulator

# =========================================================
# 1. 사용자 설정 구간 (여기만 바꾸면 됩니다!)
# =========================================================
TARGET_PHASE = "Flop"       # "Flop" (3장), "Turn" (4장), "River" (5장)
TARGET_RANK_NAME = "TWO_PAIR"  # 찾고 싶은 족보 이름 (대문자)
                            # 예: "HIGH_CARD", "ONE_PAIR", "TWO_PAIR", "THREE_OF_A_KIND",
                            #     "STRAIGHT", "FLUSH", "FULL_HOUSE", "FOUR_OF_A_KIND", "STRAIGHT_FLUSH"

NUM_TEST_CASES = 300       # 해당 조건의 상황을 몇 번이나 만들어서 테스트할지
MC_SIMULATIONS = 20000       # 각 상황마다 돌릴 몬테카를로 시뮬레이션 횟수
# =========================================================


def get_card_count_by_phase(phase_name: str) -> int:
    if phase_name == "Flop": return 3
    elif phase_name == "Turn": return 4
    elif phase_name == "River": return 5
    else: raise ValueError("Phase must be 'Flop', 'Turn', or 'River'")

def generate_scenario_with_condition(
    target_phase: str, 
    target_rank_name: str, 
    max_attempts: int = 100000
) -> Tuple[List[Card], List[Card], str]:
    """
    원하는 족보가 나올 때까지 무한정 카드를 다시 뽑는 함수 (Rejection Sampling)
    """
    evaluator = HandEvaluator()
    deck = Deck() # 덱은 루프 안에서 매번 새로 생성해야 함 (섞기 위함)
    
    card_count = get_card_count_by_phase(target_phase)
    
    for attempt in range(max_attempts):
        deck = Deck() # 새 덱
        
        # 1. 내 패 2장
        hero_cards = [deck.deal(), deck.deal()]
        
        # 2. 커뮤니티 카드 (페이즈에 맞게)
        community_cards = [deck.deal() for _ in range(card_count)]
        
        # 3. 족보 확인
        current_cards = hero_cards + community_cards
        current_rank, _, _ = evaluator.evaluate_hand(current_cards)
        
        # 4. 조건 검사 (Enum의 이름과 문자열 비교)
        if current_rank.name == target_rank_name:
            # 찾았다!
            return hero_cards, community_cards, current_rank.name
            
    raise TimeoutError(f"Failed to generate {target_rank_name} in {target_phase} phase after {max_attempts} attempts.")

def run_targeted_analysis():
    simulator = MonteCarloSimulator(num_simulations=MC_SIMULATIONS)
    
    print(f"=== [타겟 분석 모드] ===")
    print(f"설정: [{TARGET_PHASE}] 페이즈에서 내 패가 [{TARGET_RANK_NAME}]인 상황 분석")
    print(f"케이스 생성 수: {NUM_TEST_CASES}, 케이스 당 시뮬레이션: {MC_SIMULATIONS}회")
    print("-" * 60)
    
    results = []
    
    start_total = time.time()
    
    for i in range(NUM_TEST_CASES):
        try:
            # 1. 조건에 맞는 상황 생성
            # (희귀한 족보일수록 이 단계에서 시간이 걸릴 수 있습니다)
            hero_cards, community_cards, rank_name = generate_scenario_with_condition(
                TARGET_PHASE, TARGET_RANK_NAME
            )
            
            # 2. 시뮬레이션 실행 (병렬 처리)
            equity = simulator.parallel_simulation(
                hole_cards=hero_cards,
                community_cards=community_cards,
                num_opponents=1,
                num_threads=4
            )
            
            results.append(equity)
            
            # 3. 개별 결과 출력 (옵션)
            print(f"Case {i+1:02d}: {hero_cards} + {community_cards} -> 승률: {equity*100:6.2f}%")
            
        except TimeoutError as e:
            print(f"Case {i+1:02d}: 생성 실패 (너무 희귀한 확률입니다)")
        except Exception as e:
            print(f"Error: {e}")

    end_total = time.time()
    
    # === 최종 통계 출력 ===
    if results:
        avg_equity = sum(results) / len(results) * 100
        min_equity = min(results) * 100
        max_equity = max(results) * 100
        
        print("=" * 60)
        print(f"분석 결과 요약 ({TARGET_PHASE} / {TARGET_RANK_NAME})")
        print("=" * 60)
        print(f"평균 승률 (Average Equity) : {avg_equity:.2f}%")
        print(f"최저 승률 (Min Equity)     : {min_equity:.2f}% (상대방 패가 잘 붙은 경우)")
        print(f"최고 승률 (Max Equity)     : {max_equity:.2f}% (가장 유리했던 상황)")
        print(f"총 소요 시간               : {end_total - start_total:.2f}초")
        print("=" * 60)
        
        # 인사이트 제공
        if avg_equity > 80:
            print(">> [Insight] 매우 강력한 상황입니다. 밸류 베팅을 적극 추천합니다.")
        elif avg_equity > 50:
            print(">> [Insight] 유리하지만 역전 가능성이 있습니다. 상대 액션을 주의하세요.")
        else:
            print(">> [Insight] 메이드 되었으나 생각보다 승률이 낮습니다. 키커 문제이거나 역전패 가능성이 높습니다.")
            
    else:
        print("데이터를 생성하지 못했습니다.")

if __name__ == "__main__":
    
    
    
    run_targeted_analysis()

      
    TARGET_PHASE = "Turn"     
   

    run_targeted_analysis()

 
    TARGET_PHASE = "River"       
   

    run_targeted_analysis()