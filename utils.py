import hashlib
import logging
import os

logger = logging.getLogger(__name__)

# вычисление хэша файла
def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lstrip('.').lower()

def cleanup_files(*paths: str) -> None:
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError as e:
            logger.warning('Не удалось удалить временный файл %s: %s', path, e)