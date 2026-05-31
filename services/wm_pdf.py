import io
import math
import os
import traceback
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, EncodedStreamObject, NameObject

_FONT_NAME: str | None = None
_TIMES_NEW_ROMAN_PATHS = [
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/Times New Roman.ttf",
]

# загрузка шрифта 
def _get_font_name() -> str:
    global _FONT_NAME
    if _FONT_NAME is not None:
        return _FONT_NAME

    for path in _TIMES_NEW_ROMAN_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("TimesNewRoman", path))
                _FONT_NAME = "TimesNewRoman"
                print(f"[watermark] Шрифт загружен: {path}")
                return _FONT_NAME
            except Exception as e:
                print(f"[watermark] Не удалось загрузить {path}: {e}")

    print("[watermark] Times New Roman не найден в C:/Windows/Fonts, используется Helvetica")
    _FONT_NAME = "Helvetica"
    return _FONT_NAME

# декодирование сжатых страниц pdf 
def _decode_page_contents(page) -> None:
    contents = page.get("/Contents")
    if contents is None:
        return

    obj = contents.get_object()
    if not isinstance(obj, EncodedStreamObject):
        return 
    
    decoded = DecodedStreamObject()
    decoded.set_data(obj.get_data())

    skip_keys = {NameObject("/Filter"), NameObject("/DecodeParms")}
    for key, val in obj.items():
        if NameObject(str(key)) not in skip_keys:
            decoded[NameObject(str(key))] = val
    page[NameObject("/Contents")] = decoded

# создание страницы подложки с водяным знаком
def _make_watermark_page(text: str, width: float, height: float):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))
    font_name = _get_font_name()
    font_size = min(48, max(24, int(width / 10)))
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.4)
    text_width = c.stringWidth(text, font_name, font_size)
    step_x = text_width + font_size * 1.5
    step_y = font_size * 2.5
    diagonal = int(math.sqrt(width ** 2 + height ** 2))
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)
    y = -diagonal
    while y < diagonal:
        x = -diagonal
        while x < diagonal:
            c.drawString(x, y, text)
            x += step_x
        y += step_y
    c.restoreState()
    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

# наложение знака на pdf
def add_watermark_pdf(input_path: str, output_path: str, text: str) -> bool:
    try:
        original_pdf = PdfReader(input_path)
        total = len(original_pdf.pages)
        print(f"[watermark] Всего страниц: {total}")
        writer = PdfWriter()

        for page_num, page in enumerate(original_pdf.pages):
            try:
                w = float(page.mediabox.width)
                h = float(page.mediabox.height)
                rotation = int(page.get("/Rotate") or 0) % 360
                if rotation in (90, 270):
                    w, h = h, w

                _decode_page_contents(page)
                wm_page = _make_watermark_page(text, w, h)
                page.merge_page(wm_page)
                writer.add_page(page)
                print(f"[watermark] Страница {page_num + 1}/{total}: "
                      f"{w:.0f}x{h:.0f} pt, поворот {rotation}°")

            except Exception as page_err:
                print(f"[watermark] ОШИБКА на странице {page_num + 1}: {page_err}")
                traceback.print_exc()
                writer.add_page(page)

        with open(output_path, "wb") as out_file:
            writer.write(out_file)

        print(f"[watermark] Готово: {output_path}")
        return True

    except Exception as e:
        print(f"[watermark] Критическая ошибка: {e}")
        traceback.print_exc()
        return False

# проверка наличия знака в pdf
def check_watermark_pdf(filepath: str, watermark_text: str) -> bool:
    try:
        reader = PdfReader(filepath)
        search = watermark_text.lower()

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if search in text.lower():
                print(f"[check] Водяной знак найден на странице {page_num + 1}")
                return True

        if reader.metadata:
            if search in str(reader.metadata).lower():
                print("[check] Водяной знак найден в метаданных")
                return True

        print("[check] Водяной знак не найден")
        return False

    except Exception as e:
        print(f"[check] Ошибка при проверке PDF: {e}")
        traceback.print_exc()
        return False