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
    """Player 클래스 테스트"""

    def test_player_creation(self):
        player = Player("Test Player", 1000)
        assert player.name == "Test Player"
        assert player.chips == 1000
        assert len(player.hand) == 0

    def test_player_bet(self):
        player = Player("Test", 1000)
        bet_amount = player.bet(100)

        assert bet_amount == 100
        assert player.chips == 900
        assert player.current_bet == 100

    def test_player_all_in(self):
        player = Player("Test", 100)
        bet_amount = player.bet(200)  # All-in

        assert bet_amount == 100
        assert player.chips == 0
        assert player.is_all_in


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