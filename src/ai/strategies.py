# src/ai/strategies.py
import csv
import os
from typing import List, Tuple
from random import random

from src.core.card import Card
from src.ai.base_ai import Action, AIPlayer

RANKS = "23456789TJQKA"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 프리플랍 테이블 로드
PRE_TABLE = {}   # 키 = (높은카드, 낮은카드, 무늬일치여부)
pre_path = os.path.join(DATA_DIR, "preflop_winrates.csv")

with open(pre_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Rank 정규화
        r1 = row["Card1"].strip().upper()
        r2 = row["Card2"].strip().upper()

        # "10" → "T" 변환
        if r1 == "10": r1 = "T"
        if r2 == "10": r2 = "T"

        suited = row["Suited"].lower().strip() == "true"
        win = float(row["WinRate"])

        # CSV 오류 방지
        if r1 not in RANKS or r2 not in RANKS:
            print(f"⚠️ Warning: Invalid rank in CSV → ({r1}, {r2}) — row skipped")
            continue

        # hi/lo 정렬
        hi, lo = (r1, r2) if RANKS.index(r1) >= RANKS.index(r2) else (r2, r1)

        PRE_TABLE[(hi, lo, suited)] = win

# 포스트플랍 handrank 테이블 로드
POST_TABLE = {}  # key = (HandRank, Phase)
post_path = os.path.join(DATA_DIR, "handrank_winrates.csv")

with open(post_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rank = row["HandRank"]    # 예: "ONE_PAIR"
        phase = row["Phase"]      # 예: "Flop"
        win = float(row["WinRate"])

        POST_TABLE[(rank, phase)] = win

def card_to_code(card: Card) -> str:
    r = card.rank.symbol
    if r == "10":
        r = "T"
    return r + card.suit.value

def to_codes(cards: List[Card]) -> List[str]:
    return [card_to_code(c) for c in cards]



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

    hi, lo, suited = preflop_key_from_cards(hole_cards)

    key = (hi, lo, suited)
    if key in PRE_TABLE:
        return PRE_TABLE[key]

    # CSV에 없을 경우 기본값 사용
    return 0.50 if suited else 0.45

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

        rank, _, _ = ai.evaluator.evaluate_hand(ai.hole_cards + community_cards)
        phase = stage.capitalize()

        key = (rank.name, phase)
        if key in POST_TABLE:
            strength = POST_TABLE[key]

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
                    amount = max(20, pot // 3 or 20)
                    return Action.RAISE, amount
                return Action.CHECK, 0

            po = pot_odds(pot, to_call)
            if pre >= 0.75: return Action.CALL, to_call
            if pre >= 0.60 and po < 0.25: return Action.CALL, to_call
            return Action.FOLD, 0

        # 플랍 이후
        strength = ai.hand_strength(ai.hole_cards, community_cards)
        
        rank, _, _ = ai.evaluator.evaluate_hand(ai.hole_cards + community_cards)
        phase = stage.capitalize()    # flop → Flop, turn → Turn, river → River (대소문자 변환)

        key = (rank.name, phase)
        if key in POST_TABLE:
            strength = POST_TABLE[key]
        
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