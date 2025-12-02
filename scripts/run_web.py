import uvicorn
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    print("Starting Texas Hold'em Web Server...")
    print("Access the game at http://localhost:8000")
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
