import random
from rule_based_ai import RuleBasedAI
from strategies import TightStrategy, LooseStrategy
from base_ai import Action, Position


def apply_bet(player, amount, pot):
    """플레이어 칩에서 amount를 빼고 pot에 넣는다."""
    if amount <= 0:
        return pot
    player.chips -= amount
    return pot + amount

# ==========================
#   임시 덱 (Deck이 없어도 작동)
# ==========================
class FakeDeck:
    RANKS = "23456789TJQKA"
    SUITS = ["♠", "♥", "♦", "♣"]

    def __init__(self):
        self.cards = [r + s for r in self.RANKS for s in self.SUITS]
        random.shuffle(self.cards)

    def draw(self, n):
        result = self.cards[:n]
        self.cards = self.cards[n:]
        return result

# ==========================
# 현재 상태 출력 함수
# ==========================
def print_state(street, pot, current_bet, community, sb, bb):
    print(f"\n---- [{street.upper()}] ----")
    print(f"Pot = {pot}, Current Bet = {current_bet}")
    print(f"Board = {community}")
    print(f"SB({sb.name}) hand={sb.hole_cards}, chips={sb.chips}")
    print(f"BB({bb.name}) hand={bb.hole_cards}, chips={bb.chips}")
    print("----------------------------")

# ==========================
# AI vs AI 1판 테스트 함수
# ==========================
def run_one_hand():
    sb = RuleBasedAI("TIGHT_SB", strategy=TightStrategy())
    bb = RuleBasedAI("LOOSE_BB", strategy=LooseStrategy())

    sb.position = Position.SB
    bb.position = Position.BB

    # 덱 생성 → FakeDeck 사용
    deck = FakeDeck()

    # 카드 배분
    sb.hole_cards = deck.draw(2)
    bb.hole_cards = deck.draw(2)

    pot = 0
    current_bet = 0
    community_cards = []

    # ----- PREFLOP -----
    print_state("preflop", pot, current_bet, community_cards, sb, bb)

    # --- SB action ---
    action, amt = sb.make_decision([], pot, current_bet, [bb])
    print("SB ->", action.name, amt)

    if action == Action.RAISE:
        pot = apply_bet(sb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(sb, amt, pot)
    # --- BB action ---
    action, amt = bb.make_decision([], pot, current_bet, [sb])
    print("BB ->", action.name, amt)

    if action == Action.FOLD:
        print("BB 폴드 → SB 승리!")
        sb.chips += pot      # ★ SB에게 팟 지급
        pot = 0
        return

    if action == Action.RAISE:
        pot = apply_bet(bb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(bb, amt, pot)

    # ----- FLOP -----
    community_cards += deck.draw(3)
    current_bet = 0
    print_state("flop", pot, current_bet, community_cards, sb, bb)

    action, amt = sb.make_decision(community_cards, pot, current_bet, [bb])
    print("SB ->", action.name, amt)
    if action == Action.RAISE:
        pot = apply_bet(sb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(sb, amt, pot)

    # BB action
    action, amt = bb.make_decision(community_cards, pot, current_bet, [sb])
    print("BB ->", action.name, amt)

    if action == Action.FOLD:
        print("BB 폴드 → SB 승리!")
        sb.chips += pot
        pot = 0
        return

    if action == Action.RAISE:
        pot = apply_bet(bb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(bb, amt, pot)
        
    # ----- TURN -----
    community_cards += deck.draw(1)
    current_bet = 0
    print_state("turn", pot, current_bet, community_cards, sb, bb)

    action, amt = sb.make_decision(community_cards, pot, current_bet, [bb])
    print("SB ->", action.name, amt)
    if action == Action.RAISE:
        pot += amt
        current_bet = amt

    action, amt = bb.make_decision(community_cards, pot, current_bet, [sb])
    print("BB ->", action.name, amt)
    if action == Action.FOLD:
        print("BB 폴드 → SB 승리!")
        return

    if action == Action.RAISE:
        pot += amt
        current_bet = amt
    elif action == Action.CALL:
        pot += amt

    # ----- RIVER -----
    community_cards += deck.draw(1)
    current_bet = 0
    print_state("river", pot, current_bet, community_cards, sb, bb)

    action, amt = sb.make_decision(community_cards, pot, current_bet, [bb])
    print("SB ->", action.name, amt)

    if action == Action.RAISE:
        pot = apply_bet(sb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(sb, amt, pot)

    action, amt = bb.make_decision(community_cards, pot, current_bet, [sb])
    print("BB ->", action.name, amt)

    if action == Action.FOLD:
        print(f"\n===== 결과 =====\nBB 폴드 → SB({sb.name}) 승리! 팟 {pot} 획득")
        sb.chips += pot
        pot = 0
        return

    if action == Action.RAISE:
        pot = apply_bet(bb, amt, pot)
        current_bet = amt
    elif action == Action.CALL:
        pot = apply_bet(bb, amt, pot)

    # ----- SHOWDOWN -----
    print("\n===== SHOWDOWN =====")
    print("Board:", community_cards)
    print("SB:", sb.hole_cards)
    print("BB:", bb.hole_cards)
    
    winner = sb
    winner.chips += pot
    print(f"승자는 {winner.name} 입니다! 팟 {pot} 획득")
    pot = 0

if __name__ == "__main__":
    run_one_hand()