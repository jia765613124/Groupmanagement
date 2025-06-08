from typing import AsyncGenerator, Self
from dishka import Provider, Scope, provide

from bot.common.uow import UoW
from bot.database.db import SessionFactory


class DepsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_uow(self: Self) -> AsyncGenerator[UoW, None]:
        async with SessionFactory() as session:
            yield UoW(session)