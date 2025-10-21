"""
Texas Hold'em Poker Game - Main Entry Point
2025년 2학기 알고리즘 프로젝트
팀원: 문현준, 박성결, 박종호, 박우현

Week 3-7 구현 내용 (박성결):
- Week 3: 게임 상태 관리 (FSM), 턴 진행 시스템
- Week 4: Player 클래스 구조, 핸드 관리
- Week 5: 팟 구조, 베팅/레이즈/폴드 로직
- Week 6: 베팅 액션 처리, 사이드 팟, 올인 상황
- Week 7: 승자 결정, 게임 플로우 테스트, 디버그 기능
"""

from src.core.game import PokerGame


def demo_game():
    """데모 게임 실행 (테스트용)"""
    print("\n=== 데모 게임 시작 ===")
    print("이 게임은 박성결이 구현한 Week 3-7 기능을 보여줍니다.\n")

    # 게임 생성
    game = PokerGame(small_blind=10, big_blind=20)

    # 플레이어 추가
    game.add_player("Alice", 1000)
    game.add_player("Bob", 1000)
    game.add_player("Charlie", 500)

    print("플레이어가 추가되었습니다:")
    for player in game.players:
        print(f"  - {player.name}: {player.chips} chips")

    print("\n게임을 시작하려면 play_full_hand()를 호출하세요.")
    print("예: game.play_full_hand()\n")

    return game


