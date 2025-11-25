import unittest
from src.core.card import Card, Suit, Rank
from src.algorithms.hand_evaluator import HandEvaluator, HandRank
from src.core.game import PokerGame
from src.core.player import Player

class TestHandEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.game = PokerGame()
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game.players = [self.player1, self.player2]

    def test_evaluate_hand_kickers(self):
        # Test High Card: A, K, Q, J, 9 (10, 8, 2 are ignored)
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.DIAMONDS, Rank.QUEEN),
            Card(Suit.CLUBS, Rank.JACK),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.HEARTS, Rank.EIGHT),
            Card(Suit.DIAMONDS, Rank.TWO)
        ]
        rank, kickers, best_cards = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.HIGH_CARD)
        self.assertEqual(kickers, [14, 13, 12, 11, 9])

    def test_determine_winner_pair_vs_high_card(self):
        # Player 1: Pair of Aces
        self.player1.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)]
        # Player 2: High Card King
        self.player2.hand = [Card(Suit.CLUBS, Rank.KING), Card(Suit.DIAMONDS, Rank.QUEEN)]
        
        # Community: 2, 3, 4, 5, 9 (No straight, no flush possible for these suits)
        self.game.community_cards = [
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.HEARTS, Rank.THREE),
            Card(Suit.DIAMONDS, Rank.FOUR),
            Card(Suit.CLUBS, Rank.FIVE),
            Card(Suit.SPADES, Rank.NINE)
        ]
        
        winners = self.game.determine_winner()
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], self.player1)

    def test_determine_winner_tie_breaker(self):
        # Player 1: Pair of Aces, Kicker King
        self.player1.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]
        # Player 2: Pair of Aces, Kicker Queen
        self.player2.hand = [Card(Suit.CLUBS, Rank.ACE), Card(Suit.DIAMONDS, Rank.QUEEN)]
        
        # Community: A, 2, 3, 4, 9
        self.game.community_cards = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.DIAMONDS, Rank.THREE),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.NINE)
        ]
        
        # Both have Pair of Aces (A, A).
        # Kickers:
        # P1: A, A, K, 9, 4
        # P2: A, A, Q, 9, 4
        # P1 should win
        
        winners = self.game.determine_winner()
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], self.player1)

    def test_determine_winner_split_pot(self):
        # Player 1: A, K
        self.player1.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]
        # Player 2: A, K
        self.player2.hand = [Card(Suit.CLUBS, Rank.ACE), Card(Suit.DIAMONDS, Rank.KING)]
        
        # Community: Q, J, 10, 2, 3 (Straight A, K, Q, J, 10)
        self.game.community_cards = [
            Card(Suit.SPADES, Rank.QUEEN),
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.DIAMONDS, Rank.TEN),
            Card(Suit.CLUBS, Rank.TWO),
            Card(Suit.SPADES, Rank.THREE)
        ]
        
        # Both have Straight (A, K, Q, J, 10)
        
        winners = self.game.determine_winner()
        self.assertEqual(len(winners), 2)
        self.assertIn(self.player1, winners)
        self.assertIn(self.player2, winners)

if __name__ == '__main__':
    unittest.main()
