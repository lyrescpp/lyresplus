from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from course_data import MODULES


def kb_main_menu() -> InlineKeyboardMarkup:
    buttons = []
    for mod_id, mod in MODULES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{mod['emoji']} Модуль {mod_id} — {mod['title']}",
                callback_data=f"mod_{mod_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🤖 Спросить AI", callback_data="ai_free"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_module(mod_id: str) -> InlineKeyboardMarkup:
    mod = MODULES[mod_id]
    buttons = []
    
    for lesson_id, lesson in mod["lessons"].items():
        buttons.append([
            InlineKeyboardButton(
                text=f"📖 {lesson['title']}",
                callback_data=f"lesson_{mod_id}_{lesson_id}"
            )
        ])
    
    if "task" in mod:
        buttons.append([
            InlineKeyboardButton(
                text="🎯 Задание",
                callback_data=f"task_{mod_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="🤖 AI-куратор модуля",
            callback_data=f"ai_mod_{mod_id}"
        )
    ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_lesson(mod_id: str, lesson_id: str) -> InlineKeyboardMarkup:
    mod = MODULES[mod_id]
    lesson_ids = list(mod["lessons"].keys())
    current_idx = lesson_ids.index(lesson_id)
    
    nav_row = []
    if current_idx > 0:
        prev_id = lesson_ids[current_idx - 1]
        nav_row.append(InlineKeyboardButton(
            text="◀️ Пред.",
            callback_data=f"lesson_{mod_id}_{prev_id}"
        ))
    
    if current_idx < len(lesson_ids) - 1:
        next_id = lesson_ids[current_idx + 1]
        nav_row.append(InlineKeyboardButton(
            text="След. ▶️",
            callback_data=f"lesson_{mod_id}_{next_id}"
        ))
    
    buttons = []
    if nav_row:
        buttons.append(nav_row)
    
    row2 = []
    if "task" in mod:
        row2.append(InlineKeyboardButton(
            text="🎯 Задание",
            callback_data=f"task_{mod_id}"
        ))
    row2.append(InlineKeyboardButton(
        text="🤖 AI-куратор",
        callback_data=f"ai_mod_{mod_id}"
    ))
    buttons.append(row2)
    
    buttons.append([
        InlineKeyboardButton(text="◀️ К модулю", callback_data=f"mod_{mod_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_task(mod_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🤖 Проверить AI",
            callback_data=f"task_check_{mod_id}"
        )],
        [InlineKeyboardButton(text="◀️ К модулю", callback_data=f"mod_{mod_id}")]
    ])


def kb_task_check(mod_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Попробовать снова",
            callback_data=f"task_{mod_id}"
        )],
        [InlineKeyboardButton(text="◀️ К модулю", callback_data=f"mod_{mod_id}")]
    ])


def kb_back_to_mod(mod_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К модулю", callback_data=f"mod_{mod_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def kb_cancel_ai() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Выйти из чата", callback_data="main_menu")]
    ])
