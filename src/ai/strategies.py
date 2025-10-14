from abc import ABC, abstractmethod
from typing import List, Tuple

from base_ai import Action ,AIPlayer, Position

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

        pot_odds_th = pot_odds_threshold(pot, current_bet)
        
        # 기본 임계값(타이트)
        raise_th_pre, call_th_pre   = 0.72, 0.52
        raise_th_post, call_th_post = 0.70, 0.55

        if st == "pre":
            if not is_premium(ai.hole_cards):
                # 공짜면 체크, 상대가 베팅/오픈했으면 폴드
                return (Action.CHECK, 0) if current_bet == 0 else (Action.FOLD, 0)
            
            if ai.position == Position.SB and current_bet == 0 and is_premium(ai.hole_cards):
                return (Action.RAISE, open_bet_size(pot))
            
            bias = HU_PRE_BIAS.get(ai.position, 0.0)
            raise_th, call_th = raise_th_pre + bias, call_th_pre + bias * 0.6
        else:
            bias = HU_POST_BIAS.get(ai.position, 0.0)
            raise_th, call_th = raise_th_post + bias, call_th_post + bias * 0.6

        # BB 수비(상대 오픈에 대해 콜 임계 소폭 완화)
        if st == "pre" and current_bet > 0 and ai.position == Position.BB:
            call_th -= 0.05
       
        pot_odds_th = pot_odds_threshold(pot, current_bet)
        call_th = max(call_th, pot_odds_th)
        
        if st == "pre" and current_bet > 0 and ai.position == Position.BB:
            call_th = max(pot_odds_th, call_th - 0.05)

        # ----- 액션 결정 -----
        if current_bet == 0:
            # 오픈/씨벳: 강하면 베팅, 아니면 체크
            if strength >= raise_th:
                bet = open_bet_size(pot) if st == "pre" else cbet_size(pot)
                return (Action.RAISE, bet)
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

        pot_odds_th = pot_odds_threshold(pot, current_bet)

        # 기본 임계값(루즈)
        raise_th_pre,  call_th_pre  = 0.58, 0.30
        raise_th_post, call_th_post = 0.60, 0.40

        if st == "pre":
            bias = HU_PRE_BIAS.get(ai.position, 0.0) * 0.5      # 루즈는 완만하게만 반영
            raise_th, call_th = raise_th_pre + bias, max(0.12, call_th_pre + bias * 0.6)
        else:
            bias = HU_POST_BIAS.get(ai.position, 0.0) * 0.8     # 플랍 이후 SB 이점 강화
            raise_th, call_th = raise_th_post + bias, max(0.18, call_th_post + bias * 0.6)

        # BB 수비 강화
        if st == "pre" and current_bet > 0 and ai.position == Position.BB:
            call_th = max(pot_odds_th - 0.04, call_th - 0.08)

        pot_odds_th = pot_odds_threshold(pot, current_bet)
        call_th = max(call_th, pot_odds_th - 0.02)

        if current_bet == 0:
            if strength >= raise_th:
                bet = open_bet_size(pot) if street == "pre" else cbet_size(pot)
                return (Action.RAISE, bet)

            # SB 프리플랍 스틸(살짝 강하면 소액 오픈)
            if ai.position == Position.SB and street == "pre" and strength >= call_th + 0.12:
                return (Action.RAISE, max(10, pot // 5))

            # 플랍/턴 중간 강도 프로브
            if street in ("flop", "turn") and 0.45 <= strength < raise_th:
                return (Action.RAISE, max(10, pot // 3))

            return (Action.CHECK, 0)

        # 루즈는 리레이즈 임계 조금 낮춤
        reraise_th = min(0.95, raise_th + 0.05)
        if strength >= reraise_th:
            return (Action.RAISE, reraise_size(current_bet))

        if strength >= call_th:
            return (Action.CALL, current_bet)

        return (Action.FOLD, 0)
