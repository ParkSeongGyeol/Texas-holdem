import random

class Card:
    def __init__(self, 모양, 숫자):
        self.모양 = 모양
        self.숫자 = 숫자

    def __str__(self):
        return f"{self.모양}{self.숫자}"  # 예: ♠A, ♥10

class Deck:
    def __init__(self):
        모양들 = ["♠", "♥", "♦", "♣"]
        숫자들 = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.cards = [Card(모양, 숫자) for 모양 in 모양들 for 숫자 in 숫자들]

    def 섞기(self):
        random.shuffle(self.cards)

    def 뽑기(self):
        return self.cards.pop() if self.cards else None


# 테스트
if __name__ == "__main__":
    deck = Deck()
    deck.섞기()
    for _ in range(5):
        print(deck.뽑기())

        # 3장, 1장, 1장을 순차적으로 뽑는 실제 게임 룰에 적용할 것.

        from itertools import combinations

# 족보 판정 클래스
class HandEvaluator:
    순위 = {
        "로열플러시": 10,
        "스트레이트플러시": 9,
        "포카드": 8,
        "풀하우스": 7,
        "플러시": 6,
        "스트레이트": 5,
        "트리플": 4,
        "투페어": 3,
        "원페어": 2,
        "하이카드": 1
    }

    숫자값 = {
        "A": 14, "K": 13, "Q": 12, "J": 11,
        "10": 10, "9": 9, "8": 8, "7": 7,
        "6": 6, "5": 5, "4": 4, "3": 3, "2": 2
    }

    @staticmethod
    def 평가(카드7장):
        # 가능한 7장 중 5장 조합 모두 비교
        최고패 = None
        최고점수 = (0, [])

        for 조합 in combinations(카드7장, 5):
            족보명, 점수 = HandEvaluator.패평가(list(조합))
            if 점수 > 최고점수:
                최고패 = list(조합)
                최고점수 = 점수

        return 최고패, 최고점수

    @staticmethod
    def 패평가(카드5장):
        모양들 = [c.모양 for c in 카드5장]
        숫자들 = sorted([HandEvaluator.숫자값[c.숫자] for c in 카드5장], reverse=True)

        # 같은 숫자 개수 세기
        counts = {v: 숫자들.count(v) for v in set(숫자들)}
        count_values = sorted(counts.values(), reverse=True)

        is_flush = len(set(모양들)) == 1
        is_straight = HandEvaluator.is_straight(숫자들)

        # 족보 판정
        if is_flush and is_straight and max(숫자들) == 14:
            return "로열플러시", (10, 숫자들)
        elif is_flush and is_straight:
            return "스트레이트플러시", (9, 숫자들)
        elif 4 in count_values:
            return "포카드", (8, 숫자들)
        elif 3 in count_values and 2 in count_values:
            return "풀하우스", (7, 숫자들)
        elif is_flush:
            return "플러시", (6, 숫자들)
        elif is_straight:
            return "스트레이트", (5, 숫자들)
        elif 3 in count_values:
            return "트리플", (4, 숫자들)
        elif count_values.count(2) == 2:
            return "투페어", (3, 숫자들)
        elif 2 in count_values:
            return "원페어", (2, 숫자들)
        else:
            return "하이카드", (1, 숫자들)

    @staticmethod
    def is_straight(숫자들):
        """연속된 숫자인지 판단"""
        숫자셋 = sorted(set(숫자들), reverse=True)
        # A(14)를 1로 처리하는 예외(5,4,3,2,A)
        if set([14, 5, 4, 3, 2]).issubset(숫자셋):
            return True
        for i in range(len(숫자셋) - 4):
            if 숫자셋[i] - 숫자셋[i + 4] == 4:
                return True
        return False
    
    @staticmethod
    def 비교(player1_cards, player2_cards):
        """두 플레이어 중 누가 이기는지 비교"""
        p1_hand, p1_score = HandEvaluator.평가(player1_cards)
        p2_hand, p2_score = HandEvaluator.평가(player2_cards)

        if p1_score > p2_score:
            return "플레이어 1 승!", p1_hand, p1_score
        elif p2_score > p1_score:
            return "플레이어 2 승!", p2_hand, p2_score
        else:
            return "무승부!", p1_hand, p2_hand


# 테스트 코드
if __name__ == "__main__":
    deck = Deck()
    deck.섞기()

    # 두 플레이어에게 7장씩 나눠줌 (텍사스 홀덤의 쇼다운 시점과 유사)
    player1_cards = [deck.뽑기() for _ in range(7)]
    player2_cards = [deck.뽑기() for _ in range(7)]

    print("플레이어 1 카드:", " ".join(str(c) for c in player1_cards))
    print("플레이어 2 카드:", " ".join(str(c) for c in player2_cards))

    # 승자 비교 (핵심 추가)
    결과, 패, 점수 = HandEvaluator.비교(player1_cards, player2_cards)

    print("\n결과:", 결과)
    print("승리한 패:", " ".join(str(c) for c in 패))
    print("점수:", 점수)
    #텍사스 홀덤의 진행과정 중 쇼다운 시점의 역할 수행
    #7장의 카드들 중 최상의 족보를 계산하는 프로그램.
    #추가) n명의 플레이어의 손패와 그 족보들을 비교해주는 프로그램.