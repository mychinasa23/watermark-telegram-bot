import os
from dotenv import load_dotenv

load_dotenv()

bot_token: str = os.getenv('BOT_TOKEN', '')
if not bot_token:
    raise ValueError('BOT_TOKEN не задан — создайте .env файл и пропишите BOT_TOKEN=ваш_токен')

db_path: str = os.getenv('DB_PATH', 'bot_database.db')
temp_dir: str = os.getenv('TEMP_DIR', 'temp_files')
max_file_size: int = 20 * 1024 * 1024
max_wm_length: int = 50 
history_limit: int = 10 
supported_formats: list[str] = ['pdf', 'docx', 'png', 'jpg', 'jpeg']