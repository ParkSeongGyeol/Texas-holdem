from src.algorithms.outs_calculator import PokerOutsCalculator

#  outs: 승리로 이어지는 카드 수
#  known_cards: 현재 보이는 카드 수 (핸드+보드)
#  내 핸드가 메이드 되는 확률 계산

def hand_winrates1(outs, known_cards):
    """

    단순 확률 계산
    반환: 승률(퍼센트), 소수점 2자리

    """
    total_cards=52
    remaining = total_cards - known_cards
    winrates = (outs / remaining) * 100  # 단순 확률 계산
    return round(winrates, 2)

def hand_winrates2(outs, known_cards):
    """

    플랍 때, 턴과 리버(앞으로 2장을 더 받음) 고려해서 확률 계산
    반환: 승률(퍼센트), 소수점 2자리

    """
    total_cards = 52
    remaining = total_cards - known_cards  # 남은 카드 수
    
    # 턴/리버에서 아웃츠 안 나올 확률 계산
    no_outs_on_turn = (remaining - outs) / remaining
    no_outs_on_river = (remaining - 1 - outs) / (remaining - 1)
    
    # 전체 승률 = 1 - (턴에서 안 나오고 리버에서 안 나올 확률)
    winrates = 1 - (no_outs_on_turn * no_outs_on_river)
    
    return round(winrates * 100, 2)


# 플랍때는 hand_winrates2로 확률 계산(앞으로 2턴 남은걸 고려)
# 턴 때는 앞으로 한턴 남았기 때문에 hand_winrates1으로 계산
