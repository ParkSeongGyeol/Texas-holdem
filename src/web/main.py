# main.py

#pip install fastapi 
#pip install "uvicorn[standard]"
#uvicorn src.web.main:app --reload


import random
import asyncio
from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
# from src.algorithms.hand_evaluator import HandEvaluator, HandRank
# from src.core.card import Card, Deck, Rank, Suit
#위 두 모듈들 import가 안되는 문제가 있어서 데모 버전으로 테스트.


# ------------------------------------------------------------------------------
# [TEST] 간이 카드 시스템 및 족보 평가기 (외부 모듈 대체)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# [TEST] 간이 카드 시스템 및 족보 평가기
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# [TEST] 간이 카드 시스템 및 족보 평가기
# ------------------------------------------------------------------------------

class Suit:
    def __init__(self, name, value):
        self.name = name   # "SPADES"
        self.value = value # "♠"

class Rank:
    def __init__(self, symbol):
        self.symbol = symbol # "A", "10", "K"

class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        suits = [
            Suit("SPADES", "♠"), Suit("HEARTS", "♥"), 
            Suit("DIAMONDS", "♦"), Suit("CLUBS", "♣")
        ]
        ranks = [Rank(r) for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]
        self.cards = [Card(s, r) for s in suits for r in ranks]
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop() if self.cards else None

class HandRank:
    def __init__(self, value, name):
        self.value = value
        self.name = name

class HandEvaluator:
    @staticmethod
    def evaluate_hand(cards: List[Card]):
        # 테스트용: 랜덤 족보 반환
        possible_ranks = [
            HandRank(1, "High Card"), HandRank(2, "One Pair"), 
            HandRank(3, "Two Pair"), HandRank(4, "Three of a Kind"),
            HandRank(5, "Straight"), HandRank(6, "Flush"), 
            HandRank(7, "Full House"), HandRank(8, "Four of a Kind")
        ]
        selected_rank = random.choice(possible_ranks)
        return (selected_rank, ) 

app = FastAPI()

# ------------------------------------------------------------------------------
# 1. PvP 게임 매니저 (수정됨: 종료 로직 및 승자 판별 추가)
# ------------------------------------------------------------------------------
class PvPGameManager:
    def __init__(self):
        # 덱 초기화용 데이터
        self.ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.suits = ['S','H','D','C']
        
        self.players: List[WebSocket] = []
        self.hands = {} # {ws: [{'rank':..., 'suit':...}, ...]}
        self.community_cards = []
        self.revealed_count = 0
        self.turn_index = 0
        self.action_count_in_round = 0
        self.game_over = False
        
        # 덱 (딕셔너리 리스트 형태 유지 - 기존 코드 호환)
        self.deck_list = []
        self.reset_deck()

    def reset_deck(self):
        self.deck_list = [{'rank': r, 'suit': s} for s in self.suits for r in self.ranks]
        random.shuffle(self.deck_list)

    def add_player(self, websocket):
        self.players.append(websocket)

    def is_full(self):
        return len(self.players) == 2

    def start_game(self):
        self.reset_deck()
        self.community_cards = []
        self.hands = {}
        
        # 카드 분배
        self.hands[self.players[0]] = [self.deck_list.pop(), self.deck_list.pop()]
        self.hands[self.players[1]] = [self.deck_list.pop(), self.deck_list.pop()]
        
        # 커뮤니티 카드 미리 뽑기
        for _ in range(5):
            self.community_cards.append(self.deck_list.pop())
            
        self.revealed_count = 0
        self.turn_index = 0
        self.action_count_in_round = 0
        self.game_over = False

    def next_turn(self):
        self.turn_index = (self.turn_index + 1) % 2
        self.action_count_in_round += 1
        
        # 두 플레이어가 모두 행동을 마쳤다면 다음 단계로
        if self.action_count_in_round >= 2:
            self.action_count_in_round = 0
            
            if self.revealed_count == 0: 
                self.revealed_count = 3 # Flop
            elif self.revealed_count < 5: 
                self.revealed_count += 1 # Turn, River
            else:
                # 이미 5장이 다 깔려있는데 라운드가 끝났다면 Showdown
                self.game_over = True

    def get_current_turn_socket(self):
        return self.players[self.turn_index]

    def determine_winner_index(self):
        """Mock HandEvaluator를 사용하여 승자 인덱스(0, 1) 또는 -1(무승부) 반환"""
        # 실제 Card 객체로 변환하여 평가해야 함 (Evaluator가 Card 객체를 받으므로)
        # 하지만 현재 PvPManager는 dict를 쓰고 있음.
        # 테스트용이므로 랜덤 승자를 반환하거나, Evaluator를 억지로 끼워맞춤.
        # 여기서는 테스트용 Evaluator가 어차피 랜덤을 반환하므로 로직만 구성함.
        
        # 임시 Card 객체 생성 헬퍼
        def dict_to_card(d):
            # value, name 등은 테스트에서 중요치 않음
            return Card(Suit("Temp", d['suit']), Rank(d['rank']))

        p1_cards = [dict_to_card(c) for c in self.hands[self.players[0]]]
        p2_cards = [dict_to_card(c) for c in self.hands[self.players[1]]]
        comm_cards = [dict_to_card(c) for c in self.community_cards]

        score0 = HandEvaluator.evaluate_hand(p1_cards + comm_cards)[0].value
        score1 = HandEvaluator.evaluate_hand(p2_cards + comm_cards)[0].value

        if score0 > score1: return 0
        elif score1 > score0: return 1
        else: return -1 # Draw

