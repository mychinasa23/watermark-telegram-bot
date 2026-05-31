import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import supported_formats, max_file_size, temp_dir
from database import get_document, get_document_by_uuid
from services import check_watermark_pdf, check_watermark_docx, check_watermark_image
from .start import get_main_menu
from utils import cleanup_files
import re

router = Router()

class VerifyStates(StatesGroup):
    waiting_for_file = State()

@router.callback_query(lambda c: c.data == 'menu_verify')
async def start_verify(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VerifyStates.waiting_for_file)
    await callback.message.answer(
        '🔍 <b>Проверка водяного знака</b>\n\n'
        'Отправьте файл или фото — проверю наличие водяного знака.',
        parse_mode='HTML',
    )
    await callback.answer()


@router.message(VerifyStates.waiting_for_file, F.document)
async def verify_file(message: Message, state: FSMContext):
    doc = message.document

    if doc.file_size > max_file_size:
        await message.answer('❌ Файл слишком большой.', reply_markup=get_main_menu())
        await state.clear()
        return

    ext = doc.file_name.rsplit('.', 1)[-1].lower()
    if ext not in supported_formats:
        await message.answer(f'❌ Формат .{ext} не поддерживается.', reply_markup=get_main_menu())
        await state.clear()
        return

    file_path = os.path.join(temp_dir, f'verify_{message.from_user.id}_{doc.file_name}')
    await message.bot.download(doc, destination=file_path)
    await _run_verify(message, state, doc.file_name, ext, file_path)

@router.message(VerifyStates.waiting_for_file, F.photo)
async def verify_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_name = f'photo_{photo.file_unique_id}.jpg'
    file_path = os.path.join(temp_dir, f'verify_{message.from_user.id}_{file_name}')
    await message.bot.download(photo, destination=file_path)
    await _run_verify(message, state, file_name, 'jpg', file_path)

async def _run_verify(
    message: Message,
    state: FSMContext,
    file_name: str,
    ext: str,
    file_path: str,
):
    await message.answer('⏳ Проверяю файл...')

    record = await get_document(message.from_user.id, file_name)
    if not record:
        record = await get_document(message.from_user.id, f'wm_{file_name}')

    if not record:
        await message.answer(
            '❌ <b>Файл не найден в базе данных.</b>\n\n'
            'Этот файл не проходил обработку в данной системе.',
            parse_mode='HTML',
            reply_markup=get_main_menu(),
        )
        cleanup_files(file_path)
        await state.clear()
        return
    watermark_text = record[5]
    found = False

    try:
        if ext == 'pdf':
            found = check_watermark_pdf(file_path, watermark_text)
        elif ext == 'docx':
            from services.wm_docx import check_watermark_docx
            result = check_watermark_docx(file_path, watermark_text)
            found = result.get('watermark_found', False)
        else:
            found = check_watermark_image(file_path, watermark_text)
    except Exception as e:
        await message.answer(f'❌ Ошибка при проверке: {str(e)}')
        cleanup_files(file_path)
        await state.clear()
        return

    if found:
        await message.answer(
            f'✅ <b>Водяной знак найден!</b>\n\n'
            f'Текст метки: <i>{watermark_text}</i>',
            parse_mode='HTML',
            reply_markup=get_main_menu(),
        )
    else:
        await message.answer(
            '⚠️ <b>Водяной знак не обнаружен.</b>\n\n'
            'Файл есть в базе данных, но метка отсутствует в содержимом.',
            parse_mode='HTML',
            reply_markup=get_main_menu(),
        )
    cleanup_files(file_path)
    await state.clear()