def interactive_mode():
    """인터랙티브 모드 (실제 플레이 가능)"""
    print("\n" + "=" * 60)
    print("텍사스 홀덤 포커 게임 - 인터랙티브 모드")
    print("=" * 60)
    print("\nWeek 3-7 구현 기능 (박성결):")
    print("  ✓ 게임 상태 관리 (FSM)")
    print("  ✓ 턴 관리 시스템")
    print("  ✓ 플레이어 클래스 및 핸드 관리")
    print("  ✓ 팟 구조 및 베팅 로직")
    print("  ✓ 베팅 액션 처리 (Fold/Check/Call/Raise/All-in)")
    print("  ✓ 사이드 팟 계산")
    print("  ✓ 승자 결정 및 팟 분배")
    print("  ✓ 디버그 기능 및 액션 히스토리")
    print("=" * 60)

    # 게임 설정
    print("\n게임 설정:")
    try:
        num_players = int(input("플레이어 수를 입력하세요 (2-10): "))
        if num_players < 2 or num_players > 10:
            print("2-10명의 플레이어가 필요합니다. 기본값 3명으로 설정합니다.")
            num_players = 3
    except ValueError:
        print("올바른 숫자를 입력하지 않았습니다. 기본값 3명으로 설정합니다.")
        num_players = 3

    try:
        starting_chips = int(input("시작 칩 수를 입력하세요 (기본값: 1000): ") or "1000")
    except ValueError:
        starting_chips = 1000

    # 게임 생성
    game = PokerGame(small_blind=10, big_blind=20)

    # 플레이어 추가
    player_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    for i in range(num_players):
        game.add_player(player_names[i], starting_chips)

    print(f"\n{num_players}명의 플레이어가 추가되었습니다.")

    # 디버그 모드 설정
    debug = input("디버그 모드를 활성화하시겠습니까? (y/n): ").lower() == 'y'
    if debug:
        game.enable_debug_mode()

    print("\n게임을 시작합니다!")
    print("\n액션 선택:")
    print("  - fold: 폴드 (패 포기)")
    print("  - check: 체크 (베팅 없이 패스)")
    print("  - call: 콜 (현재 베팅에 맞춤)")
    print("  - raise: 레이즈 (베팅 증가)")
    print("  - allin: 올인 (모든 칩 베팅)")
    print("\n" + "=" * 60)

    # 게임 진행
    try:
        game.play_full_hand()

        # 게임 통계 출력
        print("\n" + "=" * 60)
        print("게임 통계:")
        stats = game.get_game_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 액션 히스토리 출력 여부
        show_history = input("\n액션 히스토리를 보시겠습니까? (y/n): ").lower() == 'y'
        if show_history:
            game.print_action_history()

    except KeyboardInterrupt:
        print("\n\n게임이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()


def test_mode():
    """테스트 모드 - 자동화된 기능 검증"""
    print("\n" + "=" * 60)
    print("테스트 모드 - Week 3-7 기능 검증")
    print("=" * 60)

    print("\n[테스트 1] 게임 초기화 및 플레이어 추가")
    game = PokerGame(small_blind=5, big_blind=10)
    game.add_player("Alice", 1000)
    game.add_player("Bob", 1000)
    print(f"  ✓ 플레이어 수: {len(game.players)}")
    print(f"  ✓ 스몰 블라인드: {game.small_blind}")
    print(f"  ✓ 빅 블라인드: {game.big_blind}")

    print("\n[테스트 2] 핸드 시작 및 카드 딜링")
    game.new_hand()
    print(f"  ✓ 게임 단계: {game.current_phase.value}")
    print(f"  ✓ Alice의 핸드: {game.players[0].has_full_hand()}")
    print(f"  ✓ Bob의 핸드: {game.players[1].has_full_hand()}")

    print("\n[테스트 3] 블라인드 베팅")
    game.post_blinds()
    print(f"  ✓ 팟: {game.pot}")
    print(f"  ✓ 현재 베팅: {game.current_bet}")

    print("\n[테스트 4] 게임 단계 전이")
    game.deal_flop()
    print(f"  ✓ FLOP: {game.current_phase.value}")
    print(f"  ✓ 커뮤니티 카드 수: {len(game.community_cards)}")

    game.deal_turn()
    print(f"  ✓ TURN: {game.current_phase.value}")
    print(f"  ✓ 커뮤니티 카드 수: {len(game.community_cards)}")

    game.deal_river()
    print(f"  ✓ RIVER: {game.current_phase.value}")
    print(f"  ✓ 커뮤니티 카드 수: {len(game.community_cards)}")

    print("\n[테스트 5] 액션 로깅")
    game.log_action("테스트 액션 1")
    game.log_action("테스트 액션 2")
    print(f"  ✓ 액션 히스토리 크기: {len(game.action_history)}")

    print("\n[테스트 6] 게임 통계")
    stats = game.get_game_statistics()
    print("  ✓ 게임 통계:")
    for key, value in stats.items():
        print(f"    - {key}: {value}")

    print("\n[테스트 7] 플레이어 상태 관리")
    player = game.players[0]
    print(f"  ✓ 초기 상태: {player.get_state()}")
    player.fold()
    print(f"  ✓ 폴드 후: {player.get_state()}")
    player.reset_for_new_hand()
    print(f"  ✓ 리셋 후: {player.get_state()}")

    print("\n" + "=" * 60)
    print("모든 테스트가 완료되었습니다!")
    print("=" * 60)


def main():
    """메인 함수 - 모드 선택"""
    print("\n" + "=" * 60)
    print("🎰 텍사스 홀덤 포커 게임 🎰")
    print("=" * 60)
    print("2025년 2학기 알고리즘 프로젝트")
    print("팀원: 문현준, 박성결, 박종호, 박우현")
    print("=" * 60)

    print("\n모드 선택:")
    print("  1. 인터랙티브 모드 (실제 게임 플레이)")
    print("  2. 테스트 모드 (자동화된 기능 검증)")
    print("  3. 데모 모드 (게임 객체 생성만)")
    print("  4. 종료")

    try:
        choice = input("\n선택 (1-4): ").strip()

        if choice == "1":
            interactive_mode()
        elif choice == "2":
            test_mode()
        elif choice == "3":
            demo_game()
            print("\n데모 게임이 생성되었습니다.")
        elif choice == "4":
            print("\n게임을 종료합니다. 안녕히 가세요!")
        else:
            print("\n올바른 선택이 아닙니다.")
            main()

    except KeyboardInterrupt:
        print("\n\n프로그램이 종료되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()