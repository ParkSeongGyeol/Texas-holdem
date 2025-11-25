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
        current_bet: int, # 현재 라운드에서 맞춰야 할 최고 베팅액
        community_cards: List[Card],
        current_player_idx: int,
        action_taken: Optional[Action] = None, # 이 상태로 오기 위해 취한 행동
        bet_amount: int = 0 # 그 행동에 사용된 금액
    ):
        self.players = players
        self.pot = pot
        self.current_bet = current_bet
        self.community_cards = community_cards
        self.current_player_idx = current_player_idx
        self.action_taken = action_taken
        self.bet_amount = bet_amount
        
        self.children: List['GameNode'] = []
        self.value: Optional[float] = None

    def get_current_player(self) -> Player:
        return self.players[self.current_player_idx]


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
        is_maximizing 변수가 True면 내 차례니까 가장 높은 점수를 찾고, 
        False면 상대 차례니까 가장 낮은 점수(나에게 불리한 상황)를 찾습니다.
        """
        # 1. 터미널 노드 또는 깊이 제한 확인
        if depth == 0 or self._is_terminal_node(node):
            evaluated_score = self._evaluate_node(node, is_maximizing)
            node.value = evaluated_score
            return evaluated_score

        # 2. 자식 노드 생성 (가능한 액션 시뮬레이션)
        children = self._generate_children(node) #미래예측입니다.
        
        if not children: # 더 이상 진행할 수 없는 경우 (예: 모두 올인)
            return self._evaluate_node(node, is_maximizing)

        if is_maximizing:
            max_eval = float('-inf')
            for child in children:
                # 재귀 호출
                eval_score = self.minimax(child, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                # 4. α-β 가지치기
                if beta <= alpha:
                    break 
            
            node.value = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for child in children:
                # 재귀 호출
                eval_score = self.minimax(child, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                # 4. α-β 가지치기
                if beta <= alpha:
                    break 
            
            node.value = min_eval
            return min_eval

    def get_best_action(
        self,
        current_state: GameNode
    ) -> Tuple[Action, int]:
        """최적 액션 결정"""
        #가장 점수가 높은 행동을 선택합니다.
        # 루트 노드 확장
        children = self._generate_children(current_state)
        
        if not children:
            return Action.CHECK, 0

        best_value = float('-inf')
        best_child = None

        # 루트 레벨에서는 항상 Maximizing (AI 자신)
        for child in children:
            # 자식 노드 평가 (깊이는 max_depth - 1)
            # 여기서는 다음 턴이 상대방(Minimizing)이므로 False로 시작
            value = self.minimax(child, self.max_depth - 1, False)
            
            if value > best_value:
                best_value = value
                best_child = child
        
        # 최적의 자식 노드로 이동하기 위한 액션과 금액 반환
        if best_child:
            return best_child.action_taken, best_child.bet_amount
        else:
            return Action.FOLD, 0

    def _is_terminal_node(self, node: GameNode) -> bool:
        """터미널 노드(게임 종료 또는 라운드 종료) 여부 확인"""
        active_players = [p for p in node.players if p.is_active and not p.has_folded]

        # 1. 한 명만 남음 (나머지 폴드)
        if len(active_players) <= 1:
            return True
            
        # 2. 쇼다운 조건 (이 구현에서는 뎁스 제한이 있으므로, 실제 쇼다운까지 안 가더라도 평가함)
        # 만약 실제 게임 엔진과 연동한다면 라운드 종료 여부를 체크해야 함.
        # 여기서는 단순화를 위해 플레이어가 모두 올인 상태이거나 액션이 없을 때 터미널로 간주
        if all(p.is_all_in for p in active_players):
            return True

        return False

    def _evaluate_node(self, node: GameNode, is_maximizing: bool) -> float:
        """
        노드 평가 함수 (Heuristic Evaluation Function)
        
        기대값(EV) = (승리 확률 * 팟 크기) - (패배 확률 * 투자 비용)
        """
        # 현재 턴인 플레이어 (이 노드 상황에서의 플레이어)
        # 주의: is_maximizing이 True면 AI의 관점, False면 상대방의 관점
        # 하지만 평가값은 항상 AI 입장에서 높을수록 좋아야 함.
        
        # AI 플레이어 찾기 (이름이나 ID로 식별 필요, 여기서는 0번 인덱스가 AI라고 가정하거나 호출 시 주입)
        # 편의상 node.players[0]를 Hero(AI)라고 가정합니다.
        ai_player = node.players[0]
        
        if ai_player.has_folded:
            # 폴드했다면 이미 잃은 칩(투자금)은 매몰비용, 앞으로의 이득은 0
            # 하지만 상대에게 팟을 넘겨준 것이므로 약간의 페널티
            return -node.pot * 0.1 

        # 1. 핸드 강도 (0.0 ~ 1.0)
        # src.core.player에 get_hand_strength 메서드가 있다고 가정
        # 없다면 외부 Evaluator 사용 필요
        try:
            hand_strength = ai_player.get_hand_strength() 
        except AttributeError:
            # Mock 로직
            hand_strength = 0.5 

        # 2. 팟 오즈 계산 (Pot Odds)
        # 승리 시 얻을 금액 = 현재 팟
        # 패배 시 잃을 금액 = 이번 라운드 투자금 (이미 팟에 들어감)
        
        # 간단한 EV 계산: (승률 * 총 팟)
        # 여기에 Stack 상태 등을 반영
        
        ev = (hand_strength * node.pot)
        
        # 내 스택 비율이 높으면(위협적이면) 가산점
        total_chips = sum(p.chips + p.current_bet for p in node.players) # 전체 칩량
        stack_factor = ai_player.chips / total_chips if total_chips > 0 else 0
        
        final_score = ev + (stack_factor * 100)
        
        return final_score

    def _generate_children(self, node: GameNode) -> List[GameNode]:
        """
        현재 노드에서 가능한 모든 액션을 적용하여 자식 노드들을 생성
        """
        children = []
        current_player = node.get_current_player()
        
        # 이미 폴드했거나 올인이면 액션 불가 -> 턴만 넘김 (단, 여기선 단순화를 위해 게임 종료나 스킵 처리)
        if current_player.has_folded or current_player.is_all_in:
             # 실제로는 다음 플레이어 노드를 바로 리턴해야 하나, 
             # minimax 트리에서는 보통 active player 기준으로 depth를 짬.
             return []

        # 다음 플레이어 인덱스
        next_idx = (node.current_player_idx + 1) % len(node.players)

        # --- 1. FOLD ---
        fold_node = self._create_next_node(node, next_idx)
        # 상태 업데이트
        fold_node.players[node.current_player_idx].has_folded = True
        fold_node.action_taken = Action.FOLD
        children.append(fold_node)

        # --- 2. CHECK / CALL ---
        call_cost = node.current_bet - current_player.current_bet
        
        if call_cost == 0:
            # CHECK
            check_node = self._create_next_node(node, next_idx)
            check_node.action_taken = Action.CHECK
            children.append(check_node)
        else:
            # CALL (칩이 충분한지 확인)
            if current_player.chips > call_cost:
                call_node = self._create_next_node(node, next_idx)
                player_in_node = call_node.players[node.current_player_idx]
                
                player_in_node.chips -= call_cost
                player_in_node.current_bet += call_cost
                call_node.pot += call_cost
                
                call_node.action_taken = Action.CALL
                call_node.bet_amount = call_cost
                children.append(call_node)
            else:
                # 칩 부족 -> ALL-IN (Call All-in)
                allin_node = self._create_next_node(node, next_idx)
                player_in_node = allin_node.players[node.current_player_idx]
                
                allin_amt = player_in_node.chips
                player_in_node.chips = 0
                player_in_node.current_bet += allin_amt
                player_in_node.is_all_in = True
                allin_node.pot += allin_amt
                
                allin_node.action_taken = Action.ALL_IN
                allin_node.bet_amount = allin_amt
                children.append(allin_node)

        # --- 3. BET / RAISE ---
        # 칩이 남아있고, 레이즈할 여력이 될 때
        # 전략적 단순화: 2x 레이즈(Min Raise)와 올인만 고려 (Branching Factor 조절)
        if current_player.chips > call_cost:
            # A. Min Raise (현재 벳의 2배, 혹은 팟의 일정 비율)
            # 베팅이 없었다면(current_bet=0) 기본 베팅(예: 100), 있었다면 2배
            base_raise = node.current_bet * 2 if node.current_bet > 0 else 100
            needed_chips = base_raise - current_player.current_bet
            
            if current_player.chips >= needed_chips:
                raise_node = self._create_next_node(node, next_idx)
                player_in_node = raise_node.players[node.current_player_idx]
                
                player_in_node.chips -= needed_chips
                player_in_node.current_bet += needed_chips
                raise_node.pot += needed_chips
                raise_node.current_bet = player_in_node.current_bet # 최고 베팅액 갱신
                
                action_type = Action.RAISE if node.current_bet > 0 else Action.BET
                raise_node.action_taken = action_type
                raise_node.bet_amount = needed_chips
                children.append(raise_node)

            # B. ALL-IN (Aggressive)
            # 이미 Call에서 올인 처리를 했으므로, 여기서는 '칩이 call_cost보다 많을 때'의 레이즈성 올인
            allin_raise_node = self._create_next_node(node, next_idx)
            player_in_node = allin_raise_node.players[node.current_player_idx]
            
            allin_amt = player_in_node.chips
            player_in_node.chips = 0
            player_in_node.current_bet += allin_amt
            player_in_node.is_all_in = True
            allin_raise_node.pot += allin_amt
            
            # 최고 베팅액 갱신 가능성 확인
            if player_in_node.current_bet > allin_raise_node.current_bet:
                allin_raise_node.current_bet = player_in_node.current_bet
            
            allin_raise_node.action_taken = Action.ALL_IN
            allin_raise_node.bet_amount = allin_amt
            children.append(allin_raise_node)

        return children

    def _create_next_node(self, current_node: GameNode, next_idx: int) -> GameNode:
        """현재 노드를 깊은 복사하여 다음 상태의 기본 노드를 반환"""
        # copy.deepcopy는 느릴 수 있으므로, 실제 구현 시에는 
        # 필요한 정보만 복사하는 custom copy를 구현하는 것이 성능에 좋음
        # 여기서는 안전성을 위해 deepcopy 사용
        new_players = copy.deepcopy(current_node.players)
        
        return GameNode(
            players=new_players,
            pot=current_node.pot,
            current_bet=current_node.current_bet,
            community_cards=current_node.community_cards, # 카드는 불변 객체라 얕은 복사도 무방
            current_player_idx=next_idx
        )