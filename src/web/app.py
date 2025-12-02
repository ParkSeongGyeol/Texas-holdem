# app.py

# pip install fastapi 
# pip install "uvicorn[standard]"
# uvicorn src.web.app:app --reload

import asyncio
import threading
import time
from typing import List, Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

# Import real game logic
from src.core.card import Card, Deck, Rank, Suit
from src.algorithms.hand_evaluator import HandEvaluator, HandRank
from src.web.game_adapter import WebPokerGame
from src.ai.rule_based_ai import RuleBasedAI
from src.ai.base_ai import Position

app = FastAPI()

# ------------------------------------------------------------------------------
# Lobby / Connection Manager
# ------------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.broadcast_player_count()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_player_count(self):
        count = len(self.active_connections)
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "player_count", "count": count})
            except:
                pass

lobby_manager = ConnectionManager()

# ------------------------------------------------------------------------------
# 1. PvP Game Manager (Using WebPokerGame)
# ------------------------------------------------------------------------------
class PvPGameManager:
    def __init__(self):
        self.players: List[WebSocket] = []
        self.game_instance: Optional[WebPokerGame] = None
        self.game_thread: Optional[threading.Thread] = None
        self.loop = asyncio.get_event_loop()

    def add_player(self, websocket):
        self.players.append(websocket)

    def is_full(self):
        return len(self.players) == 2

    def start_game(self):
        if self.game_thread and self.game_thread.is_alive():
            return # Already running

        self.game_instance = WebPokerGame(self.broadcast_callback)
        
        for i, ws in enumerate(self.players):
            name = f"Player {i+1}"
            self.game_instance.add_player(name, chips=1000)
            ws.player_name = name

        self.game_thread = threading.Thread(target=self._run_game)
        self.game_thread.start()

    def _run_game(self):
        """Run the blocking game loop"""
        if self.game_instance:
            self.game_instance.play_full_hand()

    def broadcast_callback(self, message: dict):
        """Callback from game thread to broadcast message"""
        asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self.loop)

    async def _broadcast_async(self, message: dict):
        for p in self.players:
            try:
                # Transform state for frontend compatibility
                if message.get("type") == "update_state":
                    # Find my player data
                    my_data = next((pl for pl in message["players"] if pl["name"] == getattr(p, "player_name", "")), None)
                    # Find opponent data (first one that is not me)
                    opp_data = next((pl for pl in message["players"] if pl["name"] != getattr(p, "player_name", "")), None)
                    
                    frontend_msg = {
                        "type": "update_state",
                        "community": message["community"],
                        "pot": message["pot"],
                        "phase": message["phase"],
                        "my_hand": my_data["hand"] if my_data else [],
                        "opp_hand": opp_data["hand"] if opp_data else [{"hidden": True}, {"hidden": True}],
                        "win_rate": my_data.get("win_rate", 0) if my_data else 0
                    }
                    
                    # Hide opponent hand if not showdown
                    if message["phase"] != "showdown" and opp_data:
                         frontend_msg["opp_hand"] = [{"hidden": True}, {"hidden": True}]
                    elif message["phase"] == "showdown" and opp_data:
                         frontend_msg["opp_hand"] = opp_data["hand"]

                    await p.send_json(frontend_msg)
                elif message.get("type") == "turn_change":
                    # Add is_my_turn flag
                    msg = message.copy()
                    msg["is_my_turn"] = (message["current_player"] == getattr(p, "player_name", ""))
                    await p.send_json(msg)
                else:
                    await p.send_json(message)
            except Exception as e:
                print(f"Broadcast error: {e}")

    def handle_input(self, websocket: WebSocket, action_data: dict):
        """Handle input from websocket and put into queue"""
        if not self.game_instance:
            return
            
        player_name = getattr(websocket, 'player_name', None)
        if player_name and player_name in self.game_instance.input_queues:
            self.game_instance.input_queues[player_name].put(action_data)

pvp_game = PvPGameManager()

