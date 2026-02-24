from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings # Import the settings object

# The DATABASE_URL is now read from the settings object
engine = create_async_engine(settings.DATABASE_URL, echo=False) # Turned echo off for cleaner logs
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
