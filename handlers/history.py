from aiogram import Router
from aiogram.types import CallbackQuery
from config import history_limit
from database import get_user_documents
from .start import get_main_menu

router = Router()

STATUS_ICONS = {
    'watermarked': '💧',
    'verified': '🔍',
    'error': '❌',
}

@router.callback_query(lambda c: c.data == 'menu_history')
async def show_history(callback: CallbackQuery):
    records = await get_user_documents(callback.from_user.id, limit=history_limit)

    if not records:
        await callback.message.answer(
            '📋 <b>История документов</b>\n\n'
            'У вас пока нет обработанных документов.\n'
            'Воспользуйтесь кнопкой «Добавить водяной знак».',
            parse_mode='HTML',
            reply_markup=get_main_menu(),
        )
        await callback.answer()
        return

    lines = [f'📋 <b>Последние {len(records)} документов:</b>\n']
    for i, (filename, fmt, date, wm_text, status) in enumerate(records, start=1):
        icon = STATUS_ICONS.get(status, '📄')
        short_date = date[:10] if date else '—'
        lines.append(
            f'{i}. {icon} <b>{filename}</b>\n'
            f'Формат: {fmt.upper()} | Дата: {short_date}\n'
            f'Метка: <i>{wm_text}</i>\n'
        )

    await callback.message.answer(
        '\n'.join(lines),
        parse_mode='HTML',
        reply_markup=get_main_menu(),
    )
    await callback.answer()