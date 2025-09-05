from pathlib import Path
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M
from utils import ensure_unique_filename, SAVED_DIR

def generate_qr_image(
        content: str,
        border: int = 4,
        error_correction=ERROR_CORRECT_M
) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=10,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def save_qr_code(content: str, filename: str) -> Path:
    img = generate_qr_image(content)
    output_path = ensure_unique_filename(SAVED_DIR / filename)
    img.save(output_path)
    return output_path