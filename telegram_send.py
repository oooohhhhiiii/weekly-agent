"""Telegram 봇으로 메시지 전송"""

import sys
import requests
from pathlib import Path


ENV_PATH = Path(__file__).parent / ".env"


def load_env():
    """환경 변수 로드"""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env


def send_document(file_path, caption=None):
    """Telegram 파일 첨부 전송 (sendDocument API)"""
    env = load_env()
    bot_token = env.get('TELEGRAM_BOT_TOKEN')
    chat_id = env.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 없습니다.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    with open(file_path, 'rb') as f:
        files = {'document': (Path(file_path).name, f, 'text/html')}
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print(f"Document 전송 성공: {file_path}")
        return True
    else:
        print(f"Document 전송 실패: {response.status_code} {response.text}")
        return False


def send_message(text, parse_mode="Markdown"):
    """Telegram 메시지 전송"""
    env = load_env()
    bot_token = env.get('TELEGRAM_BOT_TOKEN')
    chat_id = env.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 없습니다.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    })

    if response.status_code == 200:
        print("Telegram 전송 성공")
        return True
    else:
        # Markdown 파싱 실패 시 plain text로 재시도
        if parse_mode == "Markdown":
            print("Markdown 파싱 실패, plain text로 재시도...")
            return send_message(text, parse_mode=None)
        print(f"Telegram 전송 실패: {response.status_code} {response.text}")
        return False


def send_long_message(text, max_length=4000):
    """긴 메시지를 분할하여 전송 (Telegram 제한: 4096자)"""
    if len(text) <= max_length:
        return send_message(text)

    # 줄바꿈 기준으로 분할
    lines = text.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk += '\n' + line if current_chunk else line

    if current_chunk:
        chunks.append(current_chunk.strip())

    success = True
    for i, chunk in enumerate(chunks, 1):
        print(f"  메시지 {i}/{len(chunks)} 전송 중...")
        if not send_message(chunk):
            success = False
    return success


def main():
    if len(sys.argv) < 3:
        print("Usage: python telegram_send.py --message '텍스트'")
        print("       python telegram_send.py --file message.txt")
        print("       python telegram_send.py --document file.html '캡션'")
        sys.exit(1)

    if sys.argv[1] == '--message':
        text = sys.argv[2]
        send_long_message(text)
    elif sys.argv[1] == '--file':
        file_path = Path(sys.argv[2])
        text = file_path.read_text(encoding='utf-8')
        send_long_message(text)
    elif sys.argv[1] == '--document':
        file_path = Path(sys.argv[2])
        caption = sys.argv[3] if len(sys.argv) > 3 else None
        send_document(file_path, caption)
    else:
        print("--message, --file, 또는 --document 옵션을 사용하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
