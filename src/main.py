"""
Texas Hold'em Poker Game - Main Entry Point
2025년 2학기 알고리즘 프로젝트
팀원: 문현준, 박성결, 박종호, 박우현
"""

from src.core.game import PokerGame


def main():
    """메인 게임 실행 함수"""
    print("🎰 텍사스 홀덤 포커 게임")
    print("=" * 40)
    print("알고리즘을 활용한 AI 대전 시스템")
    print("=" * 40)

    # TODO: 게임 초기화 및 실행 로직 구현
    game = PokerGame()
    game.start()


if __name__ == "__main__":
    main()