# Gemini.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

Texas Hold'em Poker Game with AI - Algorithm class team project (2025 2학기)
Team members: 문현준, 박성결, 박종호, 박우현

This is a 10-week academic project implementing a complete Texas Hold'em poker game with multiple AI difficulty levels using various algorithms learned in class.

## Common Commands

### Running the Game
```bash
python src/main.py
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v tests/
```

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode (recommended)
pip install -e .

# Install with dev dependencies (for testing, linting)
pip install -e .[dev]
```

### Code Quality
```bash
# Format code
black src/

# Lint code
flake8 src/
```

## Code Architecture

### Module Organization by Team Member

The codebase is organized by individual responsibilities:

- **문현준 (Card System)**: `src/core/card.py`, `src/algorithms/hand_evaluator.py`
  - Card/Deck classes, Fisher-Yates shuffle algorithm (implemented).
  - Hand evaluation using C(7,5) = 21 combinations to find the best 5-card hand (implemented).
  - O(1) hand rank detection using bitmasking is a planned optimization.

- **박성결 (Game Logic)**: `src/core/player.py`, `src/core/game.py`
  - Finite State Machine for game phases (PREFLOP → FLOP → TURN → RIVER → SHOWDOWN).
  - Turn progression, betting rounds, pot distribution.
  - Winner determination logic.

- **박종호 (AI Strategy)**: `src/ai/base_ai.py`, `src/ai/rule_based_ai.py`, `src/ai/strategies.py`
  - AI interface and decision-making system.
  - Implemented rule-based AI with a Strategy pattern for different difficulties: Tight and Loose Aggressive.
  - Adaptive AI is a planned feature.

- **박우현 (Advanced AI)**: `src/algorithms/monte_carlo.py`, `src/algorithms/minimax.py`, `src/web/`
  - Monte Carlo simulation with parallel processing (planned).
  - Minimax algorithm with alpha-beta pruning (planned).
  - WebSocket-based multiplayer system (planned).

### Game State Flow

The game follows a strict phase progression managed by `GamePhase` enum:
1. **PREFLOP**: Deal 2 hole cards to each player, betting round
2. **FLOP**: Deal 3 community cards (with burn card), betting round
3. **TURN**: Deal 1 community card (with burn card), betting round
4. **RIVER**: Deal 1 community card (with burn card), betting round
5. **SHOWDOWN**: Determine winner using best 5-card hand from 7 total cards

Each phase transition includes a burn card before dealing community cards.

### AI Decision System

AI players inherit from `AIPlayer` ABC. The main `RuleBasedAI` class uses a `Strategy` object (`TightStrategy` or `LooseStrategy`) to make decisions. The strategy implements the `decide()` method which returns a tuple of (Action, amount).

Actions available: FOLD, CHECK, CALL, RAISE, ALL_IN

### Key Algorithms

1. **Fisher-Yates Shuffle**: Implemented in `Deck.shuffle()` via `random.shuffle()` for O(n) card shuffling.
2. **Combinatorics**: Implemented in `HandEvaluator` to check all C(7,5) = 21 combinations to find the best 5-card hand.
3. **Bitmasking**: Planned for O(1) hand rank detection in `HandEvaluator` as a future optimization.
4. **Monte Carlo**: Planned for win probability calculation.
5. **Minimax**: Planned for game tree search with alpha-beta pruning for optimal decisions.

## Development Notes

### TODO Comments
The codebase contains TODO comments marking planned implementations. These indicate features assigned to specific team members, algorithm implementations to be completed, or optimization opportunities.

### Testing Strategy
- Core classes (Card, Deck, Player, PokerGame) have unit tests in `tests/test_core.py`.
- Game flow and state transitions are tested in `tests/test_game_flow.py`.
- Add tests for new algorithms in separate test files (e.g., `test_algorithms.py`).

### Import Structure
- Use absolute imports: `from src.core.card import Card`
- The `src/` directory is a proper Python package with `__init__.py` files.
- Main entry point is `src/main.py`.