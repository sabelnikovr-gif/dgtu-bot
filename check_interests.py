# check_interests.py
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from models.database import db

async def main():
    await db.connect()
    
    interests = await db.get_user_interests(1057899073, min_score=1)
    
    print(f"🎯 Интересы пользователя 1057899073:\n")
    
    if interests:
        for row in interests:
            # 🔥 Правильная конвертация sqlite3.Row
            try:
                # Способ 1: Через keys() для sqlite3.Row
                if hasattr(row, 'keys'):
                    interest_type = row['interest_type']
                    interest_value = row['interest_value']
                    score = row['score']
                # Способ 2: Через индексы (если это кортеж)
                else:
                    interest_type = row[0]
                    interest_value = row[1]
                    score = row[2]
                
                print(f"  • Тип: {interest_type}")
                print(f"  • Значение: {interest_value}")
                print(f"  • Score: {score}")
                print()
                
            except Exception as e:
                print(f"  ⚠️ Ошибка: {e}")
                print(f"  • Row: {row}")
                print(f"  • Type: {type(row)}")
                print()
    else:
        print("  ⚠️ Нет интересов с min_score=1")
    
    await db.close()
    print("✅ Проверка завершена")

if __name__ == "__main__":
    asyncio.run(main())
