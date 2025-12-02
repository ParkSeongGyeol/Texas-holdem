import asyncio
import websockets
import json
import sys

async def player_client(name, uri):
    async with websockets.connect(uri) as websocket:
        print(f"[{name}] Connected to server")
        
        # Join Game
        # The server automatically adds player on connection to /ws/holdem
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'room_update':
                    print(f"[{name}] Room Update: {data['count']} players")
                    if data['can_start'] and name == "Player 1":
                        print(f"[{name}] Starting Game...")
                        await websocket.send(json.dumps({"action": "GAME_START"}))

                elif data['type'] == 'game_start':
                    print(f"[{name}] Game Started!")

                elif data['type'] == 'turn_change':
                    if data.get('is_my_turn'):
                        print(f"[{name}] My Turn! Sending CALL/CHECK...")
                        await websocket.send(json.dumps({"action": "CALL"}))
                    else:
                        print(f"[{name}] Opponent's Turn")

                elif data['type'] == 'game_over':
                    print(f"[{name}] Game Over! Winner: {data.get('winner')}")
                    break

                elif data['type'] == 'action_log':
                    if "다음 핸드" in data.get('message', ''):
                        print(f"[{name}] Next hand detected.")
                        # Let's run for 2 hands then stop
                        return

            except Exception as e:
                print(f"[{name}] Error: {e}")
                break

async def test_pvp():
    uri = "ws://localhost:8000/ws/holdem"
    # Start two players concurrently
    await asyncio.gather(
        player_client("Player 1", uri),
        player_client("Player 2", uri)
    )

if __name__ == "__main__":
    try:
        asyncio.run(test_pvp())
    except KeyboardInterrupt:
        print("Test stopped")
