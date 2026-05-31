import os
import math
from PIL import Image, ImageDraw, ImageFont

_FONT_CACHE: dict = {}
_TIMES_NEW_ROMAN_PATHS = [
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/Times New Roman.ttf",
]

# загрузка шрифта 
def _get_font(font_size: int) -> ImageFont.FreeTypeFont:
    if font_size in _FONT_CACHE:
        return _FONT_CACHE[font_size]

    for path in _TIMES_NEW_ROMAN_PATHS:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                _FONT_CACHE[font_size] = font
                return font
            except Exception:
                continue

    try:
        font = ImageFont.load_default(size=font_size)
    except TypeError:
        font = ImageFont.load_default()

    _FONT_CACHE[font_size] = font
    return font

# создание слоя знака для изображения
def _make_watermark_layer(width: int, height: int, text: str, font_size: int) -> Image.Image:
    SCALE = 2
    font = _get_font(font_size * SCALE)
    diagonal = (int(math.sqrt(width ** 2 + height ** 2)) + font_size * 2) * SCALE
    layer = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    step_x = text_w + font_size * SCALE * 2
    step_y = text_h + font_size * SCALE * 2

    for y in range(0, diagonal, step_y):
        for x in range(0, diagonal, step_x):
            draw.text((x + SCALE, y + SCALE), text, font=font, fill=(0, 0, 0, 50))
            draw.text((x, y), text, font=font, fill=(128, 128, 128, 102))

    rotated = layer.rotate(30, expand=True, resample=Image.BICUBIC)

    rot_w, rot_h = rotated.size
    rotated = rotated.resize((rot_w // SCALE, rot_h // SCALE), Image.LANCZOS)
    rw, rh = rotated.size
    left = (rw - width) // 2
    top = (rh - height) // 2
    return rotated.crop((left, top, left + width, top + height))

# наложение знака на изображение
def add_watermark_image(input_path: str, output_path: str, text: str) -> bool:
    try:
        image = Image.open(input_path)
        original_mode = image.mode 
        width, height = image.size
        font_size = max(20, min(width, height) // 15)
        wm_layer = _make_watermark_layer(width, height, text, font_size)

        if image.mode != 'RGBA':
            image.paste(wm_layer, (0, 0), mask=wm_layer.split()[3])
            result = image
        else:
            result = Image.alpha_composite(image, wm_layer)

        ext = os.path.splitext(output_path)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            if result.mode in ('RGBA', 'LA', 'P'):
                result = result.convert('RGB')
            result.save(output_path, quality=95, subsampling=0)
        elif ext == '.png':
            result.save(output_path, compress_level=1)
        else:
            result.save(output_path)
        print(f'[watermark] Готово: {output_path}')
        return True

    except Exception as e:
        print(f'[watermark] Ошибка при обработке изображения: {e}')
        import traceback
        traceback.print_exc()
        return False

# проверка целостности
def check_watermark_image(filepath: str, watermark_text: str) -> bool:
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True
    except Exception:
        return False