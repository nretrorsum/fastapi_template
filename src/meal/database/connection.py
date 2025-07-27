from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config import POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_DB

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db"

engine = create_async_engine(db_url)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    try:
        async with async_session() as session:
            yield session
    except Exception as e:
        print(str(e))