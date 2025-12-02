from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # Check if it returns the HTML content (roughly)
    assert "<title>텍사스 홀덤 온라인</title>" in response.text

def test_websocket_lobby():
    with client.websocket_connect("/ws/lobby") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "player_count"
        assert "count" in data

def test_websocket_ai_session():
    with client.websocket_connect("/ws/ai") as websocket:
        # 1. Game Start
        data = websocket.receive_json()
        assert data["type"] == "game_start"
        
        # 2. Initial State
        data = websocket.receive_json()
        assert data["type"] == "update_state"
        assert "my_hand" in data
        assert "community" in data

        # 3. Turn Change
        # We might receive action_logs (blinds), update_states, and AI's turn before our turn.
        found_my_turn = False
        for _ in range(20):
            data = websocket.receive_json()
            if data["type"] == "turn_change" and data.get("is_my_turn"):
                found_my_turn = True
                break
        assert found_my_turn, "Did not receive turn_change for Human"

        # 4. Send Action
        websocket.send_json({"action": "CALL"})
        
        # 5. Receive Action Log (My action)
        # We might receive other messages (like turn_change for next player) first if things are fast,
        # or update_state. So we loop.
        found_action_log = False
        for _ in range(5):
            data = websocket.receive_json()
            if data["type"] == "action_log" and "나: CALL" in data["message"]:
                found_action_log = True
                break
        assert found_action_log, "Did not receive action_log for CALL"

def test_websocket_pvp_waiting():
    # Connect only 1 player -> Should wait
    with client.websocket_connect("/ws/holdem") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "waiting"
        assert "상대방을 기다리는 중" in data["message"]
