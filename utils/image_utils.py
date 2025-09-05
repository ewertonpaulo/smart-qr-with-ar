from pathlib import Path
from PIL import Image, ImageOps
from utils.qr_utils import generate_qr_image
from utils import ensure_unique_filename, SAVED_DIR

def add_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str,
        size: float,
        margin: float
) -> Path:
    base = Image.open(base_image_path).convert("RGBA")
    qr_img = generate_qr_image(qr_content, border=1).convert("RGBA")

    W, H = base.size

    side = int(round(W * size))
    margin_px = int(round(min(W, H) * margin))

    qr = qr_img.resize((side, side), resample=Image.LANCZOS)
    qr = ImageOps.expand(qr, border=int(side * 0.05), fill="white")

    bx, by = base.size
    qx, qy = qr.size

    valid_corners = {"top-left", "top-right", "bottom-left", "bottom-right"}
    if corner not in valid_corners:
        corner = "bottom-right"

    if corner == "bottom-right": pos = (bx - qx - margin_px, by - qy - margin_px)
    elif corner == "bottom-left": pos = (margin_px, by - qy - margin_px)
    elif corner == "top-right": pos = (bx - qx - margin_px, margin_px)
    else: pos = (margin_px, margin_px)

    base.alpha_composite(qr, dest=pos)

    out_name = f"{base_image_path.stem}_watermarked.png"
    output_path = ensure_unique_filename(SAVED_DIR / out_name)
    base.convert("RGB").save(output_path, format="PNG")
    return output_path