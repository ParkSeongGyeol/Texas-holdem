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

# Install in development mode
pip install -e .

# Install with dev dependencies
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
  - Card/Deck classes, Fisher-Yates shuffle algorithm
  - Hand evaluation using bitmasking for O(1) rank detection
  - Combination logic C(7,5) = 21 for best 5-card hand

- **박성결 (Game Logic)**: `src/core/player.py`, `src/core/game.py`
  - Finite State Machine for game phases (PREFLOP → FLOP → TURN → RIVER → SHOWDOWN)
  - Turn progression, betting rounds, pot distribution
  - Winner determination logic

- **박종호 (AI Strategy)**: `src/ai/base_ai.py`, `src/ai/rule_based_ai.py`, `src/ai/strategies.py`
  - AI interface and decision-making system
  - Three difficulty levels: Tight, Loose Aggressive, Adaptive
  - Bluffing models and opponent pattern analysis

- **박우현 (Advanced AI)**: `src/algorithms/monte_carlo.py`, `src/algorithms/minimax.py`, `src/web/`
  - Monte Carlo simulation with parallel processing (1000 iterations)
  - Minimax algorithm with alpha-beta pruning
  - WebSocket-based multiplayer system (planned)

### Game State Flow

The game follows a strict phase progression managed by `GamePhase` enum:
1. **PREFLOP**: Deal 2 hole cards to each player, betting round
2. **FLOP**: Deal 3 community cards (with burn card), betting round
3. **TURN**: Deal 1 community card (with burn card), betting round
4. **RIVER**: Deal 1 community card (with burn card), betting round
5. **SHOWDOWN**: Determine winner using best 5-card hand from 7 total cards

Each phase transition includes a burn card before dealing community cards.

### AI Decision System

AI players inherit from `AIPlayer` ABC and must implement:
- `make_decision()`: Returns tuple of (Action, amount)
- `analyze_hand_strength()`: Returns float 0.0-1.0

Actions available: FOLD, CHECK, CALL, RAISE, ALL_IN

### Key Algorithms

1. **Fisher-Yates Shuffle**: O(n) card shuffling in `Deck.shuffle()`
2. **Bitmasking**: Planned for O(1) hand rank detection in `HandEvaluator`
3. **Combinatorics**: C(7,5) = 21 combinations to find best 5-card hand
4. **Monte Carlo**: 1000 simulations with parallel processing for win probability
5. **Minimax**: Game tree search with alpha-beta pruning for optimal decisions
6. **Dynamic Programming**: Expected value calculation with memoization (planned)

### Player State Management

Players maintain state through:
- `chips`: Current chip stack
- `hand`: List of hole cards
- `current_bet`: Amount bet in current round
- `is_active`, `has_folded`, `is_all_in`: State flags

Critical: Use `reset_for_new_hand()` between hands to clear state properly.

## Development Notes

### TODO Comments
The codebase contains many TODO comments marking planned implementations. These indicate:
- Features assigned to specific team members
- Algorithm implementations to be completed
- Optimization opportunities

Example: `# TODO: Fisher-Yates 알고리즘 구현 (문현준)` indicates this is 문현준's responsibility.

### Testing Strategy
- All core classes (Card, Deck, Player, PokerGame) have basic unit tests in `tests/test_core.py`
- Tests verify creation, equality, state transitions, and error conditions
- Add tests for new algorithms in separate test files (e.g., `test_algorithms.py` for hand evaluator)

### Import Structure
- Use absolute imports: `from src.core.card import Card`
- The `src/` directory is a proper Python package with `__init__.py` files
- Main entry point is `src/main.py`

### AI Implementation Pattern
When implementing new AI strategies:
1. Inherit from `AIPlayer` ABC
2. Implement required abstract methods
3. Store opponent patterns in `opponent_patterns` dict
4. Use `update_opponent_pattern()` to track opponent behavior
5. Return decisions as `(Action, int)` tuples

### Game Phase Transitions
Always follow this pattern:
1. Deal cards (community or hole)
2. Update `current_phase`
3. Run betting round
4. Update pot with collected bets
5. Check if only one active player remains (early win)
6. Proceed to next phase or showdown

### Planned Features (Not Yet Implemented)
- FastAPI web server with WebSocket support
- Tournament mode with multiple AIs
- Statistics tracking (win rate, ROI, hand performance)
- Debug mode showing AI thought process
- Full hand evaluator with bitmasking
- Complete Monte Carlo simulation
- Minimax decision tree
