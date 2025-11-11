"""
미니맥스 알고리즘 - 박우현 담당
게임 트리 탐색 및 α-β 가지치기
"""
import copy
from typing import List, Tuple, Optional
from enum import Enum

from src.core.player import Player
from src.core.card import Card
from src.ai.base_ai import Action


class GameNode:
    """게임 트리 노드"""

    def __init__(
        self,
        players: List[Player],
        pot: int,
        current_bet: int,
        community_cards: List[Card],
        current_player_idx: int
    ):
        self.players = players
        self.pot = pot
        self.current_bet = current_bet
        self.community_cards = community_cards
        self.current_player_idx = current_player_idx
        self.children: List['GameNode'] = []
        self.value: Optional[float] = None


class MinimaxAI:
    """미니맥스 알고리즘 기반 AI"""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def minimax(
        self,
        node: GameNode,
        depth: int,
        is_maximizing: bool,
        alpha: float = float('-inf'),
        beta: float = float('inf')
    ) -> float:
        """
        미니맥스 알고리즘 with α-β 가지치기
        Returns: 노드의 평가값
        """
        # TODO: 미니맥스 알고리즘 구현 (박우현)
        # 1. 터미널 노드 또는 깊이 제한 확인
        # 2. 현재 플레이어의 가능한 액션 생성
        # 3. 각 액션에 대해 재귀적으로 평가
        # 4. α-β 가지치기 적용

        if depth == 0 or self._is_terminal_node(node):
            return self._evaluate_node(node)

        if is_maximizing:
            max_eval = float('-inf')
            for child in self._generate_children(node):
                eval_score = self.minimax(child, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # α-β 가지치기
            return max_eval
        else:
            min_eval = float('inf')
            for child in self._generate_children(node):
                eval_score = self.minimax(child, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # α-β 가지치기
            return min_eval

    def get_best_action(
        self,
        current_state: GameNode
    ) -> Tuple[Action, int]:
        """최적 액션 결정"""
        # TODO: 최적 액션 선택 로직 구현 (박우현)
        best_value = float('-inf')
        best_action = Action.FOLD
        best_amount = 0

        for child in self._generate_children(current_state):
            value = self.minimax(child, self.max_depth - 1, False)
            if value > best_value:
                best_value = value
                # child에서 액션 정보 추출 필요
                best_action = Action.CALL  # 임시
                best_amount = 0

        return best_action, best_amount

    def _is_terminal_node(self, node: GameNode) -> bool:
        """터미널 노드 여부 확인"""
        # TODO: 게임 종료 조건 확인 (박우현)
        
        active_players = [p for p in node.players if p.is_active and not p.has_folded]

        # 한 명만 남음 → 게임 종료
        if len(active_players) <= 1:
            return True

        # 모든 플레이어가 콜했을 때 + 커뮤니티 카드가 리버까지 공개됨
        if all(p.current_bet == node.current_bet for p in active_players) and len(node.community_cards) == 5:
            return True

        return False

    def _evaluate_node(self, node: GameNode) -> float:
        """노드 평가 함수"""
        # TODO: 게임 상태 평가 함수 구현 (박우현)
        # 팟 크기, 핸드 강도, 포지션 등을 고려한 평가
        ai_player = node.players[node.current_player_idx]
        hand_strength = ai_player.evaluate_hand(node.community_cards)  # 0~1
        stack_ratio = ai_player.stack / sum(p.stack for p in node.players)
        pot_factor = node.pot / 1000
        
        score = (hand_strength * 0.6) + (stack_ratio * 0.3) + (pot_factor * 0.1)
        return score

    def _generate_children(self, node: GameNode) -> List[GameNode]:
        """자식 노드 생성"""
        # TODO: 가능한 액션들로부터 자식 노드 생성 (박우현)
        # 현재 플레이어의 가능한 액션들(FOLD, CALL, RAISE)에 대해
        # 각각 새로운 GameNode 생성
        children = []
        current_player = node.players[node.current_player_idx]
        next_idx = (node.current_player_idx + 1) % len(node.players)

        possible_actions = []
        if current_player.stack == 0:
            possible_actions = [Action.CHECK]
        else:
            possible_actions = [Action.FOLD, Action.CALL]
            if current_player.stack > node.current_bet * 2:
                possible_actions.append(Action.RAISE)

        for action in possible_actions:
            new_node = copy.deepcopy(node)

            if action == Action.FOLD:
                new_node.players[new_node.current_player_idx].has_folded = True
            elif action == Action.CALL:
                call_amount = node.current_bet - current_player.current_bet
                new_node.pot += call_amount
                new_node.players[new_node.current_player_idx].stack -= call_amount
            elif action == Action.RAISE:
                raise_amount = node.current_bet * 2
                new_node.current_bet = raise_amount
                new_node.pot += raise_amount
                new_node.players[new_node.current_player_idx].stack -= raise_amount

            new_node.current_player_idx = next_idx
            children.append(new_node)

        return children
       
        