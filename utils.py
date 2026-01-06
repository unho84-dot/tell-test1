import csv
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
import os

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_bot_token() -> str:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in the environment or .env file")
    return token


def load_recipients_from_csv(path: str) -> List[str]:
    recipients: List[str] = []
    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "chat_id" not in reader.fieldnames:
            raise ValueError("CSV must contain a 'chat_id' column")
        for row in reader:
            chat_id = row.get("chat_id", "").strip()
            if chat_id:
                recipients.append(chat_id)
    return recipients


def parse_chat_ids(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def ensure_recipient_limit(recipients: List[str], limit: int = 50) -> Tuple[bool, int]:
    return len(recipients) <= limit, len(recipients)


def append_log(log_path: str, chat_id: str, status: str, error_message: str = "") -> None:
    log_file = Path(log_path)
    new_file = not log_file.exists()
    with log_file.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if new_file:
            writer.writerow(["timestamp", "chat_id", "status", "error_message"])
        writer.writerow([
            datetime.now().strftime(TIMESTAMP_FORMAT),
            chat_id,
            status,
            error_message,
        ])
