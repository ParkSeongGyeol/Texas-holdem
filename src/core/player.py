"""
플레이어 클래스 - 박성결 담당
플레이어 상태 관리 및 게임 진행 로직
"""

from typing import List
from src.core.card import Card


class Player:
    """
    포커 플레이어 클래스

    텍사스 홀덤 포커 게임의 플레이어를 나타내는 클래스.
    플레이어의 칩 스택, 핸드, 베팅 상태 등을 관리합니다.

    Attributes:
        name (str): 플레이어 이름
        chips (int): 현재 보유 칩 수
        hand (List[Card]): 플레이어의 홀 카드 (최대 2장)
        current_bet (int): 현재 베팅 라운드에서의 누적 베팅액
        is_active (bool): 게임 참여 가능 여부 (칩이 있고 폴드하지 않음)
        has_folded (bool): 현재 핸드에서 폴드 여부
        is_all_in (bool): 올인 상태 여부

    Example:
        >>> player = Player("Alice", 1000)
        >>> player.bet(100)
        100
        >>> player.chips
        900
    """

    def __init__(self, name: str, chips: int = 1000):
        """
        플레이어 초기화

        Args:
            name: 플레이어 이름
            chips: 초기 칩 수 (기본값: 1000)

        Raises:
            ValueError: chips가 음수이거나 name이 비어있을 때
        """
        if not name or not name.strip():
            raise ValueError("플레이어 이름은 비어있을 수 없습니다")
        if chips < 0:
            raise ValueError("초기 칩은 0 이상이어야 합니다")

        self.name = name.strip()
        self.chips = chips
        self.hand: List[Card] = []
        self.current_bet = 0
        self.is_active = chips > 0
        self.has_folded = False
        self.is_all_in = False

    def receive_card(self, card: Card) -> None:
        """
        카드를 받아 핸드에 추가

        Args:
            card: 받을 카드

        Raises:
            ValueError: 카드가 None이거나 이미 2장을 받은 경우
        """
        if card is None:
            raise ValueError("카드는 None일 수 없습니다")
        if len(self.hand) >= 2:
            raise ValueError("플레이어는 최대 2장의 홀 카드만 가질 수 있습니다")

        self.hand.append(card)

    def bet(self, amount: int) -> int:
        """
        베팅 수행

        플레이어가 베팅을 하고 실제로 베팅된 금액을 반환합니다.
        보유 칩보다 많은 금액을 베팅하려 하면 자동으로 올인 처리됩니다.

        Args:
            amount: 베팅하려는 금액

        Returns:
            실제로 베팅된 금액 (올인 시 보유 칩 전체)

        Raises:
            ValueError: amount가 음수이거나 0일 때
            RuntimeError: 이미 폴드했거나 칩이 없는 상태에서 베팅 시도
        """
        if amount < 0:
            raise ValueError("베팅 금액은 음수일 수 없습니다")
        if amount == 0:
            raise ValueError("베팅 금액은 0보다 커야 합니다 (체크는 별도 처리)")
        if self.has_folded:
            raise RuntimeError("폴드한 플레이어는 베팅할 수 없습니다")
        if self.chips == 0:
            raise RuntimeError("칩이 없는 플레이어는 베팅할 수 없습니다")

        if amount >= self.chips:
            # All-in: 보유한 모든 칩 베팅
            actual_bet = self.chips
            self.is_all_in = True
        else:
            actual_bet = amount

        self.chips -= actual_bet
        self.current_bet += actual_bet
        return actual_bet

    def fold(self) -> None:
        """
        폴드 (패 포기)

        현재 핸드를 포기하고 게임에서 제외됩니다.
        현재까지 베팅한 칩은 회수할 수 없습니다.

        Raises:
            RuntimeError: 이미 폴드한 상태에서 다시 폴드 시도
        """
        if self.has_folded:
            raise RuntimeError("이미 폴드한 플레이어입니다")

        self.has_folded = True
        self.is_active = False

    def reset_for_new_hand(self) -> None:
        """
        새 핸드를 위한 플레이어 상태 리셋

        핸드, 베팅 상태 등을 초기화하고 칩이 있으면 다시 활성화합니다.
        보유 칩 수는 유지됩니다.
        """
        self.hand = []
        self.current_bet = 0
        self.has_folded = False
        self.is_all_in = False
        self.is_active = self.chips > 0

    def can_bet(self, amount: int) -> bool:
        """
        지정된 금액을 베팅할 수 있는지 확인

        Args:
            amount: 확인할 베팅 금액

        Returns:
            베팅 가능 여부
        """
        if amount < 0:
            return False
        return self.chips >= amount and self.is_active and not self.has_folded

    def can_act(self) -> bool:
        """
        플레이어가 액션을 수행할 수 있는지 확인

        Returns:
            액션 가능 여부 (활성 상태이고, 폴드하지 않았으며, 올인 상태가 아님)
        """
        return self.is_active and not self.has_folded and not self.is_all_in

    def get_state(self) -> str:
        """
        현재 플레이어 상태를 문자열로 반환

        Returns:
            상태 문자열 ("ACTIVE", "FOLDED", "ALL_IN", "OUT_OF_CHIPS", "INACTIVE")
        """
        if not self.is_active:
            if self.chips == 0:
                return "OUT_OF_CHIPS"
            return "INACTIVE"
        if self.has_folded:
            return "FOLDED"
        if self.is_all_in:
            return "ALL_IN"
        return "ACTIVE"

    def __str__(self) -> str:
        """플레이어 정보 문자열 (사용자 친화적)"""
        hand_str = ", ".join([str(card) for card in self.hand]) if self.hand else "없음"
        state = self.get_state()
        return f"{self.name} [{state}] ({self.chips} chips): {hand_str}"

    def __repr__(self) -> str:
        """플레이어 객체 표현 (디버깅용)"""
        return f"Player(name={self.name}, chips={self.chips}, state={self.get_state()})"

    # Week 4: 추가 핸드 관리 기능

    def get_hand_strength(self) -> float:
        """
        핸드 강도 평가 (임시 구현)

        Returns:
            0.0 ~ 1.0 사이의 핸드 강도 (높을수록 강함)

        Note:
            실제 구현은 문현준의 HandEvaluator를 사용해야 함
        """
        # TODO: 실제 핸드 평가 로직 구현 (문현준의 HandEvaluator 사용)
        # 임시로 랜덤 값 반환
        import random
        return random.random()

    def get_hand_description(self) -> str:
        """
        현재 핸드의 설명 반환

        Returns:
            핸드의 문자열 설명
        """
        if not self.hand:
            return "핸드 없음"

        hand_str = ", ".join([str(card) for card in self.hand])
        return f"{hand_str}"

    def clear_hand(self) -> None:
        """핸드 초기화 (카드 제거)"""
        self.hand = []

    def has_full_hand(self) -> bool:
        """2장의 홀 카드를 모두 받았는지 확인"""
        return len(self.hand) == 2

    def get_total_investment(self) -> int:
        """
        현재 핸드에서의 총 투자 금액

        Returns:
            현재 베팅액 (누적)
        """
        return self.current_bet

    def win_pot(self, amount: int) -> None:
        """
        팟 획득

        Args:
            amount: 획득할 칩 수

        Raises:
            ValueError: amount가 음수일 때
        """
        if amount < 0:
            raise ValueError("획득 금액은 음수일 수 없습니다")

        self.chips += amount