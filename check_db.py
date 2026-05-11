import asyncio
from models.database import db

async def check_tables():
    await db.connect()
    
    # Проверяем таблицы
    cursor = await db.db.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table'
    """)
    tables = await cursor.fetchall()
    
    print("📊 Таблицы в базе данных:")
    for table in tables:
        print(f"  • {table[0]}")
    
    await db.close()

asyncio.run(check_tables())
