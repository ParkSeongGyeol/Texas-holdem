# 배포 가이드 (Ubuntu 22.04)

이 문서는 Ubuntu 22.04 서버(Root 계정)에서 텍사스 홀덤 포커 게임을 배포하고 백그라운드 서비스로 실행하는 방법을 설명합니다.

## 전제 조건
- Ubuntu 22.04 서버
- Root 계정 접근 권한
- GitHub 저장소 접근 권한 (또는 프로젝트 파일)

## 1단계: 서버 접속 및 프로젝트 클론

서버에 SSH로 접속한 후, 홈 디렉토리(`/root`)로 이동하여 프로젝트를 다운로드합니다.

```bash
cd /root
git clone <YOUR_REPOSITORY_URL> poker_game
cd poker_game
```
*참고: `<YOUR_REPOSITORY_URL>`을 실제 깃허브 저장소 주소로 변경하세요. 만약 git을 사용하지 않고 파일을 직접 올린다면 `/root/poker_game` 폴더를 만들고 그 안에 파일들을 넣어주세요.*

## 2단계: 설치 스크립트 실행

`deployment` 폴더에 있는 `setup.sh` 스크립트를 실행하여 필요한 패키지와 라이브러리를 설치합니다.

```bash
chmod +x deployment/setup.sh
./deployment/setup.sh
```
이 스크립트는 다음 작업을 수행합니다:
- 시스템 패키지 업데이트
- Python 3, pip, venv, git 설치
- 가상 환경(`venv`) 생성
- `requirements.txt`에 명시된 파이썬 라이브러리 설치

## 3단계: 서비스 등록 및 실행

서버가 재부팅되어도 자동으로 실행되도록 Systemd 서비스를 등록합니다.

1. 서비스 파일을 시스템 디렉토리로 복사합니다.
```bash
cp deployment/poker_game.service /etc/systemd/system/
```

2. Systemd 설정을 다시 로드합니다.
```bash
systemctl daemon-reload
```

3. 서비스를 시작하고, 부팅 시 자동 실행되도록 설정합니다.
```bash
systemctl enable poker_game
systemctl start poker_game
```

## 4단계: 상태 확인 및 로그 모니터링

서비스가 정상적으로 실행 중인지 확인합니다.

```bash
systemctl status poker_game
```
`Active: active (running)`이라고 나오면 성공입니다.

실시간 로그를 확인하려면 다음 명령어를 사용하세요:
```bash
journalctl -u poker_game -f
```

## 5단계: 접속 테스트

웹 브라우저에서 `http://<YOUR_SERVER_IP>:8000`으로 접속하여 게임이 실행되는지 확인합니다.
(방화벽 설정이 필요한 경우 8000번 포트를 열어주어야 합니다: `ufw allow 8000`)
