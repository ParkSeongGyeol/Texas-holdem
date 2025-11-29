# src/ai/strategies.py

from typing import List, Tuple
from random import random

from src.core.card import Card
from src.ai.base_ai import Action, AIPlayer

########### 공용 함수들 ###########

def card_to_code(card: Card) -> str:
    r = card.rank.symbol
    if r == "10":
        r = "T"
    return r + card.suit.value

def to_codes(cards: List[Card]) -> List[str]:
    return [card_to_code(c) for c in cards]

RANKS = "23456789TJQKA"

def preflop_key_from_cards(hole_cards: List[Card]):
    c1, c2 = hole_cards
    r1, r2 = c1.rank.symbol, c2.rank.symbol
    s1, s2 = c1.suit, c2.suit
    suited = (s1 == s2)

    r1 = "T" if r1 == "10" else r1
    r2 = "T" if r2 == "10" else r2

    if RANKS.index(r1) > RANKS.index(r2):
        hi, lo = r1, r2
    else:
        hi, lo = r2, r1
    return (hi, lo, suited)

PREFLOP_TABLE = {
    ("A","A",False):0.85, ("K","K",False):0.82, ("Q","Q",False):0.80,
    ("J","J",False):0.78, ("T","T",False):0.75,
}

def get_preflop_strength(hole_cards):
    if len(hole_cards) != 2:
        return 0.5

    key = preflop_key_from_cards(hole_cards)
    if key in PREFLOP_TABLE:
        return PREFLOP_TABLE[key]

    hi, lo, suited = key
    base = 0.50
    if suited:
        base += 0.05
    return base

def pot_odds(pot: int, to_call: int):
    if to_call <= 0:
        return 0.0
    return to_call / (pot + to_call)

def street(board_codes):
    l = len(board_codes)
    if l == 0: return "pre"
    if l == 3: return "flop"
    if l == 4: return "turn"
    return "river"

########### 전략 베이스 ###########

class Strategy:
    def decide(
        self,
        ai: AIPlayer,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        opponents: List[AIPlayer],
    ) -> Tuple[Action, int]:
        raise NotImplementedError

########### 타이트 ###########

class TightStrategy(Strategy):
    def decide(self, ai, community_cards, pot, current_bet, opponents):

        board_codes = to_codes(community_cards)
        stage = street(board_codes)
        to_call = current_bet

        # 프리플랍
        if stage == "pre":
            pre = get_preflop_strength(ai.hole_cards)

            if to_call == 0:
                if pre >= 0.70:
                    amount = max(20, pot // 3 or 20)
                    return Action.RAISE, amount
                return Action.CHECK, 0

            po = pot_odds(pot, to_call)
            if pre >= 0.75: return Action.CALL, to_call
            if pre >= 0.60 and po < 0.25: return Action.CALL, to_call
            return Action.FOLD, 0

        # 플랍 이후
        strength = ai.hand_strength(ai.hole_cards, community_cards)
        po = pot_odds(pot, to_call)

        if strength >= 0.80:
            amount = max(20, pot // 2 or 20)
            return Action.RAISE, amount

        if strength >= 0.60:
            if to_call == 0: return Action.CHECK, 0
            if po <= 0.35: return Action.CALL, to_call
            return Action.FOLD, 0

        if strength >= 0.40:
            if to_call == 0: return Action.CHECK, 0
            if po <= 0.20: return Action.CALL, to_call
            return Action.FOLD, 0

        return Action.CHECK if to_call == 0 else Action.FOLD, 0

########### 루즈 ###########

class LooseStrategy(Strategy):
    def decide(self, ai, community_cards, pot, current_bet, opponents):

        board_codes = to_codes(community_cards)
        stage = street(board_codes)
        to_call = current_bet

        # 프리플랍
        if stage == "pre":
            pre = get_preflop_strength(ai.hole_cards)

            if to_call == 0:
                if pre >= 0.70:
                    amount = max(25, pot // 2 or 25)
                    return Action.RAISE, amount

                if pre >= 0.55 and random() < 0.4:
                    amount = max(15, pot // 4 or 15)
                    return Action.RAISE, amount

                return Action.CHECK, 0

            po = pot_odds(pot, to_call)
            if pre >= 0.65: return Action.CALL, to_call
            if pre >= 0.55 and po <= 0.35: return Action.CALL, to_call
            return Action.FOLD, 0

        # 플랍 이후
        strength = ai.hand_strength(ai.hole_cards, community_cards)
        po = pot_odds(pot, to_call)

        if strength >= 0.80:
            amount = max(20, pot // 2 or 20)
            return Action.RAISE, amount

        if strength >= 0.55:
            if to_call == 0:
                if random() < 0.3:
                    amount = max(10, pot // 4 or 10)
                    return Action.RAISE, amount
                return Action.CHECK, 0
            if po <= 0.45:
                return Action.CALL, to_call
            return Action.FOLD, 0

        if strength >= 0.35:
            if to_call == 0: return Action.CHECK, 0
            if po <= 0.25 and random() < 0.4:
                return Action.CALL, to_call
            return Action.FOLD, 0

        return Action.CHECK if to_call == 0 else Action.FOLD, 0