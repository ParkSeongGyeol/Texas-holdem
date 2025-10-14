from base_ai import Action, Position
from rule_based_ai import RuleBasedAI
from strategies import TightStrategy, LooseStrategy

def run_case(title, ai, pos, hole, board, pot, current_bet):
    ai.position = pos
    ai.hole_cards = hole
    action, amt = ai.make_decision(board, pot, current_bet, opponents=[])
    print(f"[{title}] pos={pos.name:>2} hole={hole} board={board} pot={pot} bet={current_bet} -> {action.name} {amt}")

def test():
    # 두 타입의 AI 준비
    tight = RuleBasedAI("TIGHT", strategy=TightStrategy())
    loose = RuleBasedAI("LOOSE", strategy=LooseStrategy())

    # ---------- 프리플랍 테스트 ----------
    # 1) Tight SB, 프리미엄 (AKs) → 오픈 레이즈 기대
    run_case("PRE SB premium (AKs)", tight, Position.SB, ["A♠","K♠"], [], pot=0, current_bet=0)

    # 2) Tight SB, 비프리미엄 (AJo offsuit) → 체크/폴드 기대
    run_case("PRE SB non-prem (AJo)", tight, Position.SB, ["A♠","J♦"], [], pot=0, current_bet=0)
    run_case("PRE SB non-prem facing bet", tight, Position.SB, ["A♠","J♦"], [], pot=30, current_bet=10)

    # 3) Loose BB, 상대 오픈(수비) → 콜/3bet 판단
    run_case("PRE BB defend KQo vs open", loose, Position.BB, ["K♣","Q♦"], [], pot=30, current_bet=10)

    # ---------- 플랍 테스트 ----------
    # 4) Tight SB, 탑페어 탑키커 느낌 (A-high board) → C-bet 기대
    run_case("FLOP SB c-bet A-high", tight, Position.SB, ["A♠","K♦"], ["A♥","7♣","2♦"], pot=40, current_bet=0)

    # 5) Loose BB, 미들페어/드로우 없음 → 체크/소액 프로브/콜 판단
    run_case("FLOP BB mid/weak", loose, Position.BB, ["8♣","6♦"], ["Q♠","7♥","2♣"], pot=40, current_bet=10)

    # 6) Loose SB, 세미블러프 후보 (플러시/스트레이트 드로우 비슷 케이스)
    run_case("FLOP SB probe/semibluff-ish", loose, Position.SB, ["J♠","T♠"], ["2♠","7♦","A♣"], pot=40, current_bet=0)

    # ---------- 턴/리버 테스트 ----------
    run_case("TURN SB", tight, Position.SB, ["Q♠","Q♦"], ["7♣","2♦","2♣","K♥"], pot=80, current_bet=0)
    run_case("RIVER BB facing bet", tight, Position.BB, ["9♠","9♦"], ["Q♣","8♦","3♠","2♥","2♦"], pot=120, current_bet=40)

if __name__ == "__main__":
    test()