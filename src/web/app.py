# app.py

# pip install fastapi 
# pip install "uvicorn[standard]"
# uvicorn src.web.app:app --reload

import asyncio
import threading
import time
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

# 실제 게임 로직 임포트
from src.core.card import Card, Deck, Rank, Suit
from src.algorithms.hand_evaluator import HandEvaluator, HandRank
from src.web.game_adapter import WebPokerGame
from src.ai.rule_based_ai import RuleBasedAI, AdaptiveRuleBasedAI
from src.ai.base_ai import Position

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TexasHoldemWeb")

app = FastAPI()

# ------------------------------------------------------------------------------
# 로비 / 연결 관리자
# ------------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Lobby connection accepted. Total: {len(self.active_connections)}")
        await self.broadcast_player_count()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Lobby connection closed. Total: {len(self.active_connections)}")

    async def broadcast_player_count(self):
        count = len(self.active_connections)
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "player_count", "count": count})
            except:
                pass

lobby_manager = ConnectionManager()

# ------------------------------------------------------------------------------
# 1. PvP 게임 매니저 (WebPokerGame 사용)
# ------------------------------------------------------------------------------
class PvPGameManager:
    def __init__(self):
        self.players: List[WebSocket] = []
        self.game_instance: Optional[WebPokerGame] = None
        self.game_thread: Optional[threading.Thread] = None
        self.loop = asyncio.get_event_loop()
        self.is_game_active = False

    async def add_player(self, websocket: WebSocket) -> bool:
        """플레이어 추가 시도. 게임 중이거나 꽉 찼으면 False 반환"""
        if self.is_game_active:
            await websocket.send_json({"type": "error", "message": "Game already in progress"})
            return False
            
        if len(self.players) >= 4:
            await websocket.send_json({"type": "error", "message": "Room is full (Max 4)"})
            return False

        self.players.append(websocket)
        logger.info(f"PvP Player joined. Total: {len(self.players)}")
        await self.broadcast_player_list()
        return True

    async def remove_player(self, websocket: WebSocket):
        if websocket in self.players:
            player_name = getattr(websocket, 'player_name', None)
            self.players.remove(websocket)
            logger.info(f"PvP Player left: {player_name}. Total: {len(self.players)}")
            await self.broadcast_player_list()
            
            # 게임 중이면 FOLD 액션을 주입하여 게임 진행이 막히지 않게 함
            if self.is_game_active and self.game_instance and player_name:
                if player_name in self.game_instance.input_queues:
                    logger.info(f"Injecting FOLD for {player_name}")
                    self.game_instance.input_queues[player_name].put({"action": "FOLD"})

    async def broadcast_player_list(self):
        """현재 대기 중인 플레이어 수 브로드캐스트"""
        count = len(self.players)
        msg = {
            "type": "room_update", 
            "count": count, 
            "can_start": count >= 2
        }
        for p in self.players:
            try:
                await p.send_json(msg)
            except:
                pass

    def start_game(self):
        if self.game_thread and self.game_thread.is_alive():
            logger.warning("Game start requested but already running.")
            return

        if len(self.players) < 2:
            logger.warning("Not enough players to start.")
            return

        logger.info(f"Starting PvP Game with {len(self.players)} players.")
        self.is_game_active = True
        self.game_instance = WebPokerGame(self.broadcast_callback)
        
        for i, ws in enumerate(self.players):
            name = f"Player {i+1}"
            self.game_instance.add_player(name, chips=1000)
            ws.player_name = name

        # 게임 시작 알림
        asyncio.run_coroutine_threadsafe(self._notify_game_start(), self.loop)

        self.game_thread = threading.Thread(target=self._run_game)
        self.game_thread.start()

    async def _notify_game_start(self):
        for p in self.players:
            try:
                await p.send_json({"type": "game_start"})
            except:
                pass

    def _run_game(self):
        """블로킹 게임 루프 실행"""
        try:
            while self.game_instance and len(self.game_instance.players) >= 2:
                # 딜러 포지션 이동 (매 핸드마다)
                if hasattr(self.game_instance, 'dealer_position'):
                    self.game_instance.dealer_position = (self.game_instance.dealer_position + 1) % len(self.game_instance.players)

                self.game_instance.play_full_hand()
                
                # 1. 연결 끊긴 플레이어 처리
                current_socket_names = [getattr(ws, 'player_name', '') for ws in self.players]
                remaining_players = []
                disconnected_players = []
                
                for p in self.game_instance.players:
                    if p.name in current_socket_names:
                        remaining_players.append(p)
                    else:
                        disconnected_players.append(p)
                
                if disconnected_players:
                    for dp in disconnected_players:
                         asyncio.run_coroutine_threadsafe(
                            self._broadcast_async({"type": "action_log", "message": f"{dp.name}님이 나갔습니다."}),
                            self.loop
                        )
                    self.game_instance.players = remaining_players
                    
                    if len(remaining_players) < 2:
                         # 기권승 처리
                         winner = remaining_players[0]
                         asyncio.run_coroutine_threadsafe(
                            self._broadcast_winner(winner.name, "상대방이 기권하여 승리했습니다!"),
                            self.loop
                        )
                         break

                # 2. 파산한 플레이어 처리
                active_players_list = []
                bankrupt_players = []
                
                for p in self.game_instance.players:
                    if p.chips <= 0:
                        bankrupt_players.append(p)
                    else:
                        active_players_list.append(p)
                
                # 파산 플레이어 알림 및 제거
                for bp in bankrupt_players:
                    target_ws = next((ws for ws in self.players if getattr(ws, 'player_name', '') == bp.name), None)
                    if target_ws:
                        asyncio.run_coroutine_threadsafe(
                            target_ws.send_json({"type": "game_over", "winner": "Others", "message": "파산했습니다! 게임에서 제외됩니다."}), 
                            self.loop
                        )
                
                self.game_instance.players = active_players_list
                
                # 남은 플레이어가 1명이면 승자 결정 (파산으로 인한 승리)
                if len(active_players_list) < 2:
                    winner = active_players_list[0]
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_winner(winner.name, f"최종 승자: {winner.name}! 축하합니다!"),
                        self.loop
                    )
                    break
                
                # 잠시 대기 후 다음 핸드
                time.sleep(5) 
                asyncio.run_coroutine_threadsafe(self._broadcast_next_hand(), self.loop)

        except Exception as e:
            logger.error(f"Game loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_game_active = False
            logger.info("Game loop finished.")

    async def _broadcast_winner(self, winner_name, message):
        for p in self.players:
            try:
                await p.send_json({
                    "type": "game_over", 
                    "winner": winner_name, 
                    "message": message
                })
            except:
                pass

    async def _broadcast_next_hand(self):
        for p in self.players:
            try:
                await p.send_json({"type": "action_log", "message": "잠시 후 다음 핸드가 시작됩니다..."})
            except:
                pass

    def broadcast_callback(self, message: dict):
        """게임 스레드에서 메시지를 브로드캐스트하기 위한 콜백"""
        asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self.loop)

    async def _broadcast_async(self, message: dict):
        for p in self.players:
            try:
                # 프론트엔드 호환성을 위한 상태 변환
                if message.get("type") == "update_state":
                    my_name = getattr(p, "player_name", "")
                    
                    # 내 데이터
                    my_data = next((pl for pl in message["players"] if pl["name"] == my_name), None)
                    
                    # 상대방 데이터 리스트 (나 제외)
                    opponents = []
                    for pl in message["players"]:
                        if pl["name"] != my_name:
                            # 쇼다운이 아니면 패 숨기기
                            opp_hand = pl["hand"]
                            if message["phase"] != "showdown":
                                opp_hand = [{"hidden": True}, {"hidden": True}]
                            
                            opponents.append({
                                "name": pl["name"],
                                "chips": pl["chips"],
                                "current_bet": pl["current_bet"],
                                "is_active": pl["is_active"],
                                "hand": opp_hand
                            })

                    frontend_msg = {
                        "type": "update_state",
                        "community": message["community"],
                        "pot": message["pot"],
                        "phase": message["phase"],
                        "my_hand": my_data["hand"] if my_data else [],
                        "opponents": opponents, # 리스트로 변경
                        "win_rate": my_data.get("win_rate", 0) if my_data else 0,
                        "my_chips": my_data["chips"] if my_data else 0,
                        "my_bet": my_data["current_bet"] if my_data else 0
                    }
                    
                    await p.send_json(frontend_msg)

                elif message.get("type") == "turn_change":
                    # is_my_turn 플래그 추가
                    msg = message.copy()
                    msg["is_my_turn"] = (message["current_player"] == getattr(p, "player_name", ""))
                    await p.send_json(msg)
                
                elif message.get("type") == "action_log":
                    # 로그 메시지는 그대로 전송
                    await p.send_json(message)
                
                else:
                    await p.send_json(message)

            except Exception as e:
                logger.error(f"Broadcast error to {getattr(p, 'player_name', 'Unknown')}: {e}")

    def handle_input(self, websocket: WebSocket, action_data: dict):
        """웹소켓 입력을 처리하고 큐에 넣음"""
        action_type = action_data.get("action")
        
        if action_type == "GAME_START":
            logger.info(f"Game start requested by {getattr(websocket, 'player_name', 'Unknown')}")
            self.start_game()
            return

        if not self.game_instance:
            return
            
        player_name = getattr(websocket, 'player_name', None)
        if player_name and player_name in self.game_instance.input_queues:
            self.game_instance.input_queues[player_name].put(action_data)

