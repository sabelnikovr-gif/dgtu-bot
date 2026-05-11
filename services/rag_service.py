"""
📚 RAG Service for DGTU Bot
============================
Сервис для поиска релевантного контекста в базе знаний.
Использует кэширование, ключевые слова и умный поиск.

Автор: @sabelnikovr
Дата: 2026
"""

from services.cache_service import cache
import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RAGService:
    """📚 RAG-сервис для поиска контекста в базе знаний ДГТУ"""
    
    # 🔥 КОНФИГУРАЦИЯ ПОИСКА
    SEARCH_CONFIG = {
        "max_context_parts": 5,           # Макс. частей контекста для обычных запросов
        "max_context_length": 2000,       # Макс. длина контекста для ИИ
        "cache_ttl": 300,                 # TTL кэша в секундах (5 минут)
        "min_keyword_matches": 1,         # Мин. совпадений для категории
    }
    
    # 🔥 КАТЕГОРИИ ПОИСКА (для точного определения намерения)
    SEARCH_CATEGORIES = {
        "passing_scores": {
            "keywords": ["балл", "проходной", "проходные", "егэ", "поступление", "минимум"],
            "faq_keys": ["scores", "passing", "ege"],
            "priority": 10,
        },
        "dormitory": {
            "keywords": ["общежит", "общага", "жильё", "студгородок", "нагибина", "поселение"],
            "faq_keys": ["dormitory", "housing"],
            "priority": 9,
        },
        "scholarships": {
            "keywords": ["стипенд", "выплата", "гас", "пгас", "социальная", "академическая", 
                        "отличник", "хорошист", "5 500", "4 500", "3 500", "15 500", "6 000"],
            "faq_keys": ["scholarships", "stipend"],
            "priority": 10,
        },
        "documents": {
            "keywords": ["документ", "паспорт", "аттестат", "снилс", "фото", "подач", "приём"],
            "faq_keys": ["documents", "application"],
            "priority": 8,
        },
        "deadlines": {
            "keywords": ["срок", "дата", "дедлайн", "20 июня", "1 августа", "календарь", "когда"],
            "faq_keys": ["deadlines", "dates"],
            "priority": 8,
        },
        "cost": {
            "keywords": ["стоимость", "цена", "платно", "контракт", "153300", "135000", "руб"],
            "faq_keys": ["cost", "payment"],
            "priority": 7,
        },
        "vuts": {
            "keywords": ["вуц", "военн", "армия", "офицер", "сержант", "билет", "отсрочк"],
            "faq_keys": ["vuts", "military"],
            "priority": 6,
        },
        "contacts": {
            "keywords": ["контакт", "телефон", "адрес", "почта", "связь", "гагарина", "273-86"],
            "faq_keys": ["contacts", "admission"],
            "priority": 5,
        },
    }
    
    # 🔥 КЛЮЧЕВЫЕ СЛОВА ДЛЯ НАПРАВЛЕНИЙ
    PROGRAM_KEYWORDS = {
        "01.03.04": ["прикладная математика", "математика", "01.03"],
        "02.03.03": ["мат. обеспечение", "большие данные", "машинное обучение", "02.03"],
        "09.03.01": ["информатика и вт", "информатика", "вычислительная техника", "09.03.01"],
        "09.03.02_ist": ["ист", "информационные системы", "09.03.02 ист"],
        "09.03.02_ai": ["искусственный интеллект", "ии", "ai", "09.03.02 ии"],
        "09.03.02_web": ["web", "веб", "разработка", "09.03.02 веб"],
        "09.03.02_zaoch": ["заочное", "ист заочное", "09.03.02 заоч"],
        "09.03.03": ["прикладная информатика", "информатика прикладная", "09.03.03"],
        "09.03.03_zaoch": ["прикладная информатика заочное", "09.03.03 заоч"],
        "09.03.04": ["программная инженерия", "программирование", "09.03.04"],
        "10.03.01": ["информационная безопасность", "инф. безопасность", "10.03"],
        "10.05.01": ["компьютерная безопасность", "комп. безопасность", "специалитет безопасность"],
        "10.05.02": ["инф. безопасность специалитет", "безопасность спец"],
    }
    
    def __init__(self, kb_path: Optional[str] = None):
        """Инициализация RAG-сервиса"""
        self.knowledge_base: dict = {}
        self.kb_path = Path(kb_path) if kb_path else None
        self.load_knowledge_base()
        logger.info(f"📚 RAG-сервис инициализирован: {len(self.knowledge_base)} разделов")
    
    # ============================================================================
    # 🔹 ЗАГРУЗКА БАЗЫ ЗНАНИЙ
    # ============================================================================
    
    def load_knowledge_base(self, path: Optional[str] = None) -> bool:
        """
        Загружает базу знаний из JSON-файла.
        
        Args:
            path: Путь к файлу (если None, используется путь по умолчанию)
            
        Returns:
            bool: True если загрузка успешна, иначе False
        """
        try:
            kb_path = Path(path) if path else self._get_default_kb_path()
            
            if not kb_path.exists():
                logger.warning(f"⚠️ База знаний не найдена: {kb_path}")
                return False
            
            with open(kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            
            logger.info(f"✅ База знаний загружена: {kb_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка JSON в базе знаний: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки базы знаний: {e}")
            return False
    
    def _get_default_kb_path(self) -> Path:
        """Возвращает путь к базе знаний по умолчанию"""
        base_path = Path(__file__).parent.parent
        return base_path / 'data' / 'knowledge_base.json'
    
    def reload_knowledge_base(self) -> bool:
        """Перезагружает базу знаний (для обновления без перезапуска бота)"""
        return self.load_knowledge_base()
    
    # ============================================================================
    # 🔹 ПОИСК ПО НАПРАВЛЕНИЯМ
    # ============================================================================
    
    def _search_by_code(self, code: str) -> str:
        """
        Поиск информации по коду направления.
        
        Args:
            code: Код направления (например, "09.03.02")
            
        Returns:
            str: Отформатированная информация или пустая строка
        """
        programs = self.knowledge_base.get("programs", {})
        
        # Прямое совпадение
        if code in programs:
            return self._format_program_info(code, programs[code])
        
        # Частичное совпадение (регистронезависимое)
        for prog_code, prog_info in programs.items():
            if code.lower() in prog_code.lower():
                return self._format_program_info(prog_code, prog_info)
        
        return ""
    
    def _search_by_name(self, name_query: str) -> str:
        """
        Поиск по названию направления.
        
        Args:
            name_query: Запрос пользователя
            
        Returns:
            str: Отформатированная информация или пустая строка
        """
        programs = self.knowledge_base.get("programs", {})
        query_lower = name_query.lower().strip()
        results = []
        
        for code, prog in programs.items():
            prog_name = prog.get('name', '').lower()
            prog_profile = prog.get('profile', '').lower()
            
            # Полное совпадение
            if query_lower in prog_name or query_lower in prog_profile:
                results.append(self._format_program_info(code, prog))
                continue
            
            # Совпадение по ключевым словам
            query_words = set(query_lower.split())
            prog_words = set(f"{prog_name} {prog_profile}".split())
            
            if len(query_words & prog_words) >= 2:  # минимум 2 совпадающих слова
                results.append(self._format_program_info(code, prog))
        
        return "\n\n".join(results) if results else ""
    
    def _search_by_keywords(self, query: str) -> list[str]:
        """
        Поиск направлений по ключевым словам из PROGRAM_KEYWORDS.
        
        Returns:
            list[str]: Список отформатированных карточек направлений
        """
        query_lower = query.lower()
        results = []
        
        for code, keywords in self.PROGRAM_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                programs = self.knowledge_base.get("programs", {})
                if code in programs:
                    results.append(self._format_program_info(code, programs[code]))
        
        return results
    
    def _format_program_info(self, code: str, info: dict) -> str:
        """
        Форматирует информацию о направлении в читаемый вид.
        
        Args:
            code: Код направления
            info: Данные о направлении из базы знаний
            
        Returns:
            str: Отформатированный текст с эмодзи
        """
        lines = [f"📚 <b>{info.get('name', 'Направление')}</b> ({code})"]
        
        if info.get('profile'):
            lines.append(f"🎯 <b>Профиль:</b> {info['profile']}")
        
        lines.append(f"🎓 <b>Уровень:</b> {info.get('level', '—')}")
        lines.append(f"📅 <b>Форма:</b> {info.get('form', '—')}")
        lines.append(f"💰 <b>Бюджетных мест:</b> {info.get('budget_places', '—')}")
        lines.append(f"💵 <b>Стоимость:</b> {info.get('cost', '—')}")
        lines.append(f"📈 <b>Проходной балл:</b> {info.get('pass_score', '—')}")
        lines.append("")
        
        # Предметы ЕГЭ
        lines.append(f"📚 <b>Предметы ЕГЭ:</b>")
        if info.get('required_subjects'):
            lines.append(f"• {info['required_subjects']}")
        if info.get('optional_subjects'):
            lines.append(f"• {info['optional_subjects']}")
        
        lines.append("")
        lines.append(f"📖 <b>Описание:</b>")
        lines.append(info.get('description', '—'))
        
        if info.get('partners'):
            lines.append("")
            lines.append(f"🤝 <b>Партнёры:</b>")
            lines.append(info['partners'])
        
        return "\n".join(lines)
    
    def _get_all_programs_summary(self) -> str:
        """
        Возвращает краткую сводку по ВСЕМ направлениям.
        Используется для запросов типа "все направления", "куда поступать".
        """
        programs = self.knowledge_base.get("programs", {})
        if not programs:
            return ""
        
        cards = []
        for code, prog in programs.items():
            card = (
                f"📚 <b>{prog.get('name', 'Направление')}</b> ({code})\n"
                f"🎓 {prog.get('level', '—')} | 📅 {prog.get('form', '—')}\n"
                f"💰 {prog.get('cost', '—')} | 📈 Проходной: {prog.get('pass_score', '—')}\n"
                f"🎯 {prog.get('profile', prog.get('description', '—')[:80])}..."
            )
            cards.append(card)
        
        return "\n\n".join(cards)
    
    # ============================================================================
    # 🔹 ПОИСК ПО FAQ И ИСТОЧНИКАМ
    # ============================================================================
    
    def _search_faq(self, query: str, category: Optional[str] = None) -> list[str]:
        """
        Поиск по базе часто задаваемых вопросов.
        
        Args:
            query: Запрос пользователя
            category: Опциональная категория для фильтрации
            
        Returns:
            list[str]: Список подходящих ответов
        """
        faq = self.knowledge_base.get("faq", {})
        query_lower = query.lower()
        results = []
        
        for key, item in faq.items():
            # Если указана категория — фильтруем по ней
            if category and category not in key:
                continue
            
            question = item.get('question', '').lower()
            answer = item.get('answer', '').lower()
            
            # Прямое совпадение по ключу или вопросу
            if key.lower() in query_lower or query_lower in question:
                results.append(f"<b>❓ {item.get('question', key)}</b>\n{item.get('answer', '')}")
                continue
            
            # Совпадение по ключевым словам в ответе
            query_words = set(query_lower.split())
            answer_words = set(answer.split())
            
            if len(query_words & answer_words) >= 2:
                results.append(f"<b>❓ {item.get('question', key)}</b>\n{item.get('answer', '')}")
        
        return results
    
    def _search_official_sources(self, query: str) -> list[str]:
        """Поиск по официальным источникам (контакты, сайты)"""
        sources = self.knowledge_base.get("official_sources", {})
        query_lower = query.lower()
        results = []
        
        for source_info in sources.values():
            name = source_info.get('name', '').lower()
            desc = source_info.get('description', '').lower()
            
            if any(kw in query_lower for kw in [name, 'общежитие', 'приёмная', 'контакт', 'сайт']):
                result = f"<b>{source_info.get('name', '')}</b>\n"
                result += f"{source_info.get('description', '')}\n"
                if source_info.get('website'):
                    result += f"🔗 {source_info['website']}"
                results.append(result)
        
        return results
    
    # ============================================================================
    # 🔹 ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ЗАПРОСА
    # ============================================================================
    
    def _detect_category(self, query: str) -> Optional[str]:
        """
        Определяет категорию запроса по ключевым словам.
        
        Returns:
            str: Название категории или None если не определено
        """
        query_lower = query.lower()
        best_category = None
        best_score = 0
        
        for category, config in self.SEARCH_CATEGORIES.items():
            score = sum(1 for kw in config['keywords'] if kw in query_lower)
            
            if score >= self.SEARCH_CONFIG["min_keyword_matches"] and score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _get_special_context(self, query: str, category: Optional[str]) -> list[str]:
        """
        Возвращает специальный контекст для определённых категорий.
        Например, прямая информация о стипендиях из приказа.
        """
        query_lower = query.lower()
        special_contexts = []
        
        # 🔥 СПЕЦИАЛЬНЫЙ КОНТЕКСТ: СТИПЕНДИИ
        if category == "scholarships" or any(kw in query_lower for kw in ['стипенд', 'отличник', 'гас', 'пгас']):
            stipend_info = (
                "<b>💰 Стипендии в ДГТУ (Приказ №2662-ЛС-О от 23.05.2025):</b>\n\n"
                
                "<b>📚 Государственная академическая (ГАС):</b>\n"
                "• 1 курс: 3 000 ₽/мес | «Хорошо»: 3 500 ₽/мес | «Отлично»: 4 500 ₽/мес\n\n"
                
                "<b>🏆 Повышенная академическая (ПГАС):</b>\n"
                "• 1-2 курс: 15 500 ₽/мес | 3 курс: 16 000 ₽/мес | 4-6 курс: 17 000 ₽/мес | Магистратура: 18 000 ₽/мес\n\n"
                
                "<b>🤝 Социальная (ГСС):</b>\n"
                "• Дети-сироты: 6 000 ₽/мес | Соц. помощь: 4 000 ₽/мес"
            )
            special_contexts.append(stipend_info)
        
        # 🔥 СПЕЦИАЛЬНЫЙ КОНТЕКСТ: ПРОХОДНЫЕ БАЛЛЫ
        if category == "passing_scores" or any(kw in query_lower for kw in ['проходн', 'балл', 'егэ', '09.03']):
            passing_info = (
                "<b>📊 Проходные баллы ИиВТ ДГТУ 2025:</b>\n\n"
                "• 01.03.04 Прикладная математика: 177 (50 мест)\n"
                "• 02.03.03 Мат. обеспечение: 193 (75 мест)\n"
                "• 09.03.01 Информатика и ВТ: 205 (477* мест)\n"
                "• 09.03.02 ИИ: 205 (477* мест) ← ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ ✨\n"
                "• 09.03.02 WEB: 210 (477* мест)\n"
                "• 09.03.04 Программная инженерия: 205 (477* мест)\n"
                "• 10.03.01 Инф. безопасность: 210 (42 места)\n\n"
                "<i>💡 477* — на все направления группы 09.03.02</i>"
            )
            special_contexts.append(passing_info)
        
        # 🔥 СПЕЦИАЛЬНЫЙ КОНТЕКСТ: ОБЩЕЖИТИЕ
        if category == "dormitory" or any(kw in query_lower for kw in ['общежит', 'общага', 'нагибина']):
            dorm_info = (
                "<b>🏠 Общежитие для студентов ИиВТ:</b>\n\n"
                "• Предоставляется иногородним студентам очной формы\n"
                "• Стоимость: ~1 500 ₽/мес (ориентировочно)\n"
                "• Адрес: пр. Михаила Нагибина, 5 (5-10 мин до корпуса)\n"
                "• Типы: квартирный, блочный, коридорный\n\n"
                "<b>📋 Как подать заявку:</b>\n"
                "1. Личный кабинет на donstu.ru\n"
                "2. Вкладка «Анкетирование» → «Конкурс на общежитие»\n"
                "3. Дождаться решения комиссии\n\n"
                "📞 Контакты: +7 (863) 273-85-85"
            )
            special_contexts.append(dorm_info)
        
        return special_contexts
    
    # ============================================================================
    # 🔹 ГЛАВНЫЙ МЕТОД ПОИСКА КОНТЕКСТА
    # ============================================================================
    
    async def find_relevant_context(self, question: str, debug: bool = False, user_id: int = None) -> str | dict:
        """
        🔍 Поиск релевантного контекста
        
        Args:
            question: Вопрос пользователя
            debug: Если True — возвращает мета-информацию для отладки
            user_id: ID пользователя для логирования
            
        Returns:
            str: Контекст для ИИ (обычный режим)
            dict: {context, category, keywords, parts} (debug режим)
        """
        # 🔥 1. ПРОВЕРКА КЭША
        cache_key = f"ctx:{question.lower()[:50]}"
        cached = await cache.get(cache_key)
        cache_hit = cached is not None
        
        if cached:
            logger.debug(f"✅ Контекст из кэша: {question[:40]}...")
            
            # 🔥 ЛОГИРОВАНИЕ В БД
            if user_id:
                from models.database import db
                await db.log_search_query(
                    user_id=user_id,
                    query=question[:200],
                    category="cached",
                    cache_hit=True,
                    context_parts=1
                )
            
            if debug:
                return {
                    "context": cached,
                    "category": "cached",
                    "keywords": [],
                    "parts": 1,
                    "cache_hit": True
                }
            return cached
        
        # 🔥 2. ПОДГОТОВКА
        query_lower = question.lower().strip()
        context_parts: list[str] = []
        category = self._detect_category(query_lower)
        found_keywords = []
        
        # 🔥 3. СПЕЦИАЛЬНЫЕ ЗАПРОСЫ
        if any(kw in query_lower for kw in ['иивт', 'направления', 'специальности', 'все направления', 'куда поступать']):
            summary = self._get_all_programs_summary()
            if summary:
                context_parts.append(f"🎓 <b>ВСЕ НАПРАВЛЕНИЯ ИиВТ ДГТУ:</b>\n\n{summary}")
        
        # 🔥 4. СПЕЦИАЛЬНЫЙ КОНТЕКСТ ПО КАТЕГОРИИ
        special = self._get_special_context(query_lower, category)
        context_parts.extend(special)
        
        # 🔥 5. ПОИСК ПО НАПРАВЛЕНИЯМ
        for code in self.knowledge_base.get("programs", {}).keys():
            if code in query_lower or query_lower.replace('.', '') in code.replace('.', ''):
                result = self._search_by_code(code)
                if result and result not in context_parts:
                    context_parts.append(result)
                    found_keywords.append(code)
        
        if category != "passing_scores":
            name_results = self._search_by_name(query_lower)
            if name_results and name_results not in context_parts:
                context_parts.append(name_results)
        
        keyword_results = self._search_by_keywords(query_lower)
        for result in keyword_results:
            if result not in context_parts:
                context_parts.append(result)
        
        # 🔥 6. ПОИСК ПО FAQ
        faq_results = self._search_faq(query_lower, category)
        for result in faq_results:
            if result not in context_parts:
                context_parts.append(result)
        
        # 🔥 7. ПОИСК ПО ИСТОЧНИКАМ
        source_results = self._search_official_sources(query_lower)
        for result in source_results:
            if result not in context_parts:
                context_parts.append(result)
        
        # 🔥 8. ДНИ ОТКРЫТЫХ ДВЕРЕЙ
        if any(kw in query_lower for kw in ['день открытых дверей', 'дата', 'когда', 'апрель']):
            open_days = self.knowledge_base.get("open_days", {})
            if open_days:
                context_parts.append(
                    f"<b>📅 Дни открытых дверей:</b>\n"
                    f"• ДГТУ: {open_days.get('dstu', '—')}\n"
                    f"• ИиВТ: {open_days.get('iivt', '—')}"
                )
        
        # 🔥 9. ФОРМИРОВАНИЕ КОНТЕКСТА
        if context_parts:
            unique_parts = list(dict.fromkeys(context_parts))
            
            if any(kw in query_lower for kw in ['иивт', 'направления', 'все направления']):
                context = "\n\n===\n\n".join(unique_parts)
            else:
                max_parts = self.SEARCH_CONFIG["max_context_parts"]
                context = "\n\n===\n\n".join(unique_parts[:max_parts])
        else:
            context = "Информация не найдена в официальных источниках ДГТУ."
        
        # 🔥 10. СОХРАНЕНИЕ В КЭШ
        await cache.set(cache_key, context)
        
        # 🔥 11. ЛОГИРОВАНИЕ В БД
        if user_id:
            from models.database import db
            await db.log_search_query(
                user_id=user_id,
                query=question[:200],
                category=category,
                cache_hit=False,
                context_parts=len(context_parts)
            )
        
        # 🔥 12. СОХРАНЕНИЕ ИНТЕРЕСА (ПЕРСОНАЛИЗАЦИЯ) — ИСПРАВЛЕННОЕ
        if user_id:
            from models.database import db
            
            # 🔥 12.1 Сначала проверяем: есть ли в запросе код/название направления
            program_found = False
            for code, keywords in self.PROGRAM_KEYWORDS.items():
                # Проверяем код направления (с точками и без)
                if code in query_lower or code.replace('.', '') in query_lower.replace('.', ''):
                    await db.save_user_interest(user_id, "program", code)
                    program_found = True
                    logger.debug(f"🎯 Сохранён интерес: program → {code}")
                    break
                
                # Проверяем ключевые слова направления
                if any(kw in query_lower for kw in keywords):
                    await db.save_user_interest(user_id, "program", code)
                    program_found = True
                    logger.debug(f"🎯 Сохранён интерес: program → {code} (by keyword)")
                    break
            
            # 🔥 12.2 Если направление не найдено — проверяем категории FAQ
            if not program_found and category:
                if category in ["scholarships", "dormitory", "documents", "deadlines", 
                               "cost", "passing_scores", "vuts", "contacts"]:
                    await db.save_user_interest(user_id, "faq", category)
                    logger.debug(f"🎯 Сохранён интерес: faq → {category}")
        
        # 🔥 13. DEBUG РЕЖИМ
        if debug:
            return {
                "context": context,
                "category": category,
                "keywords": found_keywords,
                "parts": len(context_parts),
                "cache_hit": False,
                "cache_key": cache_key
            }
        
        return context
    
    # ============================================================================
    # 🔹 УТИЛИТЫ
    # ============================================================================
    
    def get_stats(self) -> dict:
        """Возвращает статистику базы знаний"""
        programs = self.knowledge_base.get("programs", {})
        faq = self.knowledge_base.get("faq", {})
        sources = self.knowledge_base.get("official_sources", {})
        
        return {
            "programs_count": len(programs),
            "faq_count": len(faq),
            "sources_count": len(sources),
            "total_sections": len(self.knowledge_base),
        }
    
    def list_programs(self) -> list[dict]:
        """Возвращает список всех направлений для отладки"""
        programs = self.knowledge_base.get("programs", {})
        return [
            {"code": code, "name": info.get("name"), "profile": info.get("profile")}
            for code, info in programs.items()
        ]


# ============================================================================
# 🔥 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================================

rag_service = RAGService()
