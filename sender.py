import asyncio
from typing import Callable, Iterable, List, Optional, Tuple

from telethon import TelegramClient
from telethon.errors import RPCError

from utils import append_log

DEFAULT_DELAY = 1.0
DEFAULT_SESSION = "mtproto_session"


async def _send_single(client: TelegramClient, recipient: str, message: str, delay: float) -> Tuple[str, str]:
    try:
        await client.send_message(recipient, message)
        status = "success"
        error_message = ""
    except RPCError as exc:
        status = "failed"
        error_message = str(exc)
    await asyncio.sleep(delay)
    return status, error_message


async def _send_batch(
    api_id: int,
    api_hash: str,
    phone_number: str,
    password: Optional[str],
    recipients: Iterable[str],
    message: str,
    delay: float,
    log_path: str,
    session_name: str,
    code_callback: Callable[[], str],
) -> List[Tuple[str, str, str]]:
    async with TelegramClient(session_name, api_id, api_hash) as client:
        await client.start(phone=phone_number, password=password, code_callback=code_callback)
        results: List[Tuple[str, str, str]] = []
        for recipient in recipients:
            status, error_message = await _send_single(client, recipient, message, delay)
            append_log(log_path, recipient, status, error_message)
            results.append((recipient, status, error_message))
        return results


def send_messages(
    api_id: int,
    api_hash: str,
    phone_number: str,
    password: Optional[str],
    recipients: Iterable[str],
    message: str,
    delay: float = DEFAULT_DELAY,
    log_path: str = "send_log.csv",
    session_name: str = DEFAULT_SESSION,
    code_callback: Optional[Callable[[], str]] = None,
) -> List[Tuple[str, str, str]]:
    if code_callback is None:
        raise ValueError("code_callback must be provided to enter Telegram login code.")
    return asyncio.run(
        _send_batch(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            password=password,
            recipients=recipients,
            message=message,
            delay=delay,
            log_path=log_path,
            session_name=session_name,
            code_callback=code_callback,
        )
    )