pvp_game = PvPGameManager()

# ------------------------------------------------------------------------------
# 2. AI 게임 세션 (WebPokerGame 사용)
# ------------------------------------------------------------------------------
class AIGameSession:
    def __init__(self, player_socket: WebSocket, difficulty: str = "loose"):
        self.player_socket = player_socket
        self.game_instance: Optional[WebPokerGame] = None
        self.game_thread: Optional[threading.Thread] = None
        self.loop = asyncio.get_event_loop()
        self.ai_player_instance = None
        self.difficulty = difficulty
        self.stop_requested = False

    def start(self):
        if self.game_thread and self.game_thread.is_alive():
            return

        logger.info(f"Starting AI Game Session (Difficulty: {self.difficulty})")
        self.game_instance = WebPokerGame(self.broadcast_callback)
        self.stop_requested = False
        
        # 사람 플레이어 추가
        human_name = "Human"
        self.player_socket.player_name = human_name
        self.game_instance.add_player(human_name, chips=1000)
        
        # AI 플레이어 추가
        if self.difficulty == "adaptive":
            ai_player = AdaptiveRuleBasedAI("AI_Bot", Position.BB)
        else:
            ai_player = RuleBasedAI("AI_Bot", Position.BB, strategy_type=self.difficulty)
            
        ai_player.chips = 1000
        self.game_instance.add_player(ai_player.name, chips=1000)
        self.ai_player_instance = ai_player
        
        self.game_thread = threading.Thread(target=self._run_game)
        self.game_thread.start()

    def _run_game(self):
        try:
            while not self.stop_requested:
                if self.game_instance:
                    # 딜러 포지션 이동
                    self.game_instance.dealer_position = (self.game_instance.dealer_position + 1) % len(self.game_instance.players)
                    
                    self.game_instance.play_full_hand()
                    
                    # 칩 확인
                    human = next(p for p in self.game_instance.players if p.name == "Human")
                    ai = next(p for p in self.game_instance.players if p.name == "AI_Bot")
                    
                    if human.chips <= 0:
                        asyncio.run_coroutine_threadsafe(
                            self.player_socket.send_json({"type": "game_over", "winner": "AI_Bot", "message": "패배했습니다! 칩이 모두 소진되었습니다."}),
                            self.loop
                        )
                        break
                    elif ai.chips <= 0:
                        asyncio.run_coroutine_threadsafe(
                            self.player_socket.send_json({"type": "game_over", "winner": "Human", "message": "승리했습니다! AI를 파산시켰습니다!"}),
                            self.loop
                        )
                        break
                    
                    if self.stop_requested:
                        winner_names = "None"
                        if self.game_instance and self.game_instance.last_winners:
                            winner_names = ", ".join([p.name for p in self.game_instance.last_winners])
                        
                        msg = f"게임이 종료되었습니다. 마지막 승자: {winner_names}"
                        
                        asyncio.run_coroutine_threadsafe(
                            self.player_socket.send_json({"type": "game_over", "winner": winner_names, "message": msg}),
                            self.loop
                        )
                        break

                    # 다음 핸드 준비 알림
                    time.sleep(3)
                    asyncio.run_coroutine_threadsafe(
                        self.player_socket.send_json({"type": "action_log", "message": "잠시 후 다음 핸드가 시작됩니다..."}),
                        self.loop
                    )

        except Exception as e:
            logger.error(f"AI Game loop error: {e}")

    def broadcast_callback(self, message: dict):
        asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self.loop)

    async def _broadcast_async(self, message: dict):
        try:
            # 프론트엔드 호환성을 위한 상태 변환
            if message.get("type") == "update_state":
                # 사람은 항상 "Human"
                my_data = next((pl for pl in message["players"] if pl["name"] == "Human"), None)
                
                # AI 데이터
                opponents = []
                for pl in message["players"]:
                    if pl["name"] != "Human":
                        opp_hand = pl["hand"]
                        if message["phase"] != "showdown":
                            opp_hand = [{"hidden": True}, {"hidden": True}]
                        
                        opponents.append({
                            "name": pl["name"],
                            "chips": pl["chips"],
                            "current_bet": pl["current_bet"],
                            "is_active": pl["is_active"],
                            "hand": opp_hand
                        })
                
                frontend_msg = {
                    "type": "update_state",
                    "community": message["community"],
                    "pot": message["pot"],
                    "phase": message["phase"],
                    "my_hand": my_data["hand"] if my_data else [],
                    "opponents": opponents,
                    "win_rate": my_data.get("win_rate", 0) if my_data else 0,
                    "my_chips": my_data["chips"] if my_data else 0,
                    "my_bet": my_data["current_bet"] if my_data else 0
                }

                await self.player_socket.send_json(frontend_msg)
            elif message.get("type") == "turn_change":
                msg = message.copy()
                msg["is_my_turn"] = (message["current_player"] == "Human")
                await self.player_socket.send_json(msg)
            else:
                await self.player_socket.send_json(message)
            
            # AI의 턴인지 확인
            if message.get("type") == "turn_change" and message.get("current_player") == self.ai_player_instance.name:
                await asyncio.get_event_loop().run_in_executor(None, self._process_ai_turn)
                
        except Exception as e:
            logger.error(f"AI Broadcast error: {e}")

    def _process_ai_turn(self):
        """AI의 움직임을 계산하고 큐에 넣음"""
        game = self.game_instance
        ai = self.ai_player_instance
        
        # AI 핸드 업데이트
        real_ai_player = next(p for p in game.players if p.name == ai.name)
        ai.hole_cards = real_ai_player.hand
        
        # 상대방 목록
        opponents = [p for p in game.players if p.name != ai.name]
        
        action, amount = ai.act(
            game.community_cards,
            game.pot,
            game.current_bet,
            opponents
        )
        
        action_str = action.value.upper()
        
        if ai.name in game.input_queues:
            time.sleep(1.0) # 생각하는 시간 시뮬레이션
            game.input_queues[ai.name].put({"action": action_str, "amount": amount})

    def handle_input(self, action_data: dict):
        if action_data.get("action") == "EXIT":
            self.stop_requested = True
            return

        if not self.game_instance:
            return
        player_name = getattr(self.player_socket, 'player_name', None)
        if player_name and player_name in self.game_instance.input_queues:
            self.game_instance.input_queues[player_name].put(action_data)

