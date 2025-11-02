"""Global cancel handler for all FSM states."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu

router = Router()


@router.message(Command("cancel"))
async def cancel_handler(m: Message, state: FSMContext) -> None:
    """Handle /cancel command in any state."""
    current_state = await state.get_state()
    if current_state is None:
        await m.answer("Нечего отменять.", reply_markup=main_menu())
        return
    
    await state.clear()
    await m.answer("Операция отменена.", reply_markup=main_menu())
