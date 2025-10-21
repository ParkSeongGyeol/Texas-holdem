"""
게임 진행 로직 - 박성결 담당
게임 상태 관리 (FSM), 턴 진행, 베팅 라운드 구현
"""

from typing import List, Optional, Dict, Tuple
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


class Action(Enum):
    """플레이어 액션"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class PokerGame:
    """
    텍사스 홀덤 포커 게임 클래스

    Week 3-7 Features (박성결):
    - Week 3: 게임 규칙 및 상태 다이어그램 설계, 턴 관리 시스템
    - Week 4: Player 클래스 구현, 핸드 관리
    - Week 5: 팟 구조, 베팅/레이즈/폴드 로직
    - Week 6: 베팅 액션 처리, 사이드 팟, 올인 상황
    - Week 7: 승자 결정, 게임 플로우 테스트, 디버그 기능
    """

    def __init__(self, small_blind: int = 10, big_blind: int = 20):
        """
        게임 초기화

        Args:
            small_blind: 스몰 블라인드 금액 (기본값: 10)
            big_blind: 빅 블라인드 금액 (기본값: 20)
        """
        self.deck = Deck()
        self.players: List[Player] = []
        self.community_cards: List[Card] = []
        self.pot = 0
        self.side_pots: List[Dict] = []  # Week 6: 사이드 팟
        self.current_phase = GamePhase.PREFLOP
        self.dealer_position = 0
        self.current_bet = 0
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.current_player_index = 0
        self.last_raiser_index = -1
        self.min_raise = big_blind

        # Week 7: 디버그 모드
        self.debug_mode = False
        self.action_history: List[str] = []

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
        print(f"\n--- 게임 상태 ---")
        print(f"단계: {self.current_phase.value}")
        print(f"팟: {self.pot}")
        if self.side_pots:
            print(f"사이드 팟: {self.side_pots}")
        community_str = " ".join([str(card) for card in self.community_cards]) if self.community_cards else "없음"
        print(f"커뮤니티 카드: {community_str}")
        print(f"현재 베팅: {self.current_bet}")

        print("\n플레이어:")
        for i, player in enumerate(self.players):
            dealer_marker = " [D]" if i == self.dealer_position else ""
            current_marker = " <--" if i == self.current_player_index else ""
            print(f"  {player}{dealer_marker}{current_marker}")
        print("------------------\n")

    # ===== Week 3: 턴 관리 시스템 =====

    def get_active_players(self) -> List[Player]:
        """활성 플레이어 목록 반환 (폴드하지 않은 플레이어)"""
        return [p for p in self.players if not p.has_folded and p.is_active]

    def get_players_who_can_act(self) -> List[Player]:
        """액션을 수행할 수 있는 플레이어 목록"""
        return [p for p in self.players if p.can_act()]

    def next_player(self) -> Optional[Player]:
        """다음 플레이어로 이동"""
        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

            # 한 바퀴 돌았으면 None 반환
            if self.current_player_index == start_index:
                return None

            player = self.players[self.current_player_index]
            if player.can_act():
                return player

    def is_betting_round_complete(self) -> bool:
        """
        베팅 라운드가 완료되었는지 확인

        Returns:
            모든 플레이어가 같은 금액을 베팅했거나 폴드/올인한 경우 True
        """
        active_players = self.get_active_players()

        if len(active_players) <= 1:
            return True

        players_who_can_act = self.get_players_who_can_act()

        # 액션 가능한 플레이어가 없으면 라운드 종료
        if not players_who_can_act:
            return True

        # 모든 액션 가능한 플레이어가 같은 금액을 베팅했는지 확인
        for player in players_who_can_act:
            if player.current_bet != self.current_bet:
                return False

        return True

    # ===== Week 5: 베팅 라운드 구현 =====

    def post_blinds(self) -> None:
        """블라인드 배팅"""
        if len(self.players) < 2:
            return

        # 스몰 블라인드
        sb_position = (self.dealer_position + 1) % len(self.players)
        sb_player = self.players[sb_position]
        if sb_player.can_act():
            sb_amount = sb_player.bet(min(self.small_blind, sb_player.chips))
            self.pot += sb_amount
            self.log_action(f"{sb_player.name}가 스몰 블라인드 {sb_amount} 베팅")

        # 빅 블라인드
        bb_position = (self.dealer_position + 2) % len(self.players)
        bb_player = self.players[bb_position]
        if bb_player.can_act():
            bb_amount = bb_player.bet(min(self.big_blind, bb_player.chips))
            self.pot += bb_amount
            self.current_bet = bb_amount
            self.log_action(f"{bb_player.name}가 빅 블라인드 {bb_amount} 베팅")

        # 첫 액션 플레이어는 빅 블라인드 다음
        self.current_player_index = (bb_position + 1) % len(self.players)
        self.last_raiser_index = bb_position

    def betting_round(self) -> None:
        """
        베팅 라운드 진행

        Week 5: 체크/콜/레이즈/폴드 로직
        """
        if len(self.get_active_players()) <= 1:
            return

        # 베팅 라운드 시작 전 상태 초기화
        if self.current_phase != GamePhase.PREFLOP:
            self.current_bet = 0
            for player in self.players:
                player.current_bet = 0
            self.current_player_index = (self.dealer_position + 1) % len(self.players)
            self.last_raiser_index = -1

        rounds_without_action = 0
        max_rounds = len(self.players) * 2  # 무한 루프 방지

        while not self.is_betting_round_complete() and rounds_without_action < max_rounds:
            player = self.players[self.current_player_index]

            if not player.can_act():
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                continue

            # 플레이어 액션 받기
            action, amount = self.get_player_action(player)
            self.process_action(player, action, amount)

            # 다음 플레이어로
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            rounds_without_action += 1

        # 라운드 종료 후 팟에 베팅 추가
        self.collect_bets()

    def get_player_action(self, player: Player) -> Tuple[Action, int]:
        """
        플레이어로부터 액션을 받음 (임시로 간단한 입력 처리)

        Args:
            player: 액션을 수행할 플레이어

        Returns:
            (Action, amount) 튜플
        """
        print(f"\n{player.name}의 차례 (칩: {player.chips}, 현재 베팅: {player.current_bet})")
        print(f"현재 콜 금액: {self.current_bet - player.current_bet}")

        # 가능한 액션 표시
        available_actions = self.get_available_actions(player)
        print(f"가능한 액션: {[a.value for a in available_actions]}")

        # 간단한 입력 처리 (나중에 AI로 대체)
        while True:
            action_input = input("액션을 선택하세요 (fold/check/call/raise/allin): ").strip().lower()

            if action_input == "fold":
                return (Action.FOLD, 0)
            elif action_input == "check" and Action.CHECK in available_actions:
                return (Action.CHECK, 0)
            elif action_input == "call" and Action.CALL in available_actions:
                return (Action.CALL, self.current_bet - player.current_bet)
            elif action_input == "raise" and Action.RAISE in available_actions:
                min_raise_amount = self.current_bet - player.current_bet + self.min_raise
                max_raise_amount = player.chips
                print(f"레이즈 금액 입력 ({min_raise_amount} ~ {max_raise_amount}): ", end="")
                try:
                    raise_amount = int(input())
                    if min_raise_amount <= raise_amount <= max_raise_amount:
                        return (Action.RAISE, raise_amount)
                except ValueError:
                    pass
                print("올바른 금액을 입력하세요.")
            elif action_input == "allin" and Action.ALL_IN in available_actions:
                return (Action.ALL_IN, player.chips)
            else:
                print("올바른 액션을 선택하세요.")

    def get_available_actions(self, player: Player) -> List[Action]:
        """플레이어가 수행 가능한 액션 목록"""
        actions = [Action.FOLD]

        call_amount = self.current_bet - player.current_bet

        if call_amount == 0:
            actions.append(Action.CHECK)

        if call_amount > 0 and player.chips >= call_amount:
            actions.append(Action.CALL)

        if player.chips > call_amount + self.min_raise:
            actions.append(Action.RAISE)

        if player.chips > 0:
            actions.append(Action.ALL_IN)

        return actions

    # ===== Week 6: 액션 처리 및 사이드 팟 =====

    def process_action(self, player: Player, action: Action, amount: int) -> None:
        """
        플레이어 액션 처리

        Week 6: 베팅 액션 처리, 올인 상황 처리
        """
        if action == Action.FOLD:
            player.fold()
            self.log_action(f"{player.name}가 폴드했습니다")

        elif action == Action.CHECK:
            self.log_action(f"{player.name}가 체크했습니다")

        elif action == Action.CALL:
            call_amount = self.current_bet - player.current_bet
            actual_bet = player.bet(call_amount)
            self.log_action(f"{player.name}가 {actual_bet} 콜했습니다")

            if player.is_all_in:
                self.log_action(f"{player.name}가 올인했습니다!")

        elif action == Action.RAISE:
            # 현재 베팅과의 차액 + 레이즈 금액
            call_amount = self.current_bet - player.current_bet
            total_bet = call_amount + amount
            actual_bet = player.bet(total_bet)

            old_bet = self.current_bet
            self.current_bet = player.current_bet
            self.min_raise = self.current_bet - old_bet
            self.last_raiser_index = self.current_player_index

            self.log_action(f"{player.name}가 {actual_bet} 레이즈했습니다 (현재 베팅: {self.current_bet})")

            if player.is_all_in:
                self.log_action(f"{player.name}가 올인했습니다!")

        elif action == Action.ALL_IN:
            actual_bet = player.bet(player.chips)

            if player.current_bet > self.current_bet:
                old_bet = self.current_bet
                self.current_bet = player.current_bet
                self.min_raise = self.current_bet - old_bet
                self.last_raiser_index = self.current_player_index

            self.log_action(f"{player.name}가 {actual_bet}으로 올인했습니다!")

    def collect_bets(self) -> None:
        """현재 베팅을 팟에 추가"""
        total_collected = 0
        for player in self.players:
            total_collected += player.current_bet
            player.current_bet = 0

        self.pot += total_collected
        self.current_bet = 0

    def calculate_side_pots(self) -> None:
        """
        사이드 팟 계산

        Week 6: 올인 상황에서 사이드 팟 처리
        """
        self.side_pots = []

        # 각 플레이어의 총 베팅액 계산
        player_bets = []
        for player in self.players:
            if not player.has_folded:
                total_bet = player.current_bet
                player_bets.append((player, total_bet))

        # 베팅액 기준으로 정렬
        player_bets.sort(key=lambda x: x[1])

        previous_level = 0
        eligible_players = [p for p, _ in player_bets]

        for i, (player, bet_level) in enumerate(player_bets):
            if bet_level > previous_level:
                pot_amount = (bet_level - previous_level) * len(eligible_players)

                if pot_amount > 0:
                    self.side_pots.append({
                        'amount': pot_amount,
                        'eligible_players': eligible_players.copy()
                    })

                previous_level = bet_level

            # 이 플레이어는 더 이상 높은 팟에 참여 불가
            eligible_players = eligible_players[i+1:]

        if self.debug_mode and self.side_pots:
            print(f"\n사이드 팟 계산 완료: {len(self.side_pots)}개의 팟")

    # ===== Week 7: 승자 결정 및 팟 분배 =====

    def determine_winner(self) -> List[Player]:
        """
        승자 결정

        Week 7: 핸드 평가 및 승자 판정 (임시 구현)
        Note: 실제 핸드 평가는 문현준의 HandEvaluator 사용
        """
        active_players = self.get_active_players()

        if len(active_players) == 1:
            return active_players

        # TODO: 실제 핸드 평가 로직 (문현준의 HandEvaluator 사용)
        # 임시로 첫 번째 플레이어를 승자로 반환
        print("\n[임시] 핸드 평가 로직 미구현 - 첫 번째 활성 플레이어를 승자로 지정")
        return [active_players[0]]

    def distribute_pot(self, winners: List[Player]) -> None:
        """
        팟 분배

        Week 7: 승자에게 팟 분배 (사이드 팟 포함)
        """
        if not winners:
            return

        # 사이드 팟이 있으면 각각 분배
        if self.side_pots:
            for side_pot in self.side_pots:
                eligible_winners = [w for w in winners if w in side_pot['eligible_players']]

                if eligible_winners:
                    share = side_pot['amount'] // len(eligible_winners)
                    remainder = side_pot['amount'] % len(eligible_winners)

                    for i, winner in enumerate(eligible_winners):
                        amount = share + (1 if i < remainder else 0)
                        winner.chips += amount
                        self.log_action(f"{winner.name}가 사이드 팟에서 {amount} 획득")
        else:
            # 메인 팟만 분배
            share = self.pot // len(winners)
            remainder = self.pot % len(winners)

            for i, winner in enumerate(winners):
                amount = share + (1 if i < remainder else 0)
                winner.chips += amount
                self.log_action(f"{winner.name}가 {amount} 획득")

        # 팟 초기화
        self.pot = 0
        self.side_pots = []

    def showdown(self) -> None:
        """
        쇼다운 진행

        Week 7: 최종 승자 결정 및 팟 분배
        """
        self.current_phase = GamePhase.SHOWDOWN
        self.log_action("\n========== 쇼다운 ==========")

        active_players = self.get_active_players()

        print("\n참가자 핸드:")
        for player in active_players:
            hand_str = ", ".join([str(card) for card in player.hand])
            print(f"  {player.name}: {hand_str}")

        community_str = ", ".join([str(card) for card in self.community_cards])
        print(f"커뮤니티 카드: {community_str}")

        # 승자 결정
        winners = self.determine_winner()

        print(f"\n승자: {', '.join([w.name for w in winners])}")

        # 팟 분배
        self.distribute_pot(winners)

        self.log_action("========== 핸드 종료 ==========\n")

    def advance_phase(self) -> None:
        """
        다음 게임 단계로 진행

        Week 3: FSM 상태 전이
        """
        if self.current_phase == GamePhase.PREFLOP:
            self.deal_flop()
            self.log_action(f"\n========== FLOP ==========")
            self.display_game_state()
            self.betting_round()

        elif self.current_phase == GamePhase.FLOP:
            self.deal_turn()
            self.log_action(f"\n========== TURN ==========")
            self.display_game_state()
            self.betting_round()

        elif self.current_phase == GamePhase.TURN:
            self.deal_river()
            self.log_action(f"\n========== RIVER ==========")
            self.display_game_state()
            self.betting_round()

        elif self.current_phase == GamePhase.RIVER:
            self.showdown()

    # ===== Week 7: 디버그 기능 =====

    def enable_debug_mode(self) -> None:
        """디버그 모드 활성화"""
        self.debug_mode = True
        print("디버그 모드가 활성화되었습니다.")

    def disable_debug_mode(self) -> None:
        """디버그 모드 비활성화"""
        self.debug_mode = False
        print("디버그 모드가 비활성화되었습니다.")

    def log_action(self, message: str) -> None:
        """
        액션 로깅

        Week 7: 게임 진행 상황 추적
        """
        self.action_history.append(message)
        if self.debug_mode or True:  # 항상 출력
            print(message)

    def print_action_history(self) -> None:
        """액션 히스토리 출력"""
        print("\n========== 액션 히스토리 ==========")
        for action in self.action_history:
            print(action)
        print("====================================\n")

    def get_game_statistics(self) -> Dict:
        """
        게임 통계 반환

        Week 7: 게임 상태 디버깅
        """
        return {
            'phase': self.current_phase.value,
            'pot': self.pot,
            'side_pots': len(self.side_pots),
            'active_players': len(self.get_active_players()),
            'community_cards': len(self.community_cards),
            'current_bet': self.current_bet,
            'actions_taken': len(self.action_history)
        }

    def play_full_hand(self) -> None:
        """
        한 핸드를 완전히 진행

        Week 7: 전체 게임 플로우 테스트
        """
        self.new_hand()

        # 블라인드 배팅
        self.post_blinds()
        self.display_game_state()

        # 프리플랍 베팅
        self.log_action("\n========== PREFLOP ==========")
        self.betting_round()

        # 게임 진행
        while self.current_phase != GamePhase.SHOWDOWN:
            # 한 명만 남으면 조기 종료
            if len(self.get_active_players()) <= 1:
                winner = self.get_active_players()[0]
                self.log_action(f"\n{winner.name}가 유일한 참가자로 팟 {self.pot} 획득!")
                winner.chips += self.pot
                self.pot = 0
                break

            self.advance_phase()

        # 최종 상태 표시
        print("\n========== 최종 결과 ==========")
        for player in self.players:
            print(f"{player.name}: {player.chips} chips")
        print("================================\n")