import os
import secrets
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import supported_formats, max_file_size, temp_dir, max_wm_length
from database import save_document
from services import add_watermark_image, add_watermark_docx, add_watermark_pdf
from .start import get_main_menu
from utils import compute_sha256, cleanup_files

router = Router()

class WatermarkStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_text = State()

# запуск проуесса добавления знака
@router.callback_query(lambda c: c.data == 'menu_watermark')
async def start_watermark(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WatermarkStates.waiting_for_file)
    await callback.message.answer(
        '💧 <b>Добавление водяного знака</b>\n\n'
        'Отправьте файл (PDF, DOCX, PNG, JPG, JPEG) или фотографию.\n'
        f'Максимальный размер: 20 МБ.',
        parse_mode='HTML',
    )
    await callback.answer()

# обработка загруженного файла
@router.message(WatermarkStates.waiting_for_file, F.document)
async def receive_file(message: Message, state: FSMContext):
    doc = message.document

    if doc.file_size > max_file_size:
        await message.answer('❌ Файл слишком большой. Максимум 20 МБ.', reply_markup=get_main_menu())
        await state.clear()
        return

    ext = doc.file_name.rsplit('.', 1)[-1].lower()
    if ext not in supported_formats:
        await message.answer(
            f'❌ Формат .{ext} не поддерживается.\n'
            f'Поддерживаются: PDF, DOCX, PNG, JPG, JPEG.',
            reply_markup=get_main_menu(),
        )
        await state.clear()
        return

    file_path = os.path.join(temp_dir, f'{message.from_user.id}_{doc.file_name}')
    await message.bot.download(doc, destination=file_path)
    await state.update_data(
        file_path=file_path, 
        file_name=doc.file_name, 
        file_ext=ext,
        original_name=doc.file_name
    )
    await state.set_state(WatermarkStates.waiting_for_text)
    await message.answer(
        f'✅ Файл получен!\n\n'
        f'Введите текст водяного знака (не более {max_wm_length} символов).\n'
        f'Например: <i>Конфиденциально</i> или ваше имя.',
        parse_mode='HTML',
    )

@router.message(WatermarkStates.waiting_for_file, F.photo)
async def receive_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]

    if photo.file_size > max_file_size:
        await message.answer('❌ Фото слишком большое. Максимум 20 МБ.', reply_markup=get_main_menu())
        await state.clear()
        return

    file_name = f'photo_{photo.file_unique_id}.jpg'
    file_path = os.path.join(temp_dir, f'{message.from_user.id}_{file_name}')
    await message.bot.download(photo, destination=file_path)
    await state.update_data(
        file_path=file_path, 
        file_name=file_name, 
        file_ext='jpg',
        original_name=file_name
    )
    await state.set_state(WatermarkStates.waiting_for_text)
    await message.answer(
        f'✅ Фото получено!\n\n'
        f'Введите текст водяного знака (не более {max_wm_length} символов).'
    )

# обработка текста для знака и создание защищённого файла
@router.message(WatermarkStates.waiting_for_text, F.text)
async def receive_watermark_text(message: Message, state: FSMContext):
    watermark_text = message.text.strip()

    if not watermark_text:
        await message.answer('❌ Текст не может быть пустым. Попробуйте ещё раз.')
        return
    if len(watermark_text) > max_wm_length:
        await message.answer(
            f'❌ Слишком длинный текст ({len(watermark_text)} сим.). Максимум — {max_wm_length}.'
        )
        return

    data = await state.get_data()
    file_path: str = data['file_path']
    file_name: str = data['file_name']
    file_ext: str = data['file_ext']
    original_name: str = data.get('original_name', file_name)
    output_name = f'wm_{file_name}'
    output_path = os.path.join(temp_dir, f'{message.from_user.id}_{output_name}')

    await message.answer('⏳ Обрабатываю файл, подождите...')

    doc_uuid = secrets.token_hex(16) 
    
    if file_ext in ('png', 'jpg', 'jpeg'):
        success = add_watermark_image(file_path, output_path, watermark_text)
    elif file_ext == 'pdf':
        success = add_watermark_pdf(file_path, output_path, watermark_text)
    elif file_ext == 'docx':
        success = add_watermark_docx(file_path, output_path, watermark_text, doc_uuid)
    else:
        success = False

    if not success:
        await message.answer('❌ Что-то пошло не так. Попробуйте ещё раз.', reply_markup=get_main_menu())
        cleanup_files(file_path, output_path)
        await state.clear()
        return

    file_hash = compute_sha256(output_path)
    await save_document(
        user_id=message.from_user.id,
        filename=output_name,
        file_format=file_ext,
        watermark_text=watermark_text,
        sha256_hash=file_hash,
        status='watermarked',
        doc_uuid=doc_uuid,  # Сохраняем UUID в БД
    )

    masked_id = f"****{str(message.from_user.id)[-4:]}"

    await message.answer_document(
        FSInputFile(output_path, filename=output_name),
        caption=f'✅ Водяной знак <b>«{watermark_text}»</b> успешно добавлен!\n\n'
                f'🔒 <b>Документ защищён цифровой меткой</b>\n'
                f'👤 Владелец: {message.from_user.first_name}\n'
                f'🆔 ID: {masked_id}\n'
                f'📅 {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}',
        parse_mode='HTML',
    )
    await message.answer('Что хотите сделать дальше?', reply_markup=get_main_menu())
    cleanup_files(file_path, output_path)
    await state.clear()