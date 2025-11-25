
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.player import Player
from src.core.card import Card, Suit, Rank

def test_hand_strength():
    print("Testing get_hand_strength...")
    
    player = Player("TestPlayer")
    
    # Case 1: High Card
    player.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]
    community = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
        Card(Suit.SPADES, Rank.NINE)
    ]
    # A, K, Q, J, 9 -> High Card (but actually almost straight)
    # Wait, A, K, Q, J, 9 is just High Card if no flush.
    
    strength_high = player.get_hand_strength(community)
    print(f"High Card Strength: {strength_high}")
    
    # Case 2: One Pair
    player.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)]
    community = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
        Card(Suit.SPADES, Rank.NINE)
    ]
    strength_pair = player.get_hand_strength(community)
    print(f"One Pair Strength: {strength_pair}")
    
    # Case 3: Royal Flush
    player.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
    community = [
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN)
    ]
    strength_royal = player.get_hand_strength(community)
    print(f"Royal Flush Strength: {strength_royal}")
    
    if strength_royal > strength_pair > strength_high:
        print("SUCCESS: Strength order is correct.")
    else:
        print("FAILURE: Strength order is incorrect.")

if __name__ == "__main__":
    test_hand_strength()
