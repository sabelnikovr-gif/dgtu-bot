# check_programs.py
import json
from pathlib import Path

kb_path = Path("data/knowledge_base.json")

if kb_path.exists():
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    programs = kb.get("programs", {})
    
    print(f"📚 Всего направлений в базе: {len(programs)}\n")
    
    # Ищем прикладную математику
    found = False
    for code, info in programs.items():
        name = info.get('name', '').lower()
        if 'прикладная математика' in name or code == '01.03.04':
            print(f"✅ НАЙДЕНО: {code}")
            print(f"   Название: {info.get('name')}")
            print(f"   Профиль: {info.get('profile')}")
            print(f"   Проходной: {info.get('pass_score')}")
            print(f"   Бюджет: {info.get('budget_places')}")
            found = True
            break
    
    if not found:
        print("❌ Не найдено '01.03.04' или 'прикладная математика'")
        print("\n📋 Доступные направления:")
        for code, info in list(programs.items())[:5]:
            print(f"• {code}: {info.get('name')}")
else:
    print(f"❌ Файл не найден: {kb_path}")
