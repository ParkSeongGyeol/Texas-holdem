from __future__ import annotations
from typing import Dict

from base_ai import Position, Action
from rule_based_ai import RuleBasedAI, AdaptiveRuleBasedAI
from strategies import TightStrategy, LooseStrategy

# --------- AI 생성 헬퍼 ---------


def make_tight_bot(name: str = "TightBot") -> RuleBasedAI:
    return RuleBasedAI(name, strategy=TightStrategy())


def make_loose_bot(name: str = "LooseBot") -> RuleBasedAI:
    return RuleBasedAI(name, strategy=LooseStrategy())


def make_adaptive_bot(name: str = "AdaptiveBot") -> AdaptiveRuleBasedAI:
    return AdaptiveRuleBasedAI(name, base_style="tight")


# --------- 간단한 시나리오 정의 (AI vs AI 테스트 케이스) ---------

TEST_SCENARIOS = [
    # (설명, street, SB_hole, BB_hole, board, pot, current_bet_SB, current_bet_BB)
    ("PRE SB open with premium", "pre", ["A♠", "K♠"], ["Q♦", "J♦"], [], 0, 0, 0),
    ("PRE BB defend QJo vs open", "pre", ["T♠", "T♥"], ["Q♣", "J♣"], [], 30, 10, 10),
    ("FLOP SB c-bet A-high", "flop", ["A♠", "K♠"], ["9♣", "9♦"], ["A♦", "7♠", "2♣"], 40, 0, 0),
    ("FLOP BB mid pair", "flop", ["K♣", "Q♣"], ["8♠", "8♥"], ["Q♠", "7♦", "2♦"], 40, 10, 10),
    ("TURN SB", "turn", ["Q♠", "Q♥"], ["T♠", "9♠"], ["7♠", "2♥", "K♥", "J♣"], 80, 0, 0),
    ("RIVER BB facing bet", "river", ["9♠", "9♥"], ["T♠", "8♠"], ["Q♠", "8♦", "3♦", "2♥", "2♣"], 120, 40, 40),
]


# --------- AI 행동 시뮬레이션 ---------


def _play_one_scenario(
    desc: str,
    sb: RuleBasedAI,
    bb: RuleBasedAI,
    street: str,
    sb_hole,
    bb_hole,
    board,
    pot: int,
    bet_sb: int,
    bet_bb: int,
    stats: Dict[str, Dict[str, int]],
):
    """한 시나리오에서 SB / BB 각각 한 번씩 의사결정"""

    # SB 세팅 및 액션
    sb.position = Position.SB
    sb.hole_cards = sb_hole
    action_sb, amt_sb = sb.make_decision(board, pot, bet_sb, opponents=[bb])
    stats[sb.name][action_sb.name] += 1

    # BB 세팅 및 액션
    bb.position = Position.BB
    bb.hole_cards = bb_hole
    action_bb, amt_bb = bb.make_decision(board, pot, bet_bb, opponents=[sb])
    stats[bb.name][action_bb.name] += 1

    return (action_sb, amt_sb, action_bb, amt_bb)


def run_ai_vs_ai(sb_ai: RuleBasedAI, bb_ai: RuleBasedAI, repeat: int = 20):
    """
    AI vs AI 분석
    - 여러 시나리오를 반복 실행하면서 각 AI의 행동 빈도(체크/콜/레이즈/폴드)를 집계
    - 10주차: AI vs AI 시스템 구현
    - 12주차: AI 성능 분석용 데이터 생성
    """
    stats: Dict[str, Dict[str, int]] = {
        sb_ai.name: {a.name: 0 for a in Action},
        bb_ai.name: {a.name: 0 for a in Action},
    }

    for _ in range(repeat):
        for (
            desc,
            street,
            sb_hole,
            bb_hole,
            board,
            pot,
            bet_sb,
            bet_bb,
        ) in TEST_SCENARIOS:
            _play_one_scenario(
                desc,
                sb_ai,
                bb_ai,
                street,
                sb_hole,
                bb_hole,
                board,
                pot,
                bet_sb,
                bet_bb,
                stats,
            )

    return stats


# --------- 성능 분석 + 튜닝 제안 ---------


def analyze_behavior(stats: Dict[str, Dict[str, int]]):
    """
    AI 성능(행동 패턴) 분석
    - 레이즈/콜/폴드 비율을 계산해서 플레이 스타일 평가
    - 12주차: AI 성능 분석 / 전략 문서화 / 개선점 도출
    """
    report_lines = []
    for name, counters in stats.items():
        total = sum(counters.values()) or 1
        raise_rate = counters["RAISE"] / total
        call_rate = counters["CALL"] / total
        fold_rate = counters["FOLD"] / total
        check_rate = counters["CHECK"] / total

        report_lines.append(f"=== {name} ===")
        report_lines.append(
            f"RAISE {raise_rate:5.1%} / CALL {call_rate:5.1%} / CHECK {check_rate:5.1%} / FOLD {fold_rate:5.1%}"
        )

        if raise_rate > 0.45:
            report_lines.append("→ 매우 공격적인 스타일 (루즈/어그레시브). 블러핑 비율 점검 권장.")
        elif fold_rate > 0.4:
            report_lines.append("→ 너무 보수적인 스타일. 프리미엄 핸드 범위 확장 고려.")
        else:
            report_lines.append("→ 비교적 균형 잡힌 스타일.")

        report_lines.append("")

    return "\n".join(report_lines)


def suggest_tuning(stats: Dict[str, Dict[str, int]]):
    """
    간단한 파라미터 튜닝 아이디어 출력
    - 11주차: AI 파라미터 튜닝 / 밸런싱 작업
    """
    suggestions = []
    for name, counters in stats.items():
        total = sum(counters.values()) or 1
        raise_rate = counters["RAISE"] / total
        fold_rate = counters["FOLD"] / total

        suggestions.append(f"=== {name} 튜닝 제안 ===")
        if raise_rate > 0.5:
            suggestions.append(
                "- 레이즈 임계값(raise_th)을 +0.02 ~ +0.05 정도 상향해서 지나친 공격성 완화."
            )
        if fold_rate > 0.5:
            suggestions.append(
                "- 콜 임계값(call_th)을 -0.02 ~ -0.05 정도 낮춰서 지나친 폴드 경향 보정."
            )
        if 0.3 <= raise_rate <= 0.5 and fold_rate < 0.4:
            suggestions.append("- 현재 파라미터는 대체로 균형적입니다.")
        suggestions.append("")

    return "\n".join(suggestions)


# 이 파일을 직접 실행했을 때 간단 테스트 -----------------
    
if __name__ == "__main__":
        # 1) 타이트 vs 루즈
    sb_ai = make_tight_bot("TIGHT_SB")
    bb_ai = make_loose_bot("LOOSE_BB")

    stats = run_ai_vs_ai(sb_ai, bb_ai, repeat=10)
    print("[TIGHT vs LOOSE]")
    print(analyze_behavior(stats))
    print(suggest_tuning(stats))

    # 2) 적응형 vs 루즈
    sb_ai = make_adaptive_bot("ADAPT_SB")
    bb_ai = make_loose_bot("LOOSE_BB2")

    stats = run_ai_vs_ai(sb_ai, bb_ai, repeat=10)
    print("\n[ADAPT vs LOOSE]")
    print(analyze_behavior(stats))
    print(suggest_tuning(stats))