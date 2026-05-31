import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import supported_formats, max_file_size, temp_dir
from database import get_document
from .start import get_main_menu
from utils import compute_sha256, cleanup_files

router = Router()

class IntegrityStates(StatesGroup):
    waiting_for_file = State()

@router.callback_query(lambda c: c.data == 'menu_integrity')
async def start_integrity(callback: CallbackQuery, state: FSMContext):
    await state.set_state(IntegrityStates.waiting_for_file)
    await callback.message.answer(
        '🔒 <b>Контроль целостности</b>\n\n'
        'Отправьте файл или фото.\n'
        'Бот сравнит SHA-256 хэш с тем, что был сохранён при обработке.',
        parse_mode='HTML',
    )
    await callback.answer()

@router.message(IntegrityStates.waiting_for_file, F.document)
async def check_integrity_doc(message: Message, state: FSMContext):
    doc = message.document

    if doc.file_size > max_file_size:
        await message.answer('❌ Файл слишком большой.', reply_markup=get_main_menu())
        await state.clear()
        return

    ext = doc.file_name.rsplit('.', 1)[-1].lower()
    if ext not in supported_formats:
        await message.answer(f'❌ Формат .{ext} не поддерживается. Поддерживаются: PDF, DOCX, PNG, JPG, JPEG.', reply_markup=get_main_menu())
        await state.clear()
        return

    file_path = os.path.join(temp_dir, f'integrity_{message.from_user.id}_{doc.file_name}')
    await message.bot.download(doc, destination=file_path)
    await _run_integrity(message, state, doc.file_name, file_path)

@router.message(IntegrityStates.waiting_for_file, F.photo)
async def check_integrity_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_name = f'photo_{photo.file_unique_id}.jpg'
    file_path = os.path.join(temp_dir, f'integrity_{message.from_user.id}_{file_name}')
    await message.bot.download(photo, destination=file_path)
    await _run_integrity(message, state, file_name, file_path)

async def _run_integrity(
    message: Message,
    state: FSMContext,
    file_name: str,
    file_path: str,
):
    await message.answer('⏳ Вычисляю SHA-256 хэш файла...')
    current_hash = compute_sha256(file_path)

    record = await get_document(message.from_user.id, file_name)
    if not record:
        record = await get_document(message.from_user.id, f'wm_{file_name}')

    if not record:
        await message.answer(
            '❌ <b>Файл не найден в базе данных.</b>\n\n'
            'Он не проходил обработку в данной системе — сравнение невозможно.',
            parse_mode='HTML',
            reply_markup=get_main_menu(),
        )
    else:
        saved_hash = record[6]  # sha256_hash
        if current_hash == saved_hash:
            await message.answer(
                '✅ <b>Целостность подтверждена!</b>\n\n'
                f'SHA-256: <code>{current_hash}</code>\n\n'
                'Файл не изменялся после нанесения водяного знака.',
                parse_mode='HTML',
                reply_markup=get_main_menu(),
            )
        else:
            await message.answer(
                '⚠️ <b>Целостность нарушена!</b>\n\n'
                f'Текущий хэш: <code>{current_hash}</code>\n'
                f'Сохранённый хэш: <code>{saved_hash}</code>\n\n'
                'Файл был изменён после нанесения водяного знака.',
                parse_mode='HTML',
                reply_markup=get_main_menu(),
            )
    cleanup_files(file_path)
    await state.clear()