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
    deck = Deck() # 덱 생성 및 셔플 (Provided Deck class)
    
    # 1. 내 패 2장 드로우
    hero_cards = [deck.deal(), deck.deal()]
    
    # 2. 커뮤니티 카드 드로우 (페이즈에 따라 0, 3, 4, 5장)
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
    모든 페이즈(Pre-Flop ~ River)에 대해 시뮬레이션을 돌리고 통계를 집계합니다.
    """
    
    # 통계 저장소: stats[Phase][HandRank] = [Equity1, Equity2, ...]
    stats: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    
    evaluator = HandEvaluator()
    simulator = MonteCarloSimulator(num_simulations=mc_sims_per_hand)

    # 분석할 페이즈 정의 (이름, 커뮤니티 카드 수)
    phases = [
        ("Pre-Flop", 0), # 커뮤니티 카드 없음
        ("Flop", 3),     # 커뮤니티 카드 3장
        ("Turn", 4),     # 커뮤니티 카드 4장
        ("River", 5)     # 커뮤니티 카드 5장
    ]
    
    print(f"=== 포커 승률 분석 시작 (샘플: {num_samples_per_phase}, MC회수: {mc_sims_per_hand}) ===")

    for phase_name, card_count in phases:
        print(f"\n>> Analyzing [{phase_name}] Phase...")
        
        for i in range(num_samples_per_phase):
            # 1. 상황 생성
            hero_cards, community_cards = get_game_situation(card_count)
            
            # 2. '현재 시점'의 내 핸드 랭크 확인
            # 예: 플랍에서 내가 원페어인지, 하이카드인지 식별
            current_cards = hero_cards + community_cards
            
            # 프리플랍의 경우 랭크가 무조건 High Card로 나올 수 있으므로, 
            # 포켓 페어(AA, KK 등)인지를 구분하는 로직을 추가하면 더 좋습니다.
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
                print(f"   Processed {i + 1}/{num_samples_per_phase} hands...")

    return stats

def print_statistics(stats):
    """분석 결과를 표 형태로 예쁘게 출력합니다."""
    
    phase_order = ["Pre-Flop", "Flop", "Turn", "River"]
    
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
    # 주의: samples=100, sims=500이면 총 200,000번의 게임을 시뮬레이션 하므로 시간이 좀 걸립니다.
    # 테스트 할 때는 숫자를 줄여서 돌려보세요.
    result_stats = run_comprehensive_analysis(
        num_samples_per_phase=50,   # 페이즈당 50가지 상황 테스트
        mc_sims_per_hand=500,       # 각 상황당 500번 시뮬레이션 (정확도)
        num_opponents=1             # 1:1 Heads-up
    )
    
    print_statistics(result_stats)

# ### 2. 코드 작동 원리 설명

# 1.  **`get_game_situation` 함수:**
#     * 제공해주신 `Deck` 클래스를 사용하여 덱을 셔플하고, `deal()` 메서드로 카드를 뽑습니다.
#     * 페이즈(`phase_card_count`)에 맞춰 커뮤니티 카드가 0장(프리플랍), 3장(플랍), 4장(턴), 5장(리버)인 상황을 만듭니다.

# 2.  **`run_comprehensive_analysis` 함수 (핵심 로직):**
#     * `phases` 리스트를 순회하며 게임의 4단계 진행 상황을 시뮬레이션합니다.
#     * **현재 상태 평가 (`evaluator.evaluate_hand`):** 시뮬레이션을 돌리기 전에, **"지금 내가 뭘 들고 있는지"**를 먼저 판단합니다. 이것이 통계의 기준(Key)이 됩니다.
#     * **미래 예측 (`simulator.parallel_simulation`):** 현재 패를 가지고 게임이 끝까지(쇼다운) 진행되었을 때의 승률을 계산합니다.

# 3.  **결과 해석 (`print_statistics`):**
#     * 출력된 표는 다음과 같이 해석합니다.
#     * `Flop | THREE_OF_A_KIND | 82.50%`: "플랍에 트리플(셋)이 되었을 때, 리버까지 가서 이길 확률은 평균 82.5%이다."
#     * `Turn | FLUSH_DRAW (High Card) | 18.00%`: (코드엔 없지만) 이런 식으로 드로우 확률도 나중에 로직을 추가하여 분석할 수 있습니다.

# ### 3. 개선 팁 (Pre-Flop)

# 현재 코드에서 **Pre-Flop** 단계는 커뮤니티 카드가 없으므로, `HandEvaluator`는 대부분 `HIGH_CARD` 또는 `PAIR`(포켓 페어)로만 인식합니다.

# 프리플랍 통계를 더 디테일하게 보고 싶다면(예: AK vs 27), `rank_name`을 결정하는 부분에 아래와 같은 예외 처리를 추가하면 좋습니다.

# ```python
# # run_comprehensive_analysis 함수 내부




# current_rank, _, _ = evaluator.evaluate_hand(current_cards)
# rank_name = current_rank.name

# # [프리플랍 전용 로직] 핸드 랭크 대신 'AA', 'AKs' 같은 핸드 타입을 기록
# if phase_name == "Pre-Flop":
#     c1, c2 = sorted(hero_cards, key=lambda c: c.rank.value, reverse=True)
#     is_suited = 's' if c1.suit == c2.suit else 'o'
#     if c1.rank == c2.rank: # 포켓 페어
#         rank_name = f"Pocket {c1.rank.symbol}{c1.rank.symbol}"
#     else:
#         rank_name = f"{c1.rank.symbol}{c2.rank.symbol}{is_suited}"