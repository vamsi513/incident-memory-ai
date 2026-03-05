from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings


class DatabaseSingleton:
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def engine(cls) -> AsyncEngine:
        if cls._engine is None:
            cls._engine = create_async_engine(settings.postgres_dsn, echo=False, future=True)
        return cls._engine

    @classmethod
    def session_factory(cls) -> async_sessionmaker[AsyncSession]:
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(cls.engine(), expire_on_commit=False)
        return cls._session_factory

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncIterator[AsyncSession]:
        session = cls.session_factory()()
        try:
            yield session
        finally:
            await session.close()
