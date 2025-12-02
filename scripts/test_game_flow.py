import asyncio
import websockets
import json
import sys

async def test_game():
    uri = "ws://localhost:8000/ws/ai?difficulty=loose"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                print(f"Received: {data.get('type')}")
                
                if data['type'] == 'game_start':
                    print("Game Started!")
                    
                elif data['type'] == 'turn_change':
                    if data.get('is_my_turn'):
                        print("My Turn! Sending CALL...")
                        await websocket.send(json.dumps({"action": "CALL"}))
                    else:
                        print("Opponent's Turn")
                        
                elif data['type'] == 'game_over':
                    print(f"Game Over! Winner: {data.get('winner')}")
                    # Once game is over, we can exit or restart. 
                    # For this test, let's exit after one hand or if we want to test loop, wait a bit.
                    # But the user wants to check continuous play.
                    # Let's see if a new hand starts.
                    print("Waiting for next hand...")
                    
                elif data['type'] == 'action_log':
                    print(f"Log: {data.get('message')}")
                    if "다음 핸드" in data.get('message', ''):
                        print("Next hand detected! Test Successful.")
                        return

                elif data['type'] == 'update_state':
                    phase = data.get('phase')
                    print(f"Phase: {phase}, My Chips: {data.get('my_chips')}")
                    
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    try:
        asyncio.run(test_game())
    except KeyboardInterrupt:
        print("Test stopped")
