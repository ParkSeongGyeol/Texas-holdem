import time
from typing import List
from concurrent.futures import ThreadPoolExecutor
from src.core.card import Card, Deck, Suit, Rank
from src.algorithms.hand_evaluator import HandEvaluator
from src.algorithms.monte_carlo import MonteCarloSimulator


def run_preflop_analysis(num_simulations=1000, num_opponents=1):
    """
    제공된 Card/Deck 클래스를 사용하여 모든 프리플랍 핸드(169개) 승률 분석
    """
    # 시뮬레이터 인스턴스 생성
    simulator = MonteCarloSimulator(num_simulations=num_simulations)
    
    # Rank Enum을 numeric_value 기준 내림차순 정렬 (ACE(14) -> TWO(2))
    # 이렇게 하면 자동으로 A, K, Q ... 2 순서가 됩니다.
    sorted_ranks = sorted(list(Rank), key=lambda r: r.numeric_value, reverse=True)
    
    results = []
    
    print(f"=== 프리플랍 승률 분석 시작 (Sims: {num_simulations}, Opponents: {num_opponents}) ===")
    start_time = time.time()

    # 이중 루프로 모든 핸드 조합 생성 (13 * 13 로직)
    for i in range(len(sorted_ranks)):
        for j in range(i, len(sorted_ranks)):
            rank1 = sorted_ranks[i]
            rank2 = sorted_ranks[j]
            
            # Rank Enum의 symbol 프로퍼티 사용 (예: "A", "K", "10")
            char1 = rank1.symbol
            char2 = rank2.symbol

            # 1. 페어 (Pairs) - 예: AA, 22
            if i == j:
                hand_label = f"{char1}{char2}"
                # 페어는 문양이 서로 달라야 함. 
                # Card 생성자 순서: Card(suit, rank)
                hole_cards = [
                    Card(Suit.SPADES, rank1), 
                    Card(Suit.HEARTS, rank2)
                ]
                
                win_rate = simulator.parallel_simulation(hole_cards, [], num_opponents)
                results.append((hand_label, win_rate))

            # 2. 페어가 아닌 경우 (Non-Pairs)
            else:
                # 2-1. 수딧 (Suited) - 예: AKs
                hand_label_s = f"{char1}{char2}s"
                # 문양이 같아야 함
                hole_cards_s = [
                    Card(Suit.SPADES, rank1), 
                    Card(Suit.SPADES, rank2)
                ]
                
                win_rate_s = simulator.parallel_simulation(hole_cards_s, [], num_opponents)
                results.append((hand_label_s, win_rate_s))

                # 2-2. 오프수딧 (Off-suit) - 예: AKo
                hand_label_o = f"{char1}{char2}o"
                # 문양이 달라야 함
                hole_cards_o = [
                    Card(Suit.SPADES, rank1), 
                    Card(Suit.HEARTS, rank2)
                ]
                
                win_rate_o = simulator.parallel_simulation(hole_cards_o, [], num_opponents)
                results.append((hand_label_o, win_rate_o))
    
    elapsed_time = time.time() - start_time
    print(f"\n분석 완료! 소요 시간: {elapsed_time:.2f}초")
    
    return results

def print_results_table(results: List[tuple]):
    """결과 출력 함수 (변경 사항 없음, 그대로 사용)"""
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

    print("\n" + "="*55)
    print(f"| {'Rank':<4} | {'Hand':<6} | {'Win Rate':<10} | {'Bar Graph':<20} |")
    print("-" * 55)

    for idx, (hand, rate) in enumerate(sorted_results, 1):
        percentage = rate * 100
        bar_length = int(percentage / 5)
        bar = "■" * bar_length
        print(f"| {idx:<4} | {hand:<6} | {percentage:6.2f}%    | {bar:<20} |")
    
    print("="*55)

if __name__ == "__main__":
    # 실행 예시
    sim_results = run_preflop_analysis(num_simulations=20000, num_opponents=1)
    print_results_table(sim_results)