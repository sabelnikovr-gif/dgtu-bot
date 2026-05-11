from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from handlers.utils import send_single_message, get_back_keyboard, user_last_message, PHOTO_DGTU_LOGO, PHOTO_BUILDING
from handlers.faq_handler import safe_callback_answer, show_main_menu_from_welcome
from services.rag_service import rag_service
from pathlib import Path
import logging

router = Router()
logger = logging.getLogger(__name__)

# ============================================================================
# 🔥 СОСТОЯНИЯ ТЕСТА
# ============================================================================

class QuizState(StatesGroup):
    """Состояния для теста на выбор направления"""
    waiting_for_q1 = State()
    waiting_for_q2 = State()
    waiting_for_q3 = State()
    waiting_for_q4 = State()
    waiting_for_q5 = State()

# ============================================================================
# 🔥 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОТПРАВКИ С ФОТО
# ============================================================================

async def send_photo_message(callback, text, reply_markup, photo_path):
    """
    🔥 ОТПРАВКА СООБЩЕНИЯ С ФОТО
    
    Args:
        callback: CallbackQuery
        text: Текст сообщения
        reply_markup: Клавиатура
        photo_path: Путь к фото
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    bot = callback.bot
    old_msg_id = user_last_message.get(user_id)
    
    try:
        if old_msg_id:
            try:
                old_message = await bot.get_message(chat_id, old_msg_id)
                has_photo = bool(old_message.photo)
            except:
                has_photo = False
            
            if len(text) > 1024:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
                except:
                    pass
                new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                user_last_message[user_id] = new_msg.message_id
            elif has_photo and photo_path and Path(photo_path).exists():
                media = InputMediaPhoto(media=FSInputFile(photo_path), caption=text, parse_mode="HTML")
                await bot.edit_message_media(media=media, chat_id=chat_id, message_id=old_msg_id, reply_markup=reply_markup)
            else:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
                except:
                    pass
                if photo_path and Path(photo_path).exists() and len(text) <= 1024:
                    new_msg = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(photo_path), caption=text, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                user_last_message[user_id] = new_msg.message_id
        else:
            if photo_path and Path(photo_path).exists() and len(text) <= 1024:
                new_msg = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(photo_path), caption=text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
            user_last_message[user_id] = new_msg.message_id
    except Exception as e:
        logger.error(f"❌ Ошибка отправки фото: {e}")
        try:
            new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
            user_last_message[user_id] = new_msg.message_id
        except Exception as e2:
            logger.error(f"❌ Ошибка отправки текста: {e2}")

# ============================================================================
# 🔥 НАЧАЛО ТЕСТА
# ============================================================================

@router.callback_query(lambda c: c.data == "quiz_start")
async def quiz_start(callback: types.CallbackQuery, state: FSMContext):
    """🎯 Начало теста на выбор направления"""
    user_id = callback.from_user.id
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "🎯 <b>Тест на выбор направления</b>\n\n"
        "📝 <b>Ответь на 5 вопросов</b> и узнай, какое направление тебе подходит!\n\n"
        "💡 <b>Вопрос 1 из 5:</b>\n"
        "Какой предмет тебе нравится больше?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Математика и алгоритмы", callback_data="q1_math")],
        [InlineKeyboardButton(text="💻 Программирование", callback_data="q1_code")],
        [InlineKeyboardButton(text="🔍 Анализ данных", callback_data="q1_data")],
        [InlineKeyboardButton(text="🛡️ Защита информации", callback_data="q1_security")],
        [InlineKeyboardButton(text="🤖 Искусственный интеллект", callback_data="q1_ai")],
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    await state.set_state(QuizState.waiting_for_q1)
    await callback.answer()

# ============================================================================
# 🔥 ВОПРОС 2
# ============================================================================

@router.callback_query(QuizState.waiting_for_q1)
async def quiz_q2(callback: types.CallbackQuery, state: FSMContext):
    """Вопрос 2"""
    user_id = callback.from_user.id
    await state.update_data(q1=callback.data)
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "💡 <b>Вопрос 2 из 5:</b>\n"
        "Какая сфера тебе интереснее?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Искусственный интеллект и нейросети", callback_data="q2_ai")],
        [InlineKeyboardButton(text="🌐 Web-разработка и дизайн", callback_data="q2_web")],
        [InlineKeyboardButton(text="📊 Анализ больших данных", callback_data="q2_analytics")],
        [InlineKeyboardButton(text="🔐 Кибербезопасность", callback_data="q2_security")],
        [InlineKeyboardButton(text="📱 Мобильные приложения", callback_data="q2_mobile")],
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    await state.set_state(QuizState.waiting_for_q2)
    await callback.answer()

# ============================================================================
# 🔥 ВОПРОС 3
# ============================================================================

@router.callback_query(QuizState.waiting_for_q2)
async def quiz_q3(callback: types.CallbackQuery, state: FSMContext):
    """Вопрос 3"""
    user_id = callback.from_user.id
    await state.update_data(q2=callback.data)
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "💡 <b>Вопрос 3 из 5:</b>\n"
        "Как ты предпочитаешь работать?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Писать код и создавать программы", callback_data="q3_coding")],
        [InlineKeyboardButton(text="📈 Анализировать и исследовать", callback_data="q3_analyze")],
        [InlineKeyboardButton(text="🎨 Создавать интерфейсы и дизайн", callback_data="q3_design")],
        [InlineKeyboardButton(text="🔧 Настраивать системы и сети", callback_data="q3_systems")],
        [InlineKeyboardButton(text="🧪 Экспериментировать и тестировать", callback_data="q3_test")],
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    await state.set_state(QuizState.waiting_for_q3)
    await callback.answer()

# ============================================================================
# 🔥 ВОПРОС 4
# ============================================================================

@router.callback_query(QuizState.waiting_for_q3)
async def quiz_q4(callback: types.CallbackQuery, state: FSMContext):
    """Вопрос 4"""
    user_id = callback.from_user.id
    await state.update_data(q3=callback.data)
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "💡 <b>Вопрос 4 из 5:</b>\n"
        "Какая технология тебя привлекает?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Машинное обучение и AI", callback_data="q4_ml")],
        [InlineKeyboardButton(text="☁️ Облачные технологии", callback_data="q4_cloud")],
        [InlineKeyboardButton(text="📱 Мобильная разработка", callback_data="q4_mobile")],
        [InlineKeyboardButton(text="🔐 Криптография и защита", callback_data="q4_crypto")],
        [InlineKeyboardButton(text="📐 Математическое моделирование", callback_data="q4_math")],
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    await state.set_state(QuizState.waiting_for_q4)
    await callback.answer()

# ============================================================================
# 🔥 ВОПРОС 5
# ============================================================================

@router.callback_query(QuizState.waiting_for_q4)
async def quiz_q5(callback: types.CallbackQuery, state: FSMContext):
    """Вопрос 5"""
    user_id = callback.from_user.id
    await state.update_data(q4=callback.data)
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "💡 <b>Вопрос 5 из 5:</b>\n"
        "Какую карьеру ты видишь?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Разработчик в IT-компании", callback_data="q5_dev")],
        [InlineKeyboardButton(text="🔬 Научный сотрудник / аналитик", callback_data="q5_science")],
        [InlineKeyboardButton(text="👨‍💼 Руководитель проектов", callback_data="q5_manager")],
        [InlineKeyboardButton(text="🛡️ Специалист по безопасности", callback_data="q5_security")],
        [InlineKeyboardButton(text="💻 Фрилансер / стартапер", callback_data="q5_freelance")],
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    await state.set_state(QuizState.waiting_for_q5)
    await callback.answer()

# ============================================================================
# 🔥 ОТМЕНА ТЕСТА
# ============================================================================

@router.callback_query(lambda c: c.data == "quiz_cancel")
async def quiz_cancel(callback: types.CallbackQuery, state: FSMContext):
    """❌ Отмена теста"""
    await state.clear()
    await callback.answer("Тест отменён")
    await show_main_menu_from_welcome(callback)

# ============================================================================
# 🔥 РЕЗУЛЬТАТ ТЕСТА
# ============================================================================

@router.callback_query(QuizState.waiting_for_q5)
async def quiz_result(callback: types.CallbackQuery, state: FSMContext):
    """🎯 Результат теста"""
    user_id = callback.from_user.id
    
    await state.update_data(q5=callback.data)
    data = await state.get_data()
    
    answers = [data.get(f'q{i}') for i in range(1, 6)]
    
    # 🔥 ПОДСЧЁТ БАЛЛОВ ДЛЯ КАЖДОГО НАПРАВЛЕНИЯ
    scores = {
        "01.03.04": 0, "02.03.03": 0, "09.03.01": 0, "09.03.02_ist": 0,
        "09.03.02_ai": 0, "09.03.02_web": 0, "09.03.02_zaoch": 0,
        "09.03.03": 0, "09.03.03_zaoch": 0, "09.03.04": 0,
        "10.03.01": 0, "10.05.01": 0, "10.05.02": 0,
    }
    
    for answer in answers:
        if answer in ['q1_math', 'q4_math']:
            scores["01.03.04"] += 2
            scores["02.03.03"] += 1
        if answer in ['q1_code', 'q3_coding']:
            scores["09.03.04"] += 2
            scores["09.03.02_ist"] += 1
            scores["09.03.02_web"] += 1
        if answer in ['q1_ai', 'q2_ai', 'q4_ml']:
            scores["09.03.02_ai"] += 2
            scores["01.03.04"] += 1
        if answer in ['q2_web', 'q3_design']:
            scores["09.03.02_web"] += 2
            scores["09.03.04"] += 1
        if answer in ['q1_data', 'q2_analytics', 'q3_analyze']:
            scores["09.03.03"] += 2
            scores["09.03.02_ist"] += 1
        if answer in ['q1_security', 'q2_security', 'q4_crypto', 'q5_security']:
            scores["10.03.01"] += 2
            scores["10.05.01"] += 1
            scores["10.05.02"] += 1
        if answer in ['q2_mobile', 'q4_mobile']:
            scores["09.03.04"] += 1
            scores["09.03.02_web"] += 1
        if answer in ['q4_cloud', 'q3_systems']:
            scores["09.03.01"] += 2
            scores["09.03.02_ist"] += 1
        if answer in ['q5_science', 'q3_test']:
            scores["01.03.04"] += 1
            scores["02.03.03"] += 1
        if answer == 'q5_dev':
            scores["09.03.04"] += 1
            scores["09.03.02_ist"] += 1
            scores["09.03.02_web"] += 1
        if answer == 'q5_manager':
            scores["09.03.03"] += 1
            scores["09.03.04"] += 1
        if answer == 'q5_freelance':
            scores["09.03.02_web"] += 1
            scores["09.03.04"] += 1
    
    # 🔥 НАХОДИМ НАПРАВЛЕНИЕ С МАКСИМАЛЬНЫМ СЧЁТОМ
    max_score = max(scores.values())
    top_directions = [code for code, score in scores.items() if score == max_score]
    best_direction = top_directions[0]
    
    # 🔥 ИНФОРМАЦИЯ О НАПРАВЛЕНИЯХ
    directions_info = {
        "01.03.04": {"name": "Прикладная математика", "pass": 177, "budget": 50, "desc": "Математическое моделирование, вычислительные методы, алгоритмы"},
        "02.03.03": {"name": "Математическое обеспечение и администрирование", "pass": 193, "budget": 75, "desc": "Администрирование баз данных, математическое ПО"},
        "09.03.01": {"name": "Информатика и вычислительная техника", "pass": 205, "budget": 477, "desc": "Аппаратное обеспечение, компьютерные системы, сети"},
        "09.03.02_ist": {"name": "Информационные системы и технологии (ИСТ)", "pass": 201, "budget": 477, "desc": "Разработка информационных систем, баз данных"},
        "09.03.02_ai": {"name": "Искусственный интеллект (ИИ)", "pass": 205, "budget": 477, "desc": "Машинное обучение, нейросети, анализ данных"},
        "09.03.02_web": {"name": "Web-разработка (WEB)", "pass": 210, "budget": 477, "desc": "Создание сайтов, веб-приложений, интерфейсов"},
        "09.03.02_zaoch": {"name": "Информационные системы (заочное)", "pass": 188, "budget": 30, "desc": "Заочная форма обучения, ИСТ"},
        "09.03.03": {"name": "Прикладная информатика", "pass": 205, "budget": 477, "desc": "Анализ данных, бизнес-информатика, автоматизация"},
        "09.03.03_zaoch": {"name": "Прикладная информатика (заочное)", "pass": 187, "budget": 30, "desc": "Заочная форма обучения, прикладная информатика"},
        "09.03.04": {"name": "Программная инженерия", "pass": 205, "budget": 477, "desc": "Разработка ПО, программирование, тестирование"},
        "10.03.01": {"name": "Информационная безопасность", "pass": 210, "budget": 42, "desc": "Защита информации, криптография, кибербезопасность"},
        "10.05.01": {"name": "Компьютерная безопасность (специалитет)", "pass": 198, "budget": 150, "desc": "Защита компьютерных систем, 5 лет обучения"},
        "10.05.02": {"name": "Информационная безопасность (специалитет)", "pass": 198, "budget": 150, "desc": "Защита информации, 5 лет обучения"},
    }
    
    info = directions_info.get(best_direction, {})
    name = info.get("name", "Неизвестное направление")
    desc = info.get("desc", "")
    pass_score = info.get("pass", 0)
    budget = info.get("budget", 0)
    
    budget_text = f"{budget}*" if budget == 477 else budget
    
    text = (
        f"🎯 <b>Твой результат:</b>\n\n"
        f"✅ <b>{name}</b>\n\n"
        f"📌 <b>Описание:</b>\n"
        f"{desc}\n\n"
        f"📊 <b>Проходной балл 2025:</b> {pass_score}\n"
        f"💰 <b>Бюджетных мест:</b> {budget_text}\n\n"
        f"💡 <b>Совет:</b>\n"
        f"Подготовься к ЕГЭ и набери {pass_score + 10}+ баллов для высокого шанса!\n\n"
        f"👇 <b>Что дальше?</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Подробнее о направлении", callback_data=f"program_{best_direction}")],
        [InlineKeyboardButton(text="🧮 Калькулятор баллов", callback_data="calculator_btn")],
        [InlineKeyboardButton(text="🔄 Пройти ещё раз", callback_data="quiz_start")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])
    
    # 🔥 ОТПРАВЛЯЕМ С ФОТО
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    
    # 🔥 Очищаем состояние теста
    await state.clear()
    await callback.answer()
