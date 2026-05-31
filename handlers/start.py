from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import add_user

router = Router()

# меню
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text='💧 Добавить водяной знак', callback_data='menu_watermark')
    builder.button(text='🔍 Проверить документ', callback_data='menu_verify')
    builder.button(text='🔒 Контроль целостности', callback_data='menu_integrity')
    builder.button(text='📋 Мои документы', callback_data='menu_history')
    builder.button(text='❓ Справка', callback_data='menu_help')
    builder.adjust(1)
    return builder.as_markup()

# /start 
@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.first_name,
    )
    await message.answer(
        f'👋 Привет, {message.from_user.first_name}!\n\n'
        'Я бот для защиты документов с помощью цифровых водяных знаков.\n\n'
        '<b>Что умею:</b>\n'
        '💧 Наносить водяной знак на PDF, DOCX, PNG, JPG, JPEG\n'
        '🔍 Проверять наличие водяного знака в документе\n'
        '🔒 Контролировать целостность файла по SHA-256 хэшу\n'
        '📋 Показывать историю обработанных документов\n\n'
        'Выберите действие:',
        parse_mode='HTML',
        reply_markup=get_main_menu(),
    )

# /help (справка)
@router.message(Command('help'))
@router.callback_query(lambda c: c.data == 'menu_help')
async def show_help(event: Message | CallbackQuery):
    text = (
        '📖 <b>Помощь и инструкция</b>\n\n'
        '━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        '💧 <b>Добавить водяной знак</b>\n'
        '├ Отправьте файл (PDF, DOCX, PNG, JPG, JPEG)\n'
        '├ Введите текст метки (до 50 символов)\n'
        '└ Получите защищённый файл ⬇️\n\n'
        
        '🔍 <b>Проверить документ</b>\n'
        '├ Отправьте файл\n'
        '└ Бот проверит наличие водяного знака ✅\n\n'
        
        '🔒 <b>Контроль целостности</b>\n'
        '├ Отправьте файл\n'
        '└ Бот сравнит SHA-256 хэш с оригиналом 🔐\n\n'
        
        '📋 <b>Мои документы</b>\n'
        '└ Показывает последние 10 обработанных файлов 📜\n\n'
        
        '━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        '📁 <b>Поддерживаемые форматы:</b>\n'
        '│  📄 PDF   │  📘 DOCX   │  🖼️ PNG   │  🖼️ JPG/JPEG\n\n'
        
        '⚡ <b>Ограничения:</b>\n'
        '│  📦 Макс. размер файла: 20 МБ\n'
        '│  📝 Макс. длина метки: 50 символов\n'
        '━━━━━━━━━━━━━━━━━━━━━━━━━━'
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode='HTML', reply_markup=get_main_menu())
        await event.answer()
    else:
        await event.answer(text, parse_mode='HTML', reply_markup=get_main_menu())