pvp_game = PvPGameManager()

# ------------------------------------------------------------------------------
# 2. AI 게임 세션 (기존 코드 유지)
# ------------------------------------------------------------------------------
class AIGameSession:
    def __init__(self, player_socket: WebSocket):
        self.player_socket = player_socket
        self.deck = Deck()
        self.player_hand: List[Card] = []
        self.ai_hand: List[Card] = []
        self.community_cards: List[Card] = []
        self.revealed_count = 0
        self.is_player_turn = True
        self.game_over = False

    def start(self):
        self.deck.reset()
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.ai_hand = [self.deck.deal(), self.deck.deal()]
        self.community_cards = [self.deck.deal() for _ in range(5)]
        self.revealed_count = 0
        self.is_player_turn = True
        self.game_over = False

    def serialize_card(self, card: Card):
        suit_char = card.suit.name[0]
        return {'rank': card.rank.symbol, 'suit': suit_char}

    async def send_state(self, show_ai=False):
        visible_comm = [self.serialize_card(c) for c in self.community_cards[:self.revealed_count]]
        p_hand = [self.serialize_card(c) for c in self.player_hand]
        
        ai_hand_data = []
        if show_ai:
            ai_hand_data = [self.serialize_card(c) for c in self.ai_hand]
        else:
            ai_hand_data = [{"hidden": True}, {"hidden": True}]
        
        await self.player_socket.send_json({
            "type": "update_state",
            "my_hand": p_hand,
            "opp_hand": ai_hand_data,
            "community": visible_comm,
            "win_rate": 50
        })
        
        if not self.game_over:
            await self.player_socket.send_json({
                "type": "turn_change",
                "is_my_turn": self.is_player_turn
            })

    async def process_turn(self, action: str):
        await self.player_socket.send_json({"type": "action_log", "message": f"나: {action}"})
        
        if action == "FOLD":
            await self.end_game(winner="AI")
            return

        self.is_player_turn = False
        await self.send_state() 

        await asyncio.sleep(1.0)
        ai_action = self.decide_ai_action()
        await self.player_socket.send_json({"type": "action_log", "message": f"AI: {ai_action}"})

        self.next_stage()

        if self.revealed_count > 5:
             await self.showdown()
        else:
            self.is_player_turn = True
            await self.send_state()

    def decide_ai_action(self):
        return "CALL" 

    def next_stage(self):
        if self.revealed_count == 0: self.revealed_count = 3
        elif self.revealed_count < 5: self.revealed_count += 1
        else: self.revealed_count = 6

    async def showdown(self):
        p_result = HandEvaluator.evaluate_hand(self.player_hand + self.community_cards)
        ai_result = HandEvaluator.evaluate_hand(self.ai_hand + self.community_cards)
        
        p_score = p_result[0].value
        ai_score = ai_result[0].value
        
        winner = "DRAW"
        if p_score > ai_score: winner = "PLAYER"
        elif ai_score > p_score: winner = "AI"
        
        await self.send_state(show_ai=True)
        await self.player_socket.send_json({"type": "action_log", "message": f"--- 결과: {winner} 승리! ---"})
        await self.finish_game_session(winner)

    async def end_game(self, winner):
        await self.finish_game_session(winner)

    async def finish_game_session(self, winner):
        self.game_over = True
        await self.player_socket.send_json({
            "type": "game_over", 
            "message": f"게임 종료. 승자: {winner}",
            "winner": winner
        })

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.get("/")
async def get():
    return FileResponse('test.html')

@app.websocket("/ws/holdem")
async def websocket_pvp(websocket: WebSocket):
    await websocket.accept()
    pvp_game.add_player(websocket)
    
    # 2명이 차면 게임 시작
    if pvp_game.is_full():
        pvp_game.start_game()
        for p in pvp_game.players:
            await send_pvp_state(p)
            await p.send_json({"type": "game_start"})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # --- [NEW] 재시작 로직 추가 ---
            if data['action'] == 'RESTART':
                # 누구든 재시작을 누르면 게임 리셋 (단순화)
                pvp_game.start_game()
                for p in pvp_game.players:
                    await send_pvp_state(p)
                    await p.send_json({"type": "game_start"})
                continue
            # ---------------------------

            # 턴 확인
            if websocket != pvp_game.get_current_turn_socket(): 
                continue
            
            # 행동 방송
            msg = f"{data['action']} {data.get('amount', '')}"
            for p in pvp_game.players:
                prefix = "나" if p == websocket else "상대"
                await p.send_json({"type": "action_log", "message": f"{prefix}: {msg}"})
            
            # FOLD 처리
            if data['action'] == 'FOLD':
                winner_idx = (pvp_game.turn_index + 1) % 2
                winner_socket = pvp_game.players[winner_idx]
                
                # 게임 종료 처리
                pvp_game.game_over = True
                
                for i, p in enumerate(pvp_game.players):
                    is_winner = (i == winner_idx)
                    winner_str = "PLAYER" if is_winner else "AI" # 클라이언트는 내가 이기면 PLAYER, 지면 AI(상대)로 인식
                    if i == winner_idx: winner_str = "PLAYER"
                    else: winner_str = "AI"
                    
                    await p.send_json({"type": "action_log", "message": "상대방이 폴드했습니다."})
                    await p.send_json({
                        "type": "game_over",
                        "winner": winner_str
                    })
                continue

            # 게임 진행
            pvp_game.next_turn()
            
            # --- [NEW] PvP 종료(Showdown) 체크 ---
            if pvp_game.game_over:
                # 승자 판별
                winner_idx = pvp_game.determine_winner_index()
                
                # 모든 플레이어에게 결과 전송 (카드 모두 공개)
                for i, p in enumerate(pvp_game.players):
                    # 승자 문자열 결정 (클라이언트 렌더링용)
                    if winner_idx == -1:
                        winner_str = "DRAW"
                    elif i == winner_idx:
                        winner_str = "PLAYER" # 내가 이김
                    else:
                        winner_str = "AI" # 상대가 이김 (클라이언트에서 AI=상대)

                    # 상태 업데이트 (카드 공개)
                    await send_pvp_state(p, show_hands=True)
                    
                    # 게임 오버 메시지
                    await p.send_json({
                        "type": "game_over",
                        "winner": winner_str
                    })
            else:
                # 게임 계속 진행
                for p in pvp_game.players:
                    await send_pvp_state(p)

    except WebSocketDisconnect:
        if websocket in pvp_game.players: pvp_game.players.remove(websocket)

@app.websocket("/ws/ai")
async def websocket_ai(websocket: WebSocket):
    await websocket.accept()
    session = AIGameSession(websocket)
    session.start()
    
    await websocket.send_json({"type": "game_start"})
    await session.send_state()

    try:
        while True:
            data = await websocket.receive_json()
            
            if data['action'] == 'RESTART':
                session.start()
                await websocket.send_json({"type": "game_start"}) 
                await session.send_state()
                continue

            if not session.is_player_turn or session.game_over:
                continue
                
            await session.process_turn(data['action'])
            
    except WebSocketDisconnect:
        pass

async def send_pvp_state(player_socket: WebSocket, show_hands=False):
    """
    PvP 상태 전송 헬퍼
    show_hands=True일 경우 상대방 카드도 보여줌 (Showdown)
    """
    visible_community = pvp_game.community_cards[:pvp_game.revealed_count]
    is_my_turn = (player_socket == pvp_game.get_current_turn_socket())
    
    # 상대방 소켓 찾기
    opp_socket = None
    for p in pvp_game.players:
        if p != player_socket:
            opp_socket = p
            break
            
    # 내 핸드
    my_hand_data = pvp_game.hands.get(player_socket, [])
    
    # 상대 핸드 처리
    opp_hand_data = []
    if opp_socket and pvp_game.hands.get(opp_socket):
        raw_opp_hand = pvp_game.hands[opp_socket]
        if show_hands:
            # 다 보여주기
            opp_hand_data = raw_opp_hand
        else:
            # 숨기기
            opp_hand_data = [{"hidden": True}, {"hidden": True}]

    await player_socket.send_json({
        "type": "update_state",
        "my_hand": my_hand_data,
        "opp_hand": opp_hand_data,
        "community": visible_community
    })
    
    # 게임이 끝났으면 턴 변경 메시지는 보내지 않음 (UI 혼동 방지)
    if not pvp_game.game_over:
        await player_socket.send_json({
            "type": "turn_change",
            "is_my_turn": is_my_turn
        })