from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = getattr(settings, "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp")

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def create_db_and_tables():
    """Create database tables from SQLAlchemy models. Call this once during provisioning or in a migration step."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def get_session() -> AsyncSession:
    """Return an async session (use with `async with get_session() as session:`)

    Example:
        async with get_session() as session:
            result = await session.execute(text("select 1"))
    """
    async with AsyncSessionLocal() as session:
        yield session
