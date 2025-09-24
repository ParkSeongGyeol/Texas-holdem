from rule_based_ai import RuleBasedAI  
from src.ai.base_ai import Action             

class Card:
    def __init__(self, rank, suit): 
        self.rank, self.suit = rank, suit
    def __repr__(self): 
        return f"{self.rank}{self.suit}"

def show(ai, hole, board, pot, to_call):
    ai.hole_cards = [Card(*hole[0]), Card(*hole[1])]
    action, amount = ai.make_decision(
        community_cards=[Card(*c) for c in board],
        pot=pot,
        current_bet=to_call,
        opponents=[],
    )
    print(f"[{ai.__class__.__name__}] hole={ai.hole_cards} "
          f"board={board} pot={pot} to_call={to_call} "
          f"-> {action.name}, {amount}")

if __name__ == "__main__":
    ai = RuleBasedAI("ONLY_ME")   # 실제 구현체 인스턴스 생성

    # 원하는 시나리오만 넣어서 네 AI만 확인
    show(ai, (("A","♠"), ("K","♥")), [], 100, 0)   # 프리플랍, 오픈 상황
    show(ai, (("7","♠"), ("2","♠")), [], 100, 10)  # 프리플랍, 콜해야 함
    show(ai, (("A","♠"), ("K","♥")), [("Q","♠"), ("J","♦"), ("2","♣")], 160, 20)  # 플랍 이후