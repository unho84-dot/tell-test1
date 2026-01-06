import asyncio
from typing import Iterable, List, Tuple

from telegram import Bot
from telegram.error import RetryAfter, TelegramError

from utils import append_log

DEFAULT_DELAY = 1.0


async def _send_single(bot: Bot, chat_id: str, message: str, delay: float) -> Tuple[str, str]:
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        status = "success"
        error_message = ""
    except RetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            status = "success"
            error_message = ""
        except TelegramError as inner_exc:  # includes second RetryAfter or other errors
            status = "failed"
            error_message = str(inner_exc)
    except TelegramError as exc:
        status = "failed"
        error_message = str(exc)
    await asyncio.sleep(delay)
    return status, error_message


async def _send_batch(bot_token: str, recipients: Iterable[str], message: str, delay: float, log_path: str) -> List[Tuple[str, str, str]]:
    bot = Bot(token=bot_token)
    results: List[Tuple[str, str, str]] = []
    for chat_id in recipients:
        status, error_message = await _send_single(bot, chat_id, message, delay)
        append_log(log_path, chat_id, status, error_message)
        results.append((chat_id, status, error_message))
    return results


def send_messages(bot_token: str, recipients: Iterable[str], message: str, delay: float = DEFAULT_DELAY, log_path: str = "send_log.csv") -> List[Tuple[str, str, str]]:
    return asyncio.run(_send_batch(bot_token, recipients, message, delay, log_path))


def send_test_message(bot_token: str, chat_id: str, message: str, delay: float = DEFAULT_DELAY, log_path: str = "send_log.csv") -> Tuple[str, str, str]:
    results = send_messages(bot_token, [chat_id], message, delay, log_path)
    return results[0]
