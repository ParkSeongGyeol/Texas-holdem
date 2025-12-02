import queue
import time
import asyncio
from typing import Optional, Tuple, List, Dict

from src.core.game import PokerGame, Action, GamePhase
from src.core.player import Player
from src.algorithms.monte_carlo import MonteCarloSimulator

class WebPokerGame(PokerGame):
    """
    콘솔 입출력 대신 큐를 사용하는 웹 전용 PokerGame 클래스
    """
    def __init__(self, broadcast_callback, small_blind: int = 10, big_blind: int = 20):
        super().__init__(small_blind, big_blind)
        self.broadcast_callback = broadcast_callback  # 업데이트 전송을 위한 비동기 함수
        self.input_queues: Dict[str, queue.Queue] = {} # 플레이어 이름 -> 큐
        self.game_running = False
        self.monte_carlo = MonteCarloSimulator(num_simulations=1000)

    def add_player(self, name: str, chips: int = 1000) -> None:
        super().add_player(name, chips)
        self.input_queues[name] = queue.Queue()

    def log_action(self, message: str) -> None:
        """웹 클라이언트로 브로드캐스트하기 위해 log_action 오버라이드"""
        super().log_action(message)
        # 동기 메서드에서 비동기 콜백을 실행해야 함
        # log_action이 게임 스레드에서 호출된다고 가정
        self._broadcast_sync({"type": "action_log", "message": message})

    def display_game_state(self) -> None:
        """전체 상태를 브로드캐스트하기 위해 display_game_state 오버라이드"""
        # 모든 활성 플레이어의 승률 계산
        win_rates = {}
        active_players = self.get_active_players()
        
        # 게임 진행 중이고 쇼다운이 아닐 때만 계산
        if self.current_phase != GamePhase.SHOWDOWN and len(active_players) > 1:
            # 참고: 동기적으로 수행하면 느릴 수 있음.
            # 성능을 위해 병렬로 실행하거나 시뮬레이션 횟수를 줄일 수 있음.
            # 여기서는 MonteCarloSimulator의 parallel_simulation 메서드 사용
            
            community_cards = self.community_cards
            for player in active_players:
                # 상대방 수 추정 (활성 플레이어 - 자신)
                opponents_count = len(active_players) - 1
                if opponents_count > 0:
                    win_rate = self.monte_carlo.parallel_simulation(
                        player.hand, 
                        community_cards, 
                        num_opponents=opponents_count,
                        num_threads=4
                    )
                    win_rates[player.name] = round(win_rate * 100, 1)

        # 상태 객체 생성
        state = {
            "type": "update_state",
            "pot": self.pot,
            "community": [self._serialize_card(c) for c in self.community_cards],
            "phase": self.current_phase.value,
            "players": []
        }

        for player in self.players:
            p_data = {
                "name": player.name,
                "chips": player.chips,
                "current_bet": player.current_bet,
                "is_active": player.is_active,
                "has_folded": player.has_folded,
                "is_all_in": player.is_all_in,
                "hand": [self._serialize_card(c) for c in player.hand], # 항상 핸드 전송, 프론트엔드에서 가시성 결정
                "win_rate": win_rates.get(player.name, 0)
            }
            state["players"].append(p_data)

        self._broadcast_sync(state)

    def get_player_action(self, player: Player) -> Tuple[Action, int]:
        """웹 입력을 기다리기 위해 get_player_action 오버라이드"""
        
        # 1. 프론트엔드에 해당 플레이어의 턴임을 알림
        self._broadcast_sync({
            "type": "turn_change",
            "current_player": player.name,
            "available_actions": [a.value for a in self.get_available_actions(player)],
            "call_amount": self.current_bet - player.current_bet,
            "min_raise": self.min_raise
        })

        # 2. 큐에서 입력 대기
        # AI 플레이어라면 여기서 AI 로직 호출.
        # 현재는 add_player로 추가된 모든 플레이어가 사람이거나 큐를 통해 처리된다고 가정.
        # AI 통합 시 isinstance(player, AIPlayer) 확인
        
        # AI 확인 (현재는 덕 타이핑이나 이름 규칙 사용, 또는 AIPlayer 클래스 확인)
        # 순환 참조 방지를 위해 여기서 AIPlayer를 임포트하지 않았으므로,
        # 큐가 없으면 AI라고 가정하거나 app.py에서 명시적으로 AI 처리
        
        if player.name not in self.input_queues:
             # 폴백 또는 에러
             print(f"No input queue for {player.name}")
             return (Action.FOLD, 0)

        q = self.input_queues[player.name]
        try:
            # 액션 무한 대기
            action_data = q.get() 
            # action_data는 {"action": "FOLD", "amount": 0} 형태여야 함
            
            action_str = action_data.get("action")
            amount = int(action_data.get("amount", 0))
            
            if action_str == "FOLD":
                return (Action.FOLD, 0)
            elif action_str == "CHECK":
                return (Action.CHECK, 0)
            elif action_str == "CALL":
                # 콜 금액 계산
                call_amount = self.current_bet - player.current_bet
                return (Action.CALL, call_amount)
            elif action_str == "RAISE":
                return (Action.RAISE, amount)
            elif action_str == "ALL_IN":
                return (Action.ALL_IN, player.chips)
            else:
                # 기본 폴백
                return (Action.FOLD, 0)
                
        except Exception as e:
            print(f"Error getting action: {e}")
            return (Action.FOLD, 0)

    def _broadcast_sync(self, message: dict):
        """동기 컨텍스트에서 비동기 브로드캐스트를 실행하기 위한 헬퍼"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 현재 스레드에 루프가 없으면 메인 루프를 전달해야 할 수 있음
            # 보통 루프가 없는 스레드에서 실행됨.
            # 웹소켓 서버가 실행 중인 루프가 필요함.
            pass
            
        # 메인 스레드에서 전달된 루프 사용?
        # 사실 asyncio.run_coroutine_threadsafe가 방법임.
        # 메인 이벤트 루프 참조 필요.
        pass 
        # 현재는 콜백이 스레드 안전을 처리하는 래퍼라고 가정
        # 또는 __init__에 루프 전달
        
        if self.broadcast_callback:
            self.broadcast_callback(message)

    def _serialize_card(self, card):
        return {'rank': card.rank.symbol, 'suit': card.suit.name[0]}
