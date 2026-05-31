import aiosqlite
from config import db_path

# БД 
async def init_db() -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id INTEGER PRIMARY KEY, "
            "username TEXT, "
            "registered TEXT DEFAULT (datetime('now'))"
            ")"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS documents ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id INTEGER, "
            "filename TEXT, "
            "file_format TEXT, "
            "upload_date TEXT DEFAULT (datetime('now')), "
            "watermark_text TEXT, "
            "sha256_hash TEXT, "
            "status TEXT, "
            "doc_uuid EXT UNIQUE"
            ")"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_user_file "
            "ON documents (user_id, filename)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_uuid "
            "ON documents (doc_uuid)"
        )
        await db.commit()

async def add_user(user_id: int, username: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        await db.commit()

async def save_document(
    user_id: int,
    filename: str,
    file_format: str,
    watermark_text: str,
    sha256_hash: str,
    status: str,
    doc_uuid: str,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO documents "
            "(user_id, filename, file_format, watermark_text, sha256_hash, status, doc_uuid) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, filename, file_format, watermark_text, sha256_hash, status, doc_uuid),
        )
        await db.commit()

async def get_document(user_id: int, filename: str):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT * FROM documents "
            "WHERE user_id = ? AND filename = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id, filename),
        ) as cursor:
            return await cursor.fetchone()

async def get_document_by_uuid(doc_uuid: str):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT user_id, filename, watermark_text, sha256_hash FROM documents "
            "WHERE doc_uuid = ?",
            (doc_uuid,),
        ) as cursor:
            return await cursor.fetchone()

async def get_user_documents(user_id: int, limit: int = 10) -> list:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT filename, file_format, upload_date, watermark_text, status "
            "FROM documents "
            "WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            return await cursor.fetchall()