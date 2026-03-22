from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from yasar_nuri_api.config.settings import Settings


def create_engine(settings: Settings):  # type: ignore[no-untyped-def]
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=False,
    )


def get_async_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(settings)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session
