from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops
from .qr_utils import generate_qr_image
from .utils import ensure_unique_filename, SAVED_DIR
from qrcode.constants import ERROR_CORRECT_H

def _adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)

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
    if corner not in valid_corners: corner = "bottom-right"
    if corner == "bottom-right": pos = (bx - qx - margin_px, by - qy - margin_px)
    elif corner == "bottom-left": pos = (margin_px, by - qy - margin_px)
    elif corner == "top-right": pos = (bx - qx - margin_px, margin_px)
    else: pos = (margin_px, margin_px)
    base.alpha_composite(qr, dest=pos)
    out_name = f"{base_image_path.stem}_watermarked.png"
    output_path = ensure_unique_filename(SAVED_DIR / out_name)
    base.convert("RGB").save(output_path, format="PNG")
    return output_path

def add_textured_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str,
        size: float,
        margin: float,
        emboss_strength: float = 0.6,
        emboss_offset: int = 2
) -> Path:
    base = Image.open(base_image_path).convert("RGBA")
    W, H = base.size

    side = int(round(W * size))
    margin_px = int(round(min(W, H) * margin))
    valid_corners = {"top-left", "top-right", "bottom-left", "bottom-right"}
    if corner not in valid_corners: corner = "bottom-right"
    if corner == "bottom-right": x, y = W - side - margin_px, H - side - margin_px
    elif corner == "bottom-left": x, y = margin_px, H - side - margin_px
    elif corner == "top-right": x, y = W - side - margin_px, margin_px
    else: x, y = margin_px, margin_px

    background_patch_original = base.crop((x, y, x + side, y + side)).convert("RGBA")
    darker_texture = _adjust_brightness(background_patch_original.convert("RGB"), 0.5).convert("RGBA")
    qr_img = generate_qr_image(qr_content, border=0, error_correction=ERROR_CORRECT_H)
    qr_resized = qr_img.resize((side, side), resample=Image.NEAREST)

    blurred_qr = qr_resized.filter(ImageFilter.BoxBlur(emboss_offset))

    shadow_mask = ImageChops.offset(blurred_qr, emboss_offset, emboss_offset)
    shadow_effect = _adjust_brightness(darker_texture, 1 - emboss_strength)

    light_mask = ImageChops.offset(blurred_qr, -emboss_offset, -emboss_offset)
    light_effect = _adjust_brightness(darker_texture, 1 + emboss_strength)

    final_qr_area = background_patch_original.copy()
    final_qr_area.paste(shadow_effect, (0,0), mask=ImageOps.invert(shadow_mask.convert('L')))
    final_qr_area.paste(light_effect, (0,0), mask=ImageOps.invert(light_mask.convert('L')))
    mask_modules = ImageOps.invert(qr_resized.convert('L'))
    final_qr_area.paste(darker_texture, (0, 0), mask=mask_modules)

    base.alpha_composite(final_qr_area, dest=(x, y))

    out_name = f"{base_image_path.stem}_textured_emboss_qr.png"
    output_path = ensure_unique_filename(SAVED_DIR / out_name)
    base.convert("RGB").save(output_path, format="PNG")
    return output_path