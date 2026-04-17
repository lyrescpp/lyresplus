from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from course_data import MODULES
from keyboards import (
    kb_main_menu, kb_module, kb_lesson,
    kb_task, kb_task_check, kb_back_to_mod, kb_cancel_ai
)
from ai_helper import ask_ai

router = Router()

# ─── FSM States ───────────────────────────────────────
class UserState(StatesGroup):
    waiting_task_answer = State()   # ждём ответ на задание
    in_ai_chat = State()            # свободный чат с AI
    in_ai_mod_chat = State()        # чат с AI по модулю

# ─── Приветствие ──────────────────────────────────────
WELCOME = """
╔══════════════════════════════╗
║   🛡️  LYRES COURSE BOT       ║
║   Разработчик БПЛА / C++     ║
╚══════════════════════════════╝

Привет! Это твой персональный курс для работы в <b>Алмаз-Антей</b> на направлении <b>БПЛА</b>.

🎯 <b>Что тут есть:</b>
• 6 модулей — от теории до практики
• Примеры кода под беспилотники
• Задания с проверкой через AI
• AI-куратор по каждой теме

Выбирай модуль и поехали 👇
"""

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME, reply_markup=kb_main_menu(), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=kb_main_menu(), parse_mode="HTML")


# ─── Главное меню ─────────────────────────────────────
@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(WELCOME, reply_markup=kb_main_menu(), parse_mode="HTML")


# ─── О боте ───────────────────────────────────────────
@router.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery):
    text = """
🛡️ <b>LYRES COURSE BOT</b>

Персональный курс для подготовки к работе программистом C++ в оборонном холдинге <b>Алмаз-Антей</b> на направлении разработки БПЛА.

<b>Модули:</b>
00 — Что такое Алмаз-Антей и БПЛА
01 — C++ с нуля (переменные, типы, условия, циклы)
02 — Функции
03 — ООП и классы
04 — Память и указатели
05 — Linux, g++, CMake, git

<b>AI-куратор:</b> Llama 3.3 70B через Groq

<i>by LYRES</i>
"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ─── Модуль ───────────────────────────────────────────
@router.callback_query(F.data.startswith("mod_"))
async def cb_module(call: CallbackQuery, state: FSMContext):
    await state.clear()
    mod_id = call.data.split("_")[1]
    mod = MODULES.get(mod_id)
    if not mod:
        await call.answer("Модуль не найден")
        return

    lesson_count = len(mod["lessons"])
    has_task = "task" in mod

    text = f"""{mod['emoji']} <b>Модуль {mod_id} — {mod['title']}</b>

{mod['desc']}

📚 Уроков: {lesson_count}
{"🎯 Есть задание с проверкой AI" if has_task else ""}

Выбери урок 👇"""

    await call.message.edit_text(text, reply_markup=kb_module(mod_id), parse_mode="HTML")


# ─── Урок ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("lesson_"))
async def cb_lesson(call: CallbackQuery, state: FSMContext):
    await state.clear()
    _, mod_id, lesson_id = call.data.split("_")
    mod = MODULES.get(mod_id)
    if not mod:
        return

    lesson = mod["lessons"].get(lesson_id)
    if not lesson:
        return

    total = len(mod["lessons"])
    header = f"<b>Модуль {mod_id} · Урок {lesson_id}/{total}</b>\n\n"

    await call.message.edit_text(
        header + lesson["text"],
        reply_markup=kb_lesson(mod_id, lesson_id),
        parse_mode="HTML"
    )


# ─── Задание ──────────────────────────────────────────
@router.callback_query(F.data.startswith("task_") & ~F.data.startswith("task_check_"))
async def cb_task(call: CallbackQuery, state: FSMContext):
    mod_id = call.data.split("_")[1]
    mod = MODULES.get(mod_id)
    if not mod or "task" not in mod:
        return

    await state.set_state(UserState.waiting_task_answer)
    await state.update_data(task_mod_id=mod_id)

    await call.message.edit_text(
        mod["task"]["text"] + "\n\n✏️ <i>Напиши свой ответ следующим сообщением</i>",
        reply_markup=kb_task(mod_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("task_check_"))
async def cb_task_check_prompt(call: CallbackQuery, state: FSMContext):
    mod_id = call.data.split("_")[2]
    mod = MODULES.get(mod_id)
    if not mod or "task" not in mod:
        return

    await state.set_state(UserState.waiting_task_answer)
    await state.update_data(task_mod_id=mod_id)

    await call.answer("Напиши ответ следующим сообщением ✏️")


@router.message(UserState.waiting_task_answer)
async def handle_task_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    mod_id = data.get("task_mod_id")
    mod = MODULES.get(mod_id)

    if not mod or "task" not in mod:
        await state.clear()
        return

    thinking = await message.answer("🤖 <i>AI проверяет твой ответ...</i>", parse_mode="HTML")

    system = "Ты строгий но справедливый преподаватель C++ для разработчиков БПЛА. Проверяешь задания и даёшь развёрнутый фидбек на русском языке. Если есть код — разбери его. Покажи правильное решение если есть ошибки."
    prompt = mod["task"]["check_prompt"] + message.text

    result = await ask_ai(system, prompt)

    await thinking.delete()
    await message.answer(
        f"🤖 <b>Проверка AI:</b>\n\n{result}",
        reply_markup=kb_task_check(mod_id),
        parse_mode="HTML"
    )
    await state.clear()


# ─── AI чат по модулю ─────────────────────────────────
@router.callback_query(F.data.startswith("ai_mod_"))
async def cb_ai_mod(call: CallbackQuery, state: FSMContext):
    mod_id = call.data.split("_")[2]
    mod = MODULES.get(mod_id)
    if not mod:
        return

    await state.set_state(UserState.in_ai_mod_chat)
    await state.update_data(ai_mod_id=mod_id, ai_history=[])

    text = f"""🤖 <b>AI-куратор — Модуль {mod_id}: {mod['title']}</b>

Задавай любые вопросы по теме. Объясню с примерами из БПЛА и ОПК.

Чтобы выйти — нажми кнопку ниже или напиши /menu"""

    await call.message.edit_text(text, reply_markup=kb_cancel_ai(), parse_mode="HTML")


# ─── AI свободный чат ─────────────────────────────────
@router.callback_query(F.data == "ai_free")
async def cb_ai_free(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.in_ai_chat)
    await state.update_data(ai_history=[])

    text = """🤖 <b>Свободный AI-чат</b>

Задавай любые вопросы — по C++, Linux, БПЛА, ОПК, карьере.

Чтобы выйти — нажми кнопку ниже или напиши /menu"""

    await call.message.edit_text(text, reply_markup=kb_cancel_ai(), parse_mode="HTML")


@router.message(UserState.in_ai_mod_chat)
async def handle_ai_mod_message(message: Message, state: FSMContext):
    data = await state.get_data()
    mod_id = data.get("ai_mod_id")
    mod = MODULES.get(mod_id, {})
    history = data.get("ai_history", [])

    thinking = await message.answer("🤖 <i>Думаю...</i>", parse_mode="HTML")

    system = mod.get("ai_context", "Ты эксперт по C++ и разработке БПЛА. Отвечай на русском.")
    reply = await ask_ai(system, message.text, history)

    history.append({"role": "user", "content": message.text})
    history.append({"role": "assistant", "content": reply})
    await state.update_data(ai_history=history[-10:])

    await thinking.delete()
    await message.answer(reply, reply_markup=kb_cancel_ai(), parse_mode="HTML")


@router.message(UserState.in_ai_chat)
async def handle_ai_free_message(message: Message, state: FSMContext):
    data = await state.get_data()
    history = data.get("ai_history", [])

    thinking = await message.answer("🤖 <i>Думаю...</i>", parse_mode="HTML")

    system = "Ты эксперт по C++, разработке БПЛА, Linux и карьере в оборонной промышленности России. Отвечай на русском языке, подробно и с примерами."
    reply = await ask_ai(system, message.text, history)

    history.append({"role": "user", "content": message.text})
    history.append({"role": "assistant", "content": reply})
    await state.update_data(ai_history=history[-10:])

    await thinking.delete()
    await message.answer(reply, reply_markup=kb_cancel_ai(), parse_mode="HTML")
