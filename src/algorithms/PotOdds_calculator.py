from src.algorithms.outs_calculator import PokerOutsCalculator

def pot_odds(pot, call_amount):
    """
    pot: 현재 팟 금액
    call_amount: 내가 콜해야 하는 금액
    반환: 팟 오즈 퍼센트 (예: 16.67%)

    """
    odds = call_amount / (pot + call_amount)        # 소수점 4자리까지 내부 계산
    percent = round(odds * 100, 2)                 # 퍼센트 변환 후 소수점 2자리 반올림
    return f"{percent}%"


print(pot_odds(100, 20))