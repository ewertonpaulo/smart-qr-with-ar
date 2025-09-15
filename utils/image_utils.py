import colorsys
from pathlib import Path
from random import randint

from PIL import Image, ImageOps, ImageChops
from .qr_utils import generate_qr_image
from .utils import ensure_unique_filename, SAVED_DIR
from qrcode.constants import ERROR_CORRECT_M

# ==============================================================================
# New Main Function (with updated color logic)
# ==============================================================================

def add_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str = "bottom-right",
        size: float = 0.20,
        margin: float = 0.02,
        noise_amount: float = 0.12,
        opacity: float = 0.80,
        bg_opacity: float = 0.50,
        color_contrast_amount: float = 0.15,
        min_contrast: float = 2.5,
) -> Path:
    """
    Adds a stylized QR code watermark to an image using dominant colors from the patch.
    """
    base_image = Image.open(base_image_path).convert("RGBA")
    base_width, base_height = base_image.size

    # --- 1. Calculate QR code dimensions and position ---
    qr_side_px = int(round(base_width * size))
    margin_px = int(round(min(base_width, base_height) * margin))

    if corner == "bottom-right":
        x, y = base_width - qr_side_px - margin_px, base_height - qr_side_px - margin_px
    elif corner == "bottom-left":
        x, y = margin_px, base_height - qr_side_px - margin_px
    elif corner == "top-right":
        x, y = base_width - qr_side_px - margin_px, margin_px
    else: # top-left
        x, y = margin_px, margin_px

    # --- 2. Extract the patch from the image ---
    patch = base_image.crop((x, y, x + qr_side_px, y + qr_side_px))

    # --- 3. Use dominant colors and adjust them gently ---
    dominant_colors = _find_dominant_colors(patch, k=2)
    color1, color2 = dominant_colors[0], dominant_colors[1]

    # Define the darker color for modules and the lighter one for the background
    lum1 = _get_relative_luminance(color1)
    lum2 = _get_relative_luminance(color2)

    if lum1 < lum2:
        module_color_rgb, background_color_rgb = color1, color2
    else:
        module_color_rgb, background_color_rgb = color2, color1

    # Instead of creating an artificial color, we gently adjust the background color
    # just enough to achieve the minimum contrast.
    background_color_rgb = _ensure_min_contrast(
        fg_rgb=module_color_rgb,
        bg_rgb=background_color_rgb,
        min_ratio=min_contrast
    )

    # --- 4. Generate the base QR code image ---
    qr_img_binary = generate_qr_image(qr_content, border=0, error_correction=ERROR_CORRECT_M)
    qr_resized = qr_img_binary.resize((qr_side_px, qr_side_px), resample=Image.Resampling.NEAREST)

    # --- 5. Create the stylized background layer ---
    bg_alpha = int(max(0.0, min(1.0, bg_opacity)) * 255)
    bg_layer = Image.new("RGBA", (qr_side_px, qr_side_px), (*background_color_rgb, bg_alpha))
    final_qr_area = Image.alpha_composite(patch, bg_layer)

    # --- 6. Create the QR module layer with noise and texture ---
    module_color_base = Image.new("RGB", (qr_side_px, qr_side_px), module_color_rgb)
    gain_map = _make_gain_map((qr_side_px, qr_side_px), amount=noise_amount)
    gain_map_rgb = Image.merge("RGB", (gain_map, gain_map, gain_map))
    modules_with_luminance_noise = ImageChops.multiply(module_color_base, gain_map_rgb)
    noise_mask = _create_noise_image((qr_side_px, qr_side_px)).convert("L")
    mix_strength = max(0.0, min(1.0, color_contrast_amount))
    mix_mask = noise_mask.point(lambda v: int(v * mix_strength))
    mix_mask = ImageOps.invert(mix_mask)
    bg_tint_layer = Image.new("RGB", (qr_side_px, qr_side_px), background_color_rgb)
    modules_with_full_noise = Image.composite(modules_with_luminance_noise, bg_tint_layer, mix_mask)
    final_module_layer = modules_with_full_noise.convert("RGBA")

    # --- 7. Assemble the final QR code ---
    qr_pattern_mask = ImageOps.invert(qr_resized.convert("L"))
    module_alpha = max(0.0, min(1.0, opacity))
    final_mask = qr_pattern_mask.point(lambda p: int(p * module_alpha))
    final_qr_area.paste(final_module_layer, (0, 0), mask=final_mask)

    # --- 8. Composite the finished QR code back onto the base image ---
    base_image.alpha_composite(final_qr_area, dest=(x, y))
    output_path = ensure_unique_filename(SAVED_DIR / f"{base_image_path.stem}_watermarked.png")
    base_image.convert("RGB").save(output_path, "PNG")
    return output_path

# ==============================================================================
# Helper Functions
# ==============================================================================

def _find_dominant_colors(img: Image.Image, k: int) -> list[tuple[int, int, int]]:
    """
    Finds the 'k' most dominant colors in an image using palette quantization.
    """
    # Reducing image size improves performance without losing color information
    sm_img = img.convert("RGB").resize((128, 128), Image.Resampling.BOX)
    # Quantize the image to 'k' colors. The algorithm finds the best representative colors.
    result = sm_img.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    palette = result.getpalette()

    # Extract the 'k' colors from the palette
    colors = []
    for i in range(k):
        r, g, b = palette[i * 3:i * 3 + 3]
        colors.append((r, g, b))
    return colors

def _create_noise_image(size: tuple[int, int]) -> Image.Image:
    w, h = size
    try:
        return Image.effect_noise((w, h), 64.0)
    except Exception:
        noise = Image.new("L", (w, h))
        noise.putdata([randint(0, 255) for _ in range(w * h)])
        return noise

def _make_gain_map(size: tuple[int, int], amount: float = 0.10) -> Image.Image:
    noise = _create_noise_image(size)
    table = []
    for v in range(256):
        factor = 1.0 + amount * ((v - 128) / 128.0)
        factor = max(0.0, min(2.0, factor))
        table.append(int(round(factor * 255)))
    return noise.point(table, mode="L")

def _get_relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = [v / 255.0 for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _get_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    l1 = _get_relative_luminance(rgb1)
    l2 = _get_relative_luminance(rgb2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def _tune_color_brightness(rgb: tuple[int, int, int], new_v: float) -> tuple[int, int, int]:
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
    v = max(0.0, min(1.0, new_v))
    r, g, b = [int(round(x * 255)) for x in colorsys.hsv_to_rgb(h, s, v)]
    return (r, g, b)

def _ensure_min_contrast(
        fg_rgb: tuple[int, int, int],
        bg_rgb: tuple[int, int, int],
        min_ratio: float = 3.0,
        max_steps: int = 12
) -> tuple[int, int, int]:
    if _get_contrast_ratio(fg_rgb, bg_rgb) >= min_ratio:
        return bg_rgb

    fg_lum = _get_relative_luminance(fg_rgb)
    bg_lum = _get_relative_luminance(bg_rgb)
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in bg_rgb))
    make_bg_darker = bg_lum < fg_lum

    for i in range(1, max_steps + 1):
        step_size = 0.06 + 0.02 * i
        if make_bg_darker:
            new_v = v * (1.0 - step_size)
        else:
            new_v = v + (1.0 - v) * step_size
        candidate_bg = _tune_color_brightness(bg_rgb, new_v)
        if _get_contrast_ratio(fg_rgb, candidate_bg) >= min_ratio:
            return candidate_bg
        v = new_v
    return _tune_color_brightness(bg_rgb, v)