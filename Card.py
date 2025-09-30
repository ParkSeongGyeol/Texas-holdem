import random

class Card:
    def __init__(self, 모양, 숫자):
        self.모양 = 모양
        self.숫자 = 숫자

    def __str__(self):
        return f"{self.모양}{self.숫자}"  # 예: ♠A ♥10

class Deck:
    def __init__(self):
        모양들 = ["♠", "♥", "♦", "♣"]
        숫자들 = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.cards = [Card(모양, 숫자) for 모양 in 모양들 for 숫자 in 숫자들]

    def 섞기(self):
        random.shuffle(self.cards)

    def 뽑기(self):
        return self.cards.pop() if self.cards else None


# 실행 테스트
if __name__ == "__main__":
    deck = Deck()
    deck.섞기()
    for _ in range(5):
        print(deck.뽑기())

        #3장, 1장, 1장을 순차적으로 뽑는 실제 게임 룰에 적용할 것.