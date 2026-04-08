import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, slow_mode_delay: int = 1):
        self.last_from_user = {}
        self.delay = slow_mode_delay

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()

        if user_id in self.last_from_user:
            if now - self.last_from_user[user_id] < self.delay:
                return

        self.last_from_user[user_id] = now
        return await handler(event, data)
