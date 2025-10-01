"""
Core 모듈 테스트
"""

import pytest
from src.core.card import Card, Deck, Suit, Rank
from src.core.player import Player
from src.core.game import PokerGame


class TestCard:
    """Card 클래스 테스트"""

    def test_card_creation(self):
        card = Card(Suit.SPADES, Rank.ACE)
        assert card.suit == Suit.SPADES
        assert card.rank == Rank.ACE
        assert str(card) == "A♠"

    def test_card_equality(self):
        card1 = Card(Suit.HEARTS, Rank.KING)
        card2 = Card(Suit.HEARTS, Rank.KING)
        card3 = Card(Suit.SPADES, Rank.KING)

        assert card1 == card2
        assert card1 != card3


class TestDeck:
    """Deck 클래스 테스트"""

    def test_deck_creation(self):
        deck = Deck()
        assert len(deck.cards) == 52

    def test_deck_deal(self):
        deck = Deck()
        card = deck.deal()
        assert isinstance(card, Card)
        assert len(deck.cards) == 51

    def test_deck_empty(self):
        deck = Deck()
        # 모든 카드 뽑기
        for _ in range(52):
            deck.deal()

        assert deck.is_empty()
        with pytest.raises(ValueError):
            deck.deal()


class TestPlayer:
    """Player 클래스 테스트 - 박성결 담당"""

    # 기본 생성 및 초기화 테스트
    def test_player_creation(self):
        """플레이어 정상 생성"""
        player = Player("Test Player", 1000)
        assert player.name == "Test Player"
        assert player.chips == 1000
        assert len(player.hand) == 0
        assert player.is_active is True
        assert player.has_folded is False
        assert player.is_all_in is False

    def test_player_creation_with_zero_chips(self):
        """칩이 0인 플레이어 생성"""
        player = Player("Poor Player", 0)
        assert player.chips == 0
        assert player.is_active is False  # 칩이 0이면 비활성

    def test_player_creation_invalid_name(self):
        """빈 이름으로 플레이어 생성 시 에러"""
        with pytest.raises(ValueError, match="플레이어 이름은 비어있을 수 없습니다"):
            Player("", 1000)

        with pytest.raises(ValueError, match="플레이어 이름은 비어있을 수 없습니다"):
            Player("   ", 1000)

    def test_player_creation_negative_chips(self):
        """음수 칩으로 플레이어 생성 시 에러"""
        with pytest.raises(ValueError, match="초기 칩은 0 이상이어야 합니다"):
            Player("Test", -100)

    # 베팅 테스트
    def test_player_bet_normal(self):
        """정상 베팅"""
        player = Player("Test", 1000)
        bet_amount = player.bet(100)

        assert bet_amount == 100
        assert player.chips == 900
        assert player.current_bet == 100
        assert player.is_all_in is False

    def test_player_bet_multiple_times(self):
        """여러 번 베팅 (누적)"""
        player = Player("Test", 1000)
        player.bet(100)
        player.bet(50)

        assert player.chips == 850
        assert player.current_bet == 150

    def test_player_all_in(self):
        """올인 (보유 칩보다 많이 베팅)"""
        player = Player("Test", 100)
        bet_amount = player.bet(200)  # All-in

        assert bet_amount == 100  # 실제로는 100만 베팅됨
        assert player.chips == 0
        assert player.is_all_in is True
        assert player.current_bet == 100

    def test_player_all_in_exact(self):
        """정확히 보유 칩만큼 베팅 (올인)"""
        player = Player("Test", 100)
        bet_amount = player.bet(100)

        assert bet_amount == 100
        assert player.chips == 0
        assert player.is_all_in is True

    def test_player_bet_negative_amount(self):
        """음수 베팅 시도"""
        player = Player("Test", 1000)
        with pytest.raises(ValueError, match="베팅 금액은 음수일 수 없습니다"):
            player.bet(-50)

    def test_player_bet_zero_amount(self):
        """0 베팅 시도 (체크는 별도 처리)"""
        player = Player("Test", 1000)
        with pytest.raises(ValueError, match="베팅 금액은 0보다 커야 합니다"):
            player.bet(0)

    def test_player_bet_after_fold(self):
        """폴드 후 베팅 시도"""
        player = Player("Test", 1000)
        player.fold()
        with pytest.raises(RuntimeError, match="폴드한 플레이어는 베팅할 수 없습니다"):
            player.bet(100)

    def test_player_bet_with_no_chips(self):
        """칩이 없는 상태에서 베팅 시도"""
        player = Player("Test", 100)
        player.bet(100)  # 올인
        with pytest.raises(RuntimeError, match="칩이 없는 플레이어는 베팅할 수 없습니다"):
            player.bet(10)

    # 카드 받기 테스트
    def test_player_receive_card(self):
        """카드 받기"""
        player = Player("Test", 1000)
        card1 = Card(Suit.SPADES, Rank.ACE)
        card2 = Card(Suit.HEARTS, Rank.KING)

        player.receive_card(card1)
        assert len(player.hand) == 1
        assert player.hand[0] == card1

        player.receive_card(card2)
        assert len(player.hand) == 2
        assert player.hand[1] == card2

    def test_player_receive_too_many_cards(self):
        """3장 이상 받기 시도"""
        player = Player("Test", 1000)
        player.receive_card(Card(Suit.SPADES, Rank.ACE))
        player.receive_card(Card(Suit.HEARTS, Rank.KING))

        with pytest.raises(ValueError, match="플레이어는 최대 2장의 홀 카드만 가질 수 있습니다"):
            player.receive_card(Card(Suit.DIAMONDS, Rank.QUEEN))

    def test_player_receive_none_card(self):
        """None 카드 받기 시도"""
        player = Player("Test", 1000)
        with pytest.raises(ValueError, match="카드는 None일 수 없습니다"):
            player.receive_card(None)

    # 폴드 테스트
    def test_player_fold(self):
        """폴드"""
        player = Player("Test", 1000)
        player.fold()

        assert player.has_folded is True
        assert player.is_active is False

    def test_player_fold_twice(self):
        """이미 폴드한 상태에서 다시 폴드"""
        player = Player("Test", 1000)
        player.fold()

        with pytest.raises(RuntimeError, match="이미 폴드한 플레이어입니다"):
            player.fold()

    # 상태 전환 테스트
    def test_player_reset_for_new_hand(self):
        """새 핸드를 위한 리셋"""
        player = Player("Test", 1000)

        # 게임 진행
        player.receive_card(Card(Suit.SPADES, Rank.ACE))
        player.receive_card(Card(Suit.HEARTS, Rank.KING))
        player.bet(100)

        # 리셋
        player.reset_for_new_hand()

        assert len(player.hand) == 0
        assert player.current_bet == 0
        assert player.has_folded is False
        assert player.is_all_in is False
        assert player.is_active is True  # 칩이 있으므로
        assert player.chips == 900  # 칩은 유지

    def test_player_reset_with_no_chips(self):
        """칩이 없는 상태에서 리셋"""
        player = Player("Test", 100)
        player.bet(100)  # 올인

        player.reset_for_new_hand()

        assert player.is_active is False  # 칩이 0이므로 비활성
        assert player.chips == 0

    # 상태 확인 테스트
    def test_player_can_bet(self):
        """베팅 가능 여부 확인"""
        player = Player("Test", 1000)

        assert player.can_bet(100) is True
        assert player.can_bet(1000) is True
        assert player.can_bet(1001) is False  # 칩 부족
        assert player.can_bet(-50) is False  # 음수

    def test_player_can_bet_after_fold(self):
        """폴드 후 베팅 가능 여부"""
        player = Player("Test", 1000)
        player.fold()

        assert player.can_bet(100) is False

    def test_player_can_act(self):
        """액션 가능 여부 확인"""
        player = Player("Test", 1000)
        assert player.can_act() is True

        # 폴드 후
        player_folded = Player("Folded", 1000)
        player_folded.fold()
        assert player_folded.can_act() is False

        # 올인 후
        player_allin = Player("AllIn", 100)
        player_allin.bet(100)
        assert player_allin.can_act() is False

    # 상태 문자열 테스트
    def test_player_get_state(self):
        """상태 문자열 반환"""
        player = Player("Test", 1000)
        assert player.get_state() == "ACTIVE"

        player.fold()
        assert player.get_state() == "FOLDED"

        player2 = Player("Test2", 100)
        player2.bet(100)
        assert player2.get_state() == "ALL_IN"

        player3 = Player("Test3", 0)
        assert player3.get_state() == "OUT_OF_CHIPS"

    # 문자열 표현 테스트
    def test_player_str(self):
        """__str__ 메서드"""
        player = Player("Alice", 1000)
        player.receive_card(Card(Suit.SPADES, Rank.ACE))
        player.receive_card(Card(Suit.HEARTS, Rank.KING))

        result = str(player)
        assert "Alice" in result
        assert "ACTIVE" in result
        assert "1000" in result
        assert "A♠" in result
        assert "K♥" in result

    def test_player_repr(self):
        """__repr__ 메서드"""
        player = Player("Bob", 500)
        result = repr(player)
        assert "Player" in result
        assert "Bob" in result
        assert "500" in result
        assert "ACTIVE" in result


class TestPokerGame:
    """PokerGame 클래스 테스트"""

    def test_game_creation(self):
        game = PokerGame()
        assert len(game.players) == 0
        assert game.pot == 0

    def test_add_player(self):
        game = PokerGame()
        game.add_player("Alice", 1000)
        game.add_player("Bob", 1000)

        assert len(game.players) == 2
        assert game.players[0].name == "Alice"
        assert game.players[1].name == "Bob"