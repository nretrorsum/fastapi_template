from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME


db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(db_url)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    try:
        async with async_session() as session:
            yield session
    except Exception as e:
        print(str(e))