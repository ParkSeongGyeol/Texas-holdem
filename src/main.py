import uvicorn
import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가 (src의 상위 디렉토리)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

def main():
    print("Starting Texas Hold'em Web Server...")
    print("Access the game at http://localhost:8000")
    print("Press Ctrl+C to stop the server.")
    
    # 웹 서버 실행 (0.0.0.0 바인딩으로 외부 접속 허용)
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()