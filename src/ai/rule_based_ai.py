from typing import List, Tuple

from base_ai import AIPlayer, Action
from strategies import Strategy, TightStrategy

RANKS = "23456789TJQKA"

def rank_char(card: str) -> str:
    ch = card[0].upper()
    return "T" if ch == "1" else ch  # '10h' 같은 표기 대비

def hole_key(hole_cards: List[str]) -> Tuple[str, str, bool]:
    """
    프리플랍 테이블 조회용 키:
    (high_rank, low_rank, suited)
    예) 'Ah Kh' -> ('A','K', True), 'As Kd' -> ('A','K', False)
    """
    r1, r2 = rank_char(hole_cards[0]), rank_char(hole_cards[1])
    s1 = hole_cards[0][1] if len(hole_cards[0]) > 1 else "?"
    s2 = hole_cards[1][1] if len(hole_cards[1]) > 1 else "?"
    suited = (s1 == s2 and s1 not in ("?", " "))

    # high/low 정렬 (페어는 같음)
    if RANKS.index(r1) > RANKS.index(r2):
        hi, lo = r1, r2
    else:
        hi, lo = r2, r1
    return (hi, lo, suited)

# Heads-up 기준 대략적 프리플랍 승률(0~1) — 필요 시 값은 자유롭게 튜닝
HAND_STRENGTH_TABLE = {
    # Pairs
    ("A","A", False): 0.86, ("K","K", False): 0.82, ("Q","Q", False): 0.80,
    ("J","J", False): 0.78, ("T","T", False): 0.75, ("9","9", False): 0.72,
    ("8","8", False): 0.69, ("7","7", False): 0.66, ("6","6", False): 0.64,
    ("5","5", False): 0.62, ("4","4", False): 0.60, ("3","3", False): 0.58,
    ("2","2", False): 0.56,

    # Broadways (suited / offsuit)
    ("A","K", True): 0.67, ("A","K", False): 0.65,
    ("A","Q", True): 0.65, ("A","Q", False): 0.63,
    ("A","J", True): 0.63, ("A","J", False): 0.60,
    ("K","Q", True): 0.61, ("K","Q", False): 0.58,
    ("Q","J", True): 0.58, ("Q","J", False): 0.55,
    ("J","T", True): 0.57, ("J","T", False): 0.54,

    # Suited connectors
    ("T","9", True): 0.56, ("9","8", True): 0.55, ("8","7", True): 0.54,
    ("7","6", True): 0.53, ("6","5", True): 0.52,

    # Worst-ish offsuit sample
    ("7","2", False): 0.35,
}

def preflop_strength_from_table(hole_cards: List[str]) -> float:
    """
    프리플랍 강도 계산: 테이블 우선, 없으면 간단 휴리스틱으로 근사.
    """
    hi, lo, suited = hole_key(hole_cards)
    # 페어는 suited 의미 없음 → False 키로 고정
    if hi == lo:
        suited = False
    key = (hi, lo, suited)

    if key in HAND_STRENGTH_TABLE:
        return HAND_STRENGTH_TABLE[key]

    # 테이블에 없으면 브로드웨이/수딧/연결성으로 근사
    hi_i, lo_i = RANKS.index(hi), RANKS.index(lo)
    base = 0.33 + (hi_i / (len(RANKS) - 1)) * 0.22
    if suited:
        base += 0.03
    gap = hi_i - lo_i - 1
    if gap <= 0:
        base += 0.05
    elif gap == 1:
        base += 0.02
    return max(0.20, min(0.72, base))

class RuleBasedAI(AIPlayer):
    def __init__(self, name: str, chips: int = 1000, difficulty_level: int = 1, strategy: Strategy = None):
        super().__init__(name, chips, difficulty_level, strategy or TightStrategy())

    def analyze_hand_strength(self, hole_cards: List[str], community_cards: List[str]) -> float:

        # --- 프리플랍: 기본 확률 테이블 사용 ---
        if len(community_cards) == 0:
            return preflop_strength_from_table(hole_cards)
        
        # --- 플랍 이후: (임시) 기존 간단 규칙 유지 ---
        ranks = {c[0] for c in (hole_cards + community_cards)}
        if "A" in ranks: return 0.8
        if "K" in ranks: return 0.6
        return 0.4

    def make_decision(
        self,
        community_cards: List[str],
        pot: int,
        current_bet: int,
        opponents: List,
    ) -> Tuple[Action, int]:
        if self.strategy:
            return self.strategy.decide(self, community_cards, pot, current_bet, opponents)
        return (Action.CHECK if current_bet == 0 else Action.FOLD, 0)
        