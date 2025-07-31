# create_tables.py
import asyncio
from app.models.db_models import Base
from app.config.database import engine

async def async_create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(async_create_tables())