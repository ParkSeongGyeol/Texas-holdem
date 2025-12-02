"""
Texas Hold'em Poker Game - Main Entry Point
2025년 2학기 알고리즘 프로젝트
팀원: 문현준, 박성결, 박종호, 박우현
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict
from types import MethodType
from src.core.game import PokerGame, Action as GameAction
from src.core.player import Player
from src.ai.base_ai import Action as AIAction, Position
from src.ai.rule_based_ai import RuleBasedAI

try:
    from src.ai.rule_based_ai import AdaptiveRuleBasedAI
except ImportError:
    AdaptiveRuleBasedAI = None

AI_TO_GAME_ACTION = {
    AIAction.FOLD: GameAction.FOLD,
    AIAction.CHECK: GameAction.CHECK,
    AIAction.CALL: GameAction.CALL,
    AIAction.RAISE: GameAction.RAISE,
    AIAction.ALL_IN: GameAction.ALL_IN,
}

def start_multiplayer_game():
    """멀티플레이어 게임 모드 (2-4인)"""
    print("\n" + "=" * 60)
    print("🃏 멀티플레이어 게임 (최대 4인)")
    print("=" * 60)

    # 플레이어 수 설정
    while True:
        try:
            num_players = int(input("플레이어 수를 입력하세요 (2-4): "))
            if 2 <= num_players <= 4:
                break
            print("2명에서 4명 사이여야 합니다.")
        except ValueError:
            print("올바른 숫자를 입력하세요.")

    # 칩 설정
    try:
        starting_chips = int(input("시작 칩 수를 입력하세요 (기본값: 1000): ") or "1000")
    except ValueError:
        starting_chips = 1000

    # 게임 생성
    game = PokerGame(small_blind=10, big_blind=20)

    # 플레이어 추가
    for i in range(num_players):
        name = input(f"플레이어 {i+1}의 이름을 입력하세요: ").strip() or f"Player {i+1}"
        game.add_player(name, starting_chips)

    print(f"\n{num_players}명의 플레이어가 참가했습니다.")
    print("\n게임을 시작합니다!")
    
    # 게임 진행
    try:
        while True:
            game.play_full_hand()
            
            # 파산한 플레이어 체크 (간단한 로직)
            active_count = sum(1 for p in game.players if p.chips > 0)
            if active_count < 2:
                print("\n게임 종료! 플레이어가 부족합니다.")
                break
            
            # 계속 진행 여부
            again = input("\n다음 핸드를 진행할까요? (y/n): ").strip().lower()
            if again != 'y':
                break
                
    except KeyboardInterrupt:
        print("\n\n게임이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

def attach_ai_controller(game: PokerGame, ai_controllers: Dict[str, object]) -> None:
    """AI 컨트롤러 연결 (Monkey Patching)"""
    original_get_player_action = game.get_player_action

    def get_player_action_with_ai(self: PokerGame, player: Player):
        if player.name not in ai_controllers:
            return original_get_player_action(player)

        ai = ai_controllers[player.name]
        ai.receive_hole_cards(player.hand)
        
        # AI 액션 결정
        ai_action, ai_amount = ai.act(
            community_cards=self.community_cards,
            pot=self.pot,
            current_bet=self.current_bet - player.current_bet,
            opponents=[] # 현재 구현상 미사용
        )

        game_action = AI_TO_GAME_ACTION[ai_action]
        
        # Call인데 낼 돈이 0이면 Check로 변환
        if game_action == GameAction.CALL and (self.current_bet - player.current_bet) == 0:
            game_action = GameAction.CHECK

        amount = ai_amount if game_action == GameAction.RAISE else 0
        print(f"[AI] {player.name}: {game_action.value}, amount={amount}")

        return game_action, amount

    game.get_player_action = MethodType(get_player_action_with_ai, game)

def start_ai_game():
    """AI 대전 모드 (1 vs 1)"""
    print("\n" + "=" * 60)
    print("🤖 AI 대전 모드")
    print("=" * 60)

    print("AI 난이도를 선택하세요:")
    print("  1. 루즈 (Loose) - 공격적, 블러핑 많음")
    print("  2. 타이트 (Tight) - 보수적, 강한 패 위주")
    if AdaptiveRuleBasedAI:
        print("  3. 적응형 (Adaptive) - 플레이어 스타일 분석")
    
    choice = input("선택 (기본: 2): ").strip() or "2"

    game = PokerGame(small_blind=10, big_blind=20)
    
    human_name = input("당신의 이름을 입력하세요: ").strip() or "Player"
    ai_name = "AlphaGo"

    game.add_player(human_name, 1000)
    game.add_player(ai_name, 1000)

    # AI 생성
    if choice == "1":
        ai = RuleBasedAI(name=ai_name, position=Position.BB, strategy_type="loose")
        print(f"\n[설정] {ai_name}(Loose)와 대결합니다.")
    elif choice == "3" and AdaptiveRuleBasedAI:
        ai = AdaptiveRuleBasedAI(name=ai_name, position=Position.BB, base_mode="tight")
        print(f"\n[설정] {ai_name}(Adaptive)와 대결합니다.")
    else:
        ai = RuleBasedAI(name=ai_name, position=Position.BB, strategy_type="tight")
        print(f"\n[설정] {ai_name}(Tight)와 대결합니다.")

    attach_ai_controller(game, {ai_name: ai})

    print("\n게임을 시작합니다!")
    
    try:
        while True:
            game.play_full_hand()
            
            if game.players[0].chips <= 0:
                print("\n패배했습니다! 칩이 모두 소진되었습니다.")
                break
            if game.players[1].chips <= 0:
                print("\n승리했습니다! AI의 칩이 모두 소진되었습니다.")
                break

            again = input("\n다음 핸드를 진행할까요? (y/n): ").strip().lower()
            if again != 'y':
                break

    except KeyboardInterrupt:
        print("\n게임이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "=" * 60)
    print("🎰 텍사스 홀덤 포커 게임 🎰")
    print("=" * 60)

    while True:
        print("\n메뉴 선택:")
        print("  1. 멀티플레이어 게임 (2-4인)")
        print("  2. AI와 대전 (1 vs 1)")
        print("  3. 종료")

        choice = input("\n선택 > ").strip()

        if choice == "1":
            start_multiplayer_game()
        elif choice == "2":
            start_ai_game()
        elif choice == "3":
            print("\n게임을 종료합니다.")
            break
        else:
            print("올바른 번호를 입력해주세요.")

if __name__ == "__main__":
    main()