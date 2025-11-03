from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu

router = Router()


@router.message(CommandStart())
async def start(m: Message) -> None:
    await m.answer(
        "🚀 <b>Shadowrocket Config Manager</b>\n\nУправляйте правилами через Telegram\n\n📊 /stats — статистика\n🕒 /recent — последние изменения\n⚙️ /normalize — нормализация",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🏠 Главное меню")
async def back_to_menu(m: Message) -> None:
    await m.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())