# ------------------------------------------------------------------------------
# 2. AI Game Session (Using WebPokerGame)
# ------------------------------------------------------------------------------
class AIGameSession:
    def __init__(self, player_socket: WebSocket):
        self.player_socket = player_socket
        self.game_instance: Optional[WebPokerGame] = None
        self.game_thread: Optional[threading.Thread] = None
        self.loop = asyncio.get_event_loop()
        self.ai_player_instance = None

    def start(self):
        if self.game_thread and self.game_thread.is_alive():
            return

        self.game_instance = WebPokerGame(self.broadcast_callback)
        
        # Add Human Player
        human_name = "Human"
        self.player_socket.player_name = human_name
        self.game_instance.add_player(human_name, chips=1000)
        
        # Add AI Player
        ai_player = RuleBasedAI("AI_Bot", Position.BB, strategy_type="loose")
        ai_player.chips = 1000
        self.game_instance.add_player(ai_player.name, chips=1000)
        self.ai_player_instance = ai_player
        
        self.game_thread = threading.Thread(target=self._run_game)
        self.game_thread.start()

    def _run_game(self):
        if self.game_instance:
            self.game_instance.play_full_hand()

    def broadcast_callback(self, message: dict):
        asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self.loop)

    async def _broadcast_async(self, message: dict):
        try:
            # Transform state for frontend compatibility
            if message.get("type") == "update_state":
                # Human is always "Human"
                my_data = next((pl for pl in message["players"] if pl["name"] == "Human"), None)
                opp_data = next((pl for pl in message["players"] if pl["name"] != "Human"), None)
                
                frontend_msg = {
                    "type": "update_state",
                    "community": message["community"],
                    "pot": message["pot"],
                    "phase": message["phase"],
                    "my_hand": my_data["hand"] if my_data else [],
                    "opp_hand": opp_data["hand"] if opp_data else [{"hidden": True}, {"hidden": True}],
                    "win_rate": my_data.get("win_rate", 0) if my_data else 0
                }
                
                if message["phase"] != "showdown" and opp_data:
                        frontend_msg["opp_hand"] = [{"hidden": True}, {"hidden": True}]
                elif message["phase"] == "showdown" and opp_data:
                        frontend_msg["opp_hand"] = opp_data["hand"]

                await self.player_socket.send_json(frontend_msg)
            elif message.get("type") == "turn_change":
                msg = message.copy()
                msg["is_my_turn"] = (message["current_player"] == "Human")
                await self.player_socket.send_json(msg)
            else:
                await self.player_socket.send_json(message)
            
            # Check if it's AI's turn
            if message.get("type") == "turn_change" and message.get("current_player") == self.ai_player_instance.name:
                await asyncio.get_event_loop().run_in_executor(None, self._process_ai_turn)
                
        except Exception as e:
            print(f"Broadcast error: {e}")

    def _process_ai_turn(self):
        """Calculate AI move and put into queue"""
        game = self.game_instance
        ai = self.ai_player_instance
        
        # Update AI's hand
        real_ai_player = next(p for p in game.players if p.name == ai.name)
        ai.hole_cards = real_ai_player.hand
        
        # Opponents
        opponents = [p for p in game.players if p.name != ai.name]
        
        action, amount = ai.act(
            game.community_cards,
            game.pot,
            game.current_bet,
            opponents
        )
        
        action_str = action.value.upper()
        
        if ai.name in game.input_queues:
            time.sleep(1.0) # Simulate thinking
            game.input_queues[ai.name].put({"action": action_str, "amount": amount})

    def handle_input(self, action_data: dict):
        if not self.game_instance:
            return
        player_name = getattr(self.player_socket, 'player_name', None)
        if player_name and player_name in self.game_instance.input_queues:
            self.game_instance.input_queues[player_name].put(action_data)

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.get("/")
async def get():
    return FileResponse('src/web/index.html')

@app.websocket("/ws/lobby")
async def websocket_lobby(websocket: WebSocket):
    await lobby_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        lobby_manager.disconnect(websocket)
        await lobby_manager.broadcast_player_count()

@app.websocket("/ws/holdem")
async def websocket_pvp(websocket: WebSocket):
    await websocket.accept()
    pvp_game.add_player(websocket)
    
    # 2 players -> Start
    if pvp_game.is_full():
        pvp_game.start_game()
        for p in pvp_game.players:
            await p.send_json({"type": "game_start"})
    else:
        await websocket.send_json({"type": "waiting", "message": "상대방을 기다리는 중..."})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('action') == 'RESTART':
                pvp_game.start_game()
                continue

            pvp_game.handle_input(websocket, data)

    except WebSocketDisconnect:
        if websocket in pvp_game.players: pvp_game.players.remove(websocket)

@app.websocket("/ws/ai")
async def websocket_ai(websocket: WebSocket):
    await websocket.accept()
    session = AIGameSession(websocket)
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