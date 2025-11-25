# main.py

import random
from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional


app = FastAPI()
# ------------------------------------------------------------------------------
class GameManager: #테스트용
    def __init__(self):
       
        ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        suits = ['S','H','D','C']
        self.deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
        random.shuffle(self.deck)
        
      
        self.players = [] 
        self.hands = {}   
        self.community_cards = [] 
        self.revealed_count = 0   
        self.turn_index = 0       
        self.action_count_in_round = 0 

    def add_player(self, websocket):
        self.players.append(websocket)
    
    def is_full(self):
        return len(self.players) == 2

    def start_game(self):
        
        self.hands[self.players[0]] = [self.deck.pop(), self.deck.pop()]
        self.hands[self.players[1]] = [self.deck.pop(), self.deck.pop()]
        
        
        for _ in range(5):
            self.community_cards.append(self.deck.pop())
            
        
        self.revealed_count = 3
        self.turn_index = 0 
        self.action_count_in_round = 0

    def next_turn(self):
        
        self.turn_index = (self.turn_index + 1) % 2
        self.action_count_in_round += 1
        
       #그냥 한번씩 왔다갔다 하면 한장 오픈
        if self.action_count_in_round >= 2:
            self.action_count_in_round = 0
            if self.revealed_count < 5:
                self.revealed_count += 1 

    def get_current_turn_socket(self):
        return self.players[self.turn_index]

game = GameManager()  #데모버전

@app.get("/")
async def get():
    return FileResponse('test.html')

@app.websocket("/ws/holdem")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
  
    if game.is_full(): #방 꽉참
        await websocket.close() #방 닫음
        return
        
    game.add_player(websocket)
    
    if game.is_full(): #여전히 방 꽉참
        game.start_game() #게임 시작
        
        for p in game.players:
            await send_game_state(p)
    else:
        # 대기 중 메시지
        pass 

    try:
        while True:
            data = await websocket.receive_json()
            
            # 턴 검증: 현재 턴인 사람만 행동 가능
            if websocket != game.get_current_turn_socket():
                await websocket.send_json({"type": "action_log", "message": "아직 당신 차례가 아닙니다!"})
                continue
            
            # 행동 처리 및 방송
            action_msg = f"{data['action']} {data.get('amount', '')}"
            for p in game.players:
                msg = "나" if p == websocket else "상대"
                await p.send_json({"type": "action_log", "message": f"{msg}: {action_msg}"})

            # 턴 넘기기 및 상태 업데이트
            game.next_turn()
            
            # 모든 플레이어에게 최신 화면(턴, 카드) 전송
            for p in game.players:
                await send_game_state(p)
            
    except WebSocketDisconnect:
        game.players.remove(websocket)
        # 게임 초기화 로직 필요 (생략)

async def send_game_state(player_socket: WebSocket):
    # 현재 공개해야 할 커뮤니티 카드만 자르기
    visible_community = game.community_cards[:game.revealed_count]
    
    is_my_turn = (player_socket == game.get_current_turn_socket())
    
    # 상태 전송
    await player_socket.send_json({
        "type": "update_state",
        "my_hand": game.hands[player_socket],
        "opp_hand": [{"hidden": True}, {"hidden": True}], # 상대 패는 항상 숨김
        "community": visible_community
    })
    
    # 턴 정보 전송
    await player_socket.send_json({
        "type": "turn_change",
        "is_my_turn": is_my_turn
    })

    # 게임 시작 플래그 (최초 1회만 의미 있음, UI 로딩 제거용)
    if game.revealed_count == 3 and game.action_count_in_round == 0:
         await player_socket.send_json({"type": "game_start"})

