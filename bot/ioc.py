from typing import AsyncGenerator, Self
from dishka import Provider, Scope, provide, make_async_container

from bot.common.uow import UoW
from bot.database.db import SessionFactory


class DepsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_uow(self: Self) -> AsyncGenerator[UoW, None]:
        async with SessionFactory() as session:
            yield UoW(session)

# 新增：全局容器工厂
_container = None

def get_container():
    global _container
    if _container is None:
        _container = make_async_container(DepsProvider())
    return _container