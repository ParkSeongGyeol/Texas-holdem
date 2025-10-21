"""
게임 플로우 테스트 - Week 7 (박성결)
전체 게임 진행 테스트 및 디버그 기능 검증
"""

import pytest
from src.core.game import PokerGame, GamePhase, Action
from src.core.player import Player


class TestGameFlow:
    """게임 플로우 테스트 클래스"""

    def test_game_initialization(self):
        """게임 초기화 테스트"""
        game = PokerGame(small_blind=10, big_blind=20)

        assert game.small_blind == 10
        assert game.big_blind == 20
        assert game.pot == 0
        assert game.current_phase == GamePhase.PREFLOP
        assert len(game.players) == 0
        assert len(game.community_cards) == 0
        assert game.debug_mode == False

    def test_add_players(self):
        """플레이어 추가 테스트"""
        game = PokerGame()

        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        assert len(game.players) == 3
        assert game.players[0].name == "Alice"
        assert game.players[1].name == "Bob"
        assert game.players[2].name == "Charlie"

        for player in game.players:
            assert player.chips == 1000
            assert player.is_active == True

    def test_deal_hole_cards(self):
        """홀 카드 딜링 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        game.new_hand()

        # 각 플레이어가 2장씩 받았는지 확인
        for player in game.players:
            assert len(player.hand) == 2
            assert player.has_full_hand() == True

    def test_game_phases(self):
        """게임 단계 전이 테스트"""
        game = PokerGame()

        # 초기 상태: PREFLOP
        assert game.current_phase == GamePhase.PREFLOP

        # FLOP
        game.deal_flop()
        assert game.current_phase == GamePhase.FLOP
        assert len(game.community_cards) == 3

        # TURN
        game.deal_turn()
        assert game.current_phase == GamePhase.TURN
        assert len(game.community_cards) == 4

        # RIVER
        game.deal_river()
        assert game.current_phase == GamePhase.RIVER
        assert len(game.community_cards) == 5

    def test_active_players(self):
        """활성 플레이어 관리 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        # 초기 상태: 모두 활성
        assert len(game.get_active_players()) == 3

        # Bob이 폴드
        game.players[1].fold()
        assert len(game.get_active_players()) == 2

        # Charlie도 폴드
        game.players[2].fold()
        assert len(game.get_active_players()) == 1

    def test_player_can_act(self):
        """플레이어 액션 가능 여부 테스트"""
        player = Player("Alice", 1000)

        # 초기 상태: 액션 가능
        assert player.can_act() == True

        # 폴드 후: 액션 불가
        player.fold()
        assert player.can_act() == False

        # 리셋 후: 다시 액션 가능
        player.reset_for_new_hand()
        assert player.can_act() == True

        # 올인 후: 액션 불가
        player.bet(1000)
        assert player.is_all_in == True
        assert player.can_act() == False

    def test_betting_round_completion(self):
        """베팅 라운드 완료 조건 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.new_hand()

        # 초기: 베팅 라운드 미완료
        game.current_bet = 100
        game.players[0].bet(100)
        assert game.is_betting_round_complete() == False

        # 모두 같은 금액 베팅: 완료
        game.players[1].bet(100)
        assert game.is_betting_round_complete() == True

    def test_pot_collection(self):
        """팟 수집 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        # 베팅
        game.players[0].bet(100)
        game.players[1].bet(100)

        initial_pot = game.pot
        game.collect_bets()

        # 팟에 베팅액 추가 확인
        assert game.pot == initial_pot + 200
        assert game.players[0].current_bet == 0
        assert game.players[1].current_bet == 0

    def test_action_fold(self):
        """폴드 액션 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        player = game.players[0]
        game.process_action(player, Action.FOLD, 0)

        assert player.has_folded == True
        assert player.is_active == False

    def test_action_check(self):
        """체크 액션 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        player = game.players[0]
        initial_chips = player.chips

        game.process_action(player, Action.CHECK, 0)

        # 체크는 칩 변화 없음
        assert player.chips == initial_chips
        assert player.has_folded == False

    def test_action_call(self):
        """콜 액션 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        player = game.players[0]
        game.current_bet = 100

        game.process_action(player, Action.CALL, 100)

        assert player.chips == 900
        assert player.current_bet == 100

    def test_action_raise(self):
        """레이즈 액션 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        player = game.players[0]
        game.current_bet = 50

        # 50 레이즈 (50 콜 + 50 레이즈 = 100 베팅)
        game.process_action(player, Action.RAISE, 50)

        assert player.chips == 900
        assert player.current_bet == 100
        assert game.current_bet == 100

    def test_action_allin(self):
        """올인 액션 테스트"""
        game = PokerGame()
        game.add_player("Alice", 500)

        player = game.players[0]
        game.process_action(player, Action.ALL_IN, 500)

        assert player.chips == 0
        assert player.is_all_in == True
        assert player.current_bet == 500

    def test_available_actions(self):
        """사용 가능한 액션 목록 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        player = game.players[0]
        game.current_bet = 0

        # 베팅이 없을 때: FOLD, CHECK, RAISE, ALL_IN
        actions = game.get_available_actions(player)
        assert Action.FOLD in actions
        assert Action.CHECK in actions
        assert Action.RAISE in actions
        assert Action.ALL_IN in actions

        # 베팅이 있을 때: FOLD, CALL, RAISE, ALL_IN
        game.current_bet = 100
        actions = game.get_available_actions(player)
        assert Action.FOLD in actions
        assert Action.CALL in actions
        assert Action.RAISE in actions
        assert Action.ALL_IN in actions
        assert Action.CHECK not in actions

    def test_blinds_posting(self):
        """블라인드 베팅 테스트"""
        game = PokerGame(small_blind=10, big_blind=20)
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        game.new_hand()
        game.post_blinds()

        # 팟에 블라인드가 추가되었는지 확인
        assert game.pot >= 30  # SB(10) + BB(20)

    def test_pot_distribution_single_winner(self):
        """단일 승자 팟 분배 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        game.pot = 200
        winners = [game.players[0]]

        initial_chips = game.players[0].chips
        game.distribute_pot(winners)

        assert game.players[0].chips == initial_chips + 200
        assert game.pot == 0

    def test_pot_distribution_multiple_winners(self):
        """다수 승자 팟 분배 테스트 (분할)"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        game.pot = 200
        winners = [game.players[0], game.players[1]]

        initial_chips_alice = game.players[0].chips
        initial_chips_bob = game.players[1].chips

        game.distribute_pot(winners)

        # 각각 100씩 분할
        assert game.players[0].chips == initial_chips_alice + 100
        assert game.players[1].chips == initial_chips_bob + 100
        assert game.pot == 0

    def test_debug_mode(self):
        """디버그 모드 테스트"""
        game = PokerGame()

        assert game.debug_mode == False

        game.enable_debug_mode()
        assert game.debug_mode == True

        game.disable_debug_mode()
        assert game.debug_mode == False

    def test_action_logging(self):
        """액션 로깅 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)

        assert len(game.action_history) == 0

        game.log_action("Test action 1")
        game.log_action("Test action 2")

        assert len(game.action_history) == 2
        assert "Test action 1" in game.action_history
        assert "Test action 2" in game.action_history

    def test_game_statistics(self):
        """게임 통계 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        game.new_hand()
        game.pot = 100
        game.current_bet = 50

        stats = game.get_game_statistics()

        assert stats['phase'] == GamePhase.PREFLOP.value
        assert stats['pot'] == 100
        assert stats['active_players'] == 2
        assert stats['current_bet'] == 50

    def test_player_hand_management(self):
        """플레이어 핸드 관리 테스트"""
        player = Player("Alice", 1000)

        # 초기: 핸드 없음
        assert player.has_full_hand() == False
        assert player.get_hand_description() == "핸드 없음"

        # 카드 추가
        from src.core.card import Card, Rank, Suit
        card1 = Card(Suit.SPADES, Rank.ACE)
        card2 = Card(Suit.HEARTS, Rank.KING)

        player.receive_card(card1)
        assert player.has_full_hand() == False

        player.receive_card(card2)
        assert player.has_full_hand() == True

        # 핸드 초기화
        player.clear_hand()
        assert len(player.hand) == 0
        assert player.has_full_hand() == False

    def test_player_win_pot(self):
        """플레이어 팟 획득 테스트"""
        player = Player("Alice", 1000)

        initial_chips = player.chips
        player.win_pot(500)

        assert player.chips == initial_chips + 500

    def test_early_game_end(self):
        """조기 게임 종료 테스트 (한 명만 남음)"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        game.new_hand()

        # Bob과 Charlie가 폴드
        game.players[1].fold()
        game.players[2].fold()

        # Alice만 남음
        active_players = game.get_active_players()
        assert len(active_players) == 1
        assert active_players[0].name == "Alice"

    def test_next_player_rotation(self):
        """플레이어 순회 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        game.current_player_index = 0

        # 다음 플레이어
        next_p = game.next_player()
        assert next_p.name == "Bob"
        assert game.current_player_index == 1

        # 그 다음 플레이어
        next_p = game.next_player()
        assert next_p.name == "Charlie"
        assert game.current_player_index == 2

        # 순환
        next_p = game.next_player()
        assert next_p.name == "Alice"
        assert game.current_player_index == 0


class TestSidePots:
    """사이드 팟 테스트 클래스"""

    def test_side_pot_calculation_simple(self):
        """간단한 사이드 팟 계산 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        # Alice: 100 (올인)
        # Bob: 200
        # Charlie: 200
        game.players[0].bet(100)
        game.players[0].is_all_in = True
        game.players[1].bet(200)
        game.players[2].bet(200)

        game.calculate_side_pots()

        # 메인 팟: 100 * 3 = 300 (모두 참여)
        # 사이드 팟: 100 * 2 = 200 (Bob, Charlie만 참여)
        assert len(game.side_pots) >= 1

    def test_side_pot_distribution(self):
        """사이드 팟 분배 테스트"""
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)
        game.add_player("Charlie", 1000)

        # 사이드 팟 생성
        game.side_pots = [
            {
                'amount': 300,
                'eligible_players': [game.players[0], game.players[1], game.players[2]]
            },
            {
                'amount': 200,
                'eligible_players': [game.players[1], game.players[2]]
            }
        ]

        # Charlie가 승리 (모든 팟 획득)
        winners = [game.players[2]]
        initial_chips = game.players[2].chips

        game.distribute_pot(winners)

        # 300 + 200 = 500 획득
        assert game.players[2].chips == initial_chips + 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