# ------------------------------------------------------------------------------
# API 엔드포인트
# ------------------------------------------------------------------------------

@app.get("/")
async def get():
    return FileResponse('src/web/index.html')

@app.websocket("/ws/lobby")
async def websocket_lobby(websocket: WebSocket):
    await lobby_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # 연결 유지
    except WebSocketDisconnect:
        lobby_manager.disconnect(websocket)
        await lobby_manager.broadcast_player_count()

@app.websocket("/ws/holdem")
async def websocket_pvp(websocket: WebSocket):
    await websocket.accept()
    
    success = await pvp_game.add_player(websocket)
    if not success:
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('action') == 'RESTART':
                # 재시작 로직은 좀 더 복잡할 수 있음 (모두 동의?)
                # 현재는 간단히 구현하거나 비활성화
                pass

            pvp_game.handle_input(websocket, data)

    except WebSocketDisconnect:
        await pvp_game.remove_player(websocket)

@app.websocket("/ws/ai")
async def websocket_ai(websocket: WebSocket, difficulty: str = "loose"):
    await websocket.accept()
    session = AIGameSession(websocket, difficulty=difficulty)
    session.start()
    
    await websocket.send_json({"type": "game_start"})

    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('action') == 'RESTART':
                session.start()
                await websocket.send_json({"type": "game_start"}) 
                continue
                
            session.handle_input(data)
            
    except WebSocketDisconnect:
        pass