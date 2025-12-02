
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

try:
    from src.core.card import Card, Deck
    from src.algorithms.hand_evaluator import HandEvaluator
    print("Imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
