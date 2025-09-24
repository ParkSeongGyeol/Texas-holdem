"""
게임 진행 로직 - 박성결 담당
게임 상태 관리 (FSM), 턴 진행, 베팅 라운드 구현
"""

from typing import List
from enum import Enum

from src.core.card import Deck, Card
from src.core.player import Player


class GamePhase(Enum):
    """게임 단계"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class PokerGame:
    """텍사스 홀덤 포커 게임 클래스"""

    def __init__(self):
        self.deck = Deck()
        self.players: List[Player] = []
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_phase = GamePhase.PREFLOP
        self.dealer_position = 0
        self.current_bet = 0

    def add_player(self, name: str, chips: int = 1000) -> None:
        """플레이어 추가"""
        player = Player(name, chips)
        self.players.append(player)

    def start(self) -> None:
        """게임 시작"""
        if len(self.players) < 2:
            print("게임을 시작하려면 최소 2명의 플레이어가 필요합니다.")
            return

        print("새 핸드를 시작합니다...")
        self.new_hand()

    def new_hand(self) -> None:
        """새 핸드 시작"""
        # TODO: 게임 초기화 로직 구현 (박성결)
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_phase = GamePhase.PREFLOP
        self.current_bet = 0

        # 플레이어 상태 리셋
        for player in self.players:
            player.reset_for_new_hand()

        # 홀 카드 딜링
        self.deal_hole_cards()
        self.display_game_state()

    def deal_hole_cards(self) -> None:
        """홀 카드 2장씩 딜링"""
        for _ in range(2):
            for player in self.players:
                if player.is_active:
                    player.receive_card(self.deck.deal())

    def deal_flop(self) -> None:
        """플롭 딜링 (3장)"""
        # TODO: 번 카드 처리 및 플롭 딜링 (박성결)
        self.deck.deal()  # Burn card
        for _ in range(3):
            self.community_cards.append(self.deck.deal())
        self.current_phase = GamePhase.FLOP

    def deal_turn(self) -> None:
        """턴 딜링 (1장)"""
        # TODO: 번 카드 처리 및 턴 딜링 (박성결)
        self.deck.deal()  # Burn card
        self.community_cards.append(self.deck.deal())
        self.current_phase = GamePhase.TURN

    def deal_river(self) -> None:
        """리버 딜링 (1장)"""
        # TODO: 번 카드 처리 및 리버 딜링 (박성결)
        self.deck.deal()  # Burn card
        self.community_cards.append(self.deck.deal())
        self.current_phase = GamePhase.RIVER

    def display_game_state(self) -> None:
        """현재 게임 상태 출력"""
        print(f"\\n--- 게임 상태 ---")
        print(f"단계: {self.current_phase.value}")
        print(f"팟: {self.pot}")
        community_str = " ".join([str(card) for card in self.community_cards])
        print(f"커뮤니티 카드: {community_str}")

        print("\\n플레이어:")
        for player in self.players:
            print(f"  {player}")
        print("------------------\\n")

    # TODO: 베팅 라운드, 팟 분배, 승자 판정 로직 구현 (박성결)