from aiogram import Router, types, F
from aiogram.filters import Command
from services.rag_service import rag_service
from handlers.faq_handler import send_single_message, _clean_html
import logging

logger = logging.getLogger(__name__)
router = Router()

SYNONYMS = {
    "общага": ["общежитие", "студенческий городок", "жильё"],
    "деньги": ["стоимость", "цена", "платно", "бюджет", "стипендия"],
    "сколько стоит": ["стоимость", "цена", "платно"],
    "стипуха": ["стипендия", "деньги"],
    "баллы": ["проходные баллы", "егэ", "поступление"],
    "проходной": ["проходные баллы", "егэ", "поступление"],
    "куда поступать": ["направления", "специальности", "профили"],
    "декан": ["деканат", "руководство"],
    "вуц": ["военная кафедра", "военный учебный центр", "армия"],
    "расписание": ["занятия", "пары", "экзамены"],
    "телефон": ["контакты", "связь", "позвонить"],
}

@router.message(Command("search"))
async def smart_search_command(message: types.Message):
    """🔍 УМНЫЙ ПОИСК"""
    
    if len(message.text.split()) > 1:
        query = message.text.replace("/search", "").strip()
        await process_smart_search(message, query)
        return
    
    text = (
        "🔍 <b>Умный поиск по базе знаний</b>\n\n"
        
        "📝 <b>Просто напиши:</b>\n"
        "• <code>/search общежитие</code>\n"
        "• <code>/search стоимость</code>\n"
        "• <code>/search проходные баллы</code>\n\n"
        
        "💡 <b>Я понимаю:</b>\n"
        "• Синонимы (общага = общежитие)\n"
        "• Опечатки\n"
        "• Разные формулировки"
    )
    
    await message.answer(text)

async def process_smart_search(message: types.Message, query: str):
    """🔍 Обработка поиска"""
    
    logger.info(f"🔍 Поиск: {query}")
    
    context = await rag_service.find_relevant_context(query)
    
    if context:
        answer = _clean_html(context)
        await send_single_message(message, answer)
    else:
        query_lower = query.lower()
        found = False
        
        for key, synonyms in SYNONYMS.items():
            if query_lower in key or any(s in query_lower for s in synonyms):
                found = True
                await message.answer(
                    f"💡 <b>Поиск:</b> {key}\n\n"
                    f"🔗 <b>Разделы:</b>\n"
                    f"• /faq — вопросы\n"
                    f"• /start — меню"
                )
                break
        
        if not found:
            await message.answer(
                "⚠️ <b>Не найдено</b>\n\n"
                "💡 <b>Попробуй:</b>\n"
                "• /faq — частые вопросы\n"
                "• /ai_assistant — ИИ-помощник\n"
                "• /quick_help — связь с волонтёром"
            )
