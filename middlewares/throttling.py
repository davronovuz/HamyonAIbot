import time
from idlelib.window import add_windows_to_menu
from typing import Any,Awaitable,Callable,Dict
from aiogram import BaseMiddleware
from aiogram.types import Message



class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self,slow_mode_delay:int=3):
        self.last_from_user={} # 23232323:12:13
        self.delay=slow_mode_delay


    async def __call__(
            self,
            handler:Callable[[Message,Dict[str,Any]],Awaitable[Any]],
            event:Message,
            data:Dict[str,Any]


    )->Any:

        user_id=event.from_user.id
        now=time.time()

        if user_id in self.last_from_user:
            previous_time=self.last_from_user[user_id]
            time_passed=now-previous_time

            if time_passed<self.delay:
                if time_passed>0.5:
                    await event.answer("Too many requests...")

                return

        self.last_from_user[user_id]=now
        return await handler(event,data)







