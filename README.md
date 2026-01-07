# Telegram Sender (Windows)

간단한 Tkinter GUI로 여러 수신자에게 텍스트 메시지를 보내는 Windows용 Telegram Bot 도구입니다. `python-telegram-bot` 최신 버전(21.x)과 `.env`에 저장된 BOT_TOKEN을 사용합니다.

## 폴더 구조 제안
```
project_root/
├─ app.py            # Tkinter GUI 엔트리 포인트
├─ sender.py         # 메시지 발송 로직(재시도, 지연)
├─ scheduler.py      # 예약 발송 시간 처리
├─ utils.py          # CSV/토큰/로그 유틸
├─ requirements.txt  # 의존성 목록
├─ send_log.csv      # 발송 결과 로그(실행 후 생성)
└─ .env              # BOT_TOKEN=...
```

## 사전 준비
1. Python 3.11+ 설치 (Windows 기준).
2. [BotFather](https://t.me/BotFather)로 발급받은 BOT_TOKEN을 준비합니다.
3. 레포지토리 클론 후 프로젝트 루트에서 `.env` 파일을 생성하고 토큰을 적습니다:
   ```
   BOT_TOKEN=123456:ABC-Your-Telegram-Bot-Token
   ```
4. (선택) 테스트용 수신자 목록 예시를 만듭니다:
   ```csv
   # recipients.csv 예시
   chat_id,name
   123456789,홍길동
   987654321,테스트
   ```
5. 가상환경 생성 및 의존성 설치:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 실행 방법 (Windows, PowerShell 기준)
1. 프로젝트 루트에서 가상환경을 활성화합니다:
   ```powershell
   .venv\Scripts\activate
   ```
2. GUI를 실행합니다:
   ```powershell
   python app.py
   ```
3. 실행 후 순서
   - `Load recipients.csv` 버튼으로 CSV를 불러오거나, "Or paste chat_ids" 박스에 줄바꿈으로 chat_id를 붙여넣습니다.
   - 메시지를 입력합니다.
   - **즉시 발송**: `즉시 발송` 버튼 클릭.
   - **예약 발송**: `YYYY-MM-DD HH:MM` 형식(Asia/Seoul)을 입력하고 `예약 발송` 클릭.
   - **테스트 발송**: 상단 입력란에 개인 chat_id를 적고 `테스트 발송` 클릭.

> Tip: 예약 입력 예시 — `2024-12-31 22:30` (Asia/Seoul). 발송 로그는 실행 폴더의 `send_log.csv`에 누적됩니다.

## 주요 기능
- recipients.csv 불러오기(`chat_id` 컬럼 필수, `name` 컬럼은 선택)
- 텍스트 박스에 chat_id 직접 입력(줄바꿈 구분)
- 메시지 멀티라인 입력
- 발송 모드: 즉시 발송 / 예약 발송(Asia/Seoul, `YYYY-MM-DD HH:MM`)
- 버튼: 테스트 발송(개인 chat_id), 즉시 발송, 예약 발송
- 수신자 최대 50명 제한
- 발송 간 기본 지연(sleep) 및 Telegram `RetryAfter` 예외 재시도 처리
- 발송 결과를 `send_log.csv`에 기록(timestamp, chat_id, status, error_message)

## PyInstaller로 단일 실행 파일 만들기
의존성을 설치한 후 아래 명령을 실행하면 `dist/telegram_sender.exe`가 생성됩니다.
```
pyinstaller --onefile --name telegram_sender app.py
```
(첫 실행 시 `pyinstaller`가 없으면 `pip install pyinstaller`로 설치)

## 사용 팁
- 예약 발송 입력 예시: `2024-12-31 22:30`
- 발송 전에 반드시 테스트 발송으로 토큰/채팅 ID를 확인하세요.
- `send_log.csv`는 실행 시 자동 생성되며, 동일 이름의 파일이 있으면 뒤에 이어 기록합니다.
