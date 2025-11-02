from abc import ABC, abstractmethod
from typing import List, Tuple

from base_ai import Action ,AIPlayer, Position
from random import random #블러핑 확률용

def pot_odds_threshold(pot: int, current_bet: int) -> float:
    """팟오즈 기반 콜 손익분기점 (0~1)"""
    if current_bet <= 0:
        return 0.0
    return current_bet / (pot + current_bet + 1e-6)

PREMIUM_SET = {
    ("A","A", False), ("K","K", False), ("Q","Q", False), ("J","J", False), ("T","T", False),
    ("A","K", True), ("A","Q", True), ("A","J", True), ("K","Q", True),
    ("A","K", False), ("A","Q", False),
}
RANKS = "23456789TJQKA"

def rank_char(card: str) -> str:
    ch = card[0].upper()
    return "T" if ch == "1" else ch

def hole_key_simple(hole_cards: List[str]) -> Tuple[str, str, bool]:
    r1, r2 = rank_char(hole_cards[0]), rank_char(hole_cards[1])
    s1 = hole_cards[0][1] if len(hole_cards[0]) > 1 else "?"
    s2 = hole_cards[1][1] if len(hole_cards[1]) > 1 else "?"
    suited = (s1 == s2 and s1 not in ("?", " "))
    if RANKS.index(r1) > RANKS.index(r2):
        hi, lo = r1, r2
    else:
        hi, lo = r2, r1
    if hi == lo:
        suited = False
    return (hi, lo, suited)

def is_premium(hole_cards: List[str]) -> bool:
    return hole_key_simple(hole_cards) in PREMIUM_SET

class Strategy(ABC):
    @abstractmethod
    def decide(
        self,
        ai: AIPlayer,
        community_cards: List[str],
        pot: int,
        current_bet: int,
        opponents: List,
    ) -> Tuple[Action, int] : pass

def open_bet_size(pot: int) -> int:
    return max(10, pot // 4)

# 오픈된 카드 수 확인
def street(community_cards: List[str]) -> str:
    l = len(community_cards)
    if l == 0:  return "pre"
    if l == 3:  return "flop"
    if l == 4:  return "turn"
    return "river"

def cbet_size(pot: int) -> int:
    # 플랍 이후 기본 컨티뉴에이션 베팅: 팟의 1/2
    return max(10, pot // 2)

def reraise_size(current_bet: int) -> int:
    # 상대 베팅에 대한 재레이즈 크기(약 2.5배)
    return max(20, int(current_bet * 2.5))

HU_PRE_BIAS  = {Position.SB: -0.02, Position.BB: -0.00} #프리플랍(플랍 전)
HU_POST_BIAS = {Position.SB: -0.05, Position.BB: +0.02} #플랍 이후 

class TightStrategy(Strategy): 
    def decide(self, ai, community_cards, pot, current_bet, opponents) : 
        strength = ai.analyze_hand_strength(ai.hole_cards, community_cards)
        st = street(community_cards)

        # ---------- 프리미엄 게이트 (타이트 전용) ----------
        if st == "pre":
                # 공짜면 체크, 상대가 베팅/오픈했으면 폴드
            if not is_premium(ai.hole_cards):
                return (Action.CHECK, 0) if current_bet == 0 else (Action.FOLD, 0)
            if ai.position == Position.SB and current_bet == 0 and is_premium(ai.hole_cards):
                return (Action.RAISE, open_bet_size(pot))

        # ---------- 기본 임계 ----------
        raise_th_pre, call_th_pre   = 0.72, 0.52
        raise_th_post, call_th_post = 0.70, 0.55
        if st == "pre": 
            bias = HU_PRE_BIAS.get(ai.position, 0.0)
            raise_th, call_th = raise_th_pre + bias, call_th_pre + bias * 0.6
        else:
            bias = HU_POST_BIAS.get(ai.position, 0.0)
            raise_th, call_th = raise_th_post + bias, call_th_post + bias * 0.6
        
        # ---------- 팟오즈 반영 (항상 1회) ----------  
        pot_odds_th = pot_odds_threshold(pot, current_bet)
        call_th = max(call_th, pot_odds_th)

        # ---------- BB 수비 (프리플랍, 상대 오픈에 한정) ----------
        if st == "pre" and current_bet > 0 and ai.position == Position.BB:
            call_th = max(pot_odds_th, call_th - 0.05)

        # ---------- 액션 ----------
        if current_bet == 0:
            # 강하면 오픈/씨벳
            if strength >= raise_th:
                bet = open_bet_size(pot) if st == "pre" else cbet_size(pot)
                return (Action.RAISE, bet)
            # (타이트) SB이고 플랍/턴에서 아주 낮은 확률로 스틸 (약간 약할 때만) 
            if st in ("flop", "turn") and ai.position == Position.SB and 0.42 <= strength < raise_th:
                if random() < 0.03:  # 3%
                    return (Action.RAISE, max(10, pot // 3))
            return (Action.CHECK, 0)
        
        # 리레이즈(3bet/레이즈 백): 아주 강할 때
        reraise_th = min(0.98, raise_th + 0.08)  # 타이트는 더 강해야 리레이즈
        if strength >= reraise_th:
            return (Action.RAISE, reraise_size(current_bet))
        # 콜: 강도 >= 콜 임계(= max(기본, 팟오즈))
        if strength >= call_th:
            return (Action.CALL, current_bet)
        # 그 외 폴드
        return (Action.FOLD, 0)

class LooseStrategy(Strategy): 
    def decide(self, ai, community_cards, pot, current_bet, opponents) : 
        strength = ai.analyze_hand_strength(ai.hole_cards, community_cards)
        st = street(community_cards)

        # ---------- 기본 임계 (루즈는 완만) ----------
        raise_th_pre,  call_th_pre  = 0.58, 0.30
        raise_th_post, call_th_post = 0.60, 0.40

        if st == "pre":
            bias = HU_PRE_BIAS.get(ai.position, 0.0) * 0.5      # 루즈는 완만하게만 반영
            raise_th, call_th = raise_th_pre + bias, max(0.12, call_th_pre + bias * 0.6)
        else:
            bias = HU_POST_BIAS.get(ai.position, 0.0) * 0.8     # 플랍 이후 SB 이점 강화
            raise_th, call_th = raise_th_post + bias, max(0.18, call_th_post + bias * 0.6)
        
        # ---------- 팟오즈 반영 (한 번) ----------
        pot_odds_th = pot_odds_threshold(pot, current_bet)
        call_th = max(call_th, pot_odds_th - 0.02)

        # ---------- BB 수비 (프리플랍, 상대 오픈 시) ----------
        if st == "pre" and current_bet > 0 and ai.position == Position.BB:
            call_th = max(pot_odds_th - 0.04, call_th - 0.08)
        
        # ---------- 액션 ----------
        if current_bet == 0:
            # 강하면 오픈/씨벳
            if strength >= raise_th:
                bet = open_bet_size(pot) if st == "pre" else cbet_size(pot)
                return (Action.RAISE, bet)

            # SB 프리플랍 스틸: call_th보다 살짝 높으면 소액 오픈
            if ai.position == Position.SB and st == "pre" and strength >= call_th + 0.12:
                return (Action.RAISE, max(10, pot // 5))

            # 플랍/턴 중간 강도 프로브 (정보 수집 + 폴드 이득)
            if st in ("flop", "turn") and 0.45 <= strength < raise_th:
                return (Action.RAISE, max(10, pot // 3))
            
            # 체크 상황 블러핑(확률)
            if st in ("flop", "turn") and random() < 0.12:  # 12%
                return (Action.RAISE, max(10, pot // 3))
            return (Action.CHECK, 0)

        # 상대 베팅에 맞서는 구간
        # 리레이즈(3bet): 루즈는 조금 낮은 기준
        reraise_th = min(0.95, raise_th + 0.05)
        if strength >= reraise_th:
            return (Action.RAISE, reraise_size(current_bet))

        # 페이스 블러핑(확률): SB이고 리버 전, 약할 때 가끔 레이즈 압박
        if st in ("flop", "turn") and ai.position == Position.SB and strength < call_th:
            if random() < 0.08:  # 8%
                return (Action.RAISE, max(10, pot // 3))
        # 콜
        if strength >= call_th:
            return (Action.CALL, current_bet)

        return (Action.FOLD, 0)
