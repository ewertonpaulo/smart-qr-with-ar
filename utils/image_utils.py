import colorsys
from pathlib import Path

from PIL import Image, ImageOps
from .qr_utils import generate_qr_image
from .utils import ensure_unique_filename, SAVED_DIR
from qrcode.constants import ERROR_CORRECT_M

def add_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str = "bottom-right",
        size: float = 0.15,
        margin: float = 0.02,
        opacity: float = 0.80,
        bg_opacity: float = 0.40,
        min_contrast: float = 2.3,
) -> Path:
    """
    Adds a stylized QR code watermark with solid colors to an image,
    using dominant colors from the patch.
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

    # --- 3. Use dominant colors and adjust them ---
    dominant_colors = _find_dominant_colors(patch, k=2)
    color1, color2 = dominant_colors[0], dominant_colors[1]

    lum1 = _get_relative_luminance(color1)
    lum2 = _get_relative_luminance(color2)

    if lum1 < lum2:
        module_color_rgb, background_color_rgb = color1, color2
    else:
        module_color_rgb, background_color_rgb = color2, color1

    background_color_rgb = _ensure_min_contrast(
        fg_rgb=module_color_rgb,
        bg_rgb=background_color_rgb,
        min_ratio=min_contrast
    )

    # --- 4. Generate the QR code image itself ---
    qr_img_binary = generate_qr_image(qr_content, border=0, error_correction=ERROR_CORRECT_M)
    qr_resized = qr_img_binary.resize((qr_side_px, qr_side_px), resample=Image.Resampling.NEAREST)

    # --- 5. Create the background and module layers ---
    # Create a semi-transparent background layer
    bg_alpha = int(max(0.0, min(1.0, bg_opacity)) * 255)
    bg_layer = Image.new("RGBA", (qr_side_px, qr_side_px), (*background_color_rgb, bg_alpha))
    final_qr_area = Image.alpha_composite(patch, bg_layer)

    final_module_layer = Image.new("RGBA", (qr_side_px, qr_side_px), module_color_rgb)

    # --- 6. Combine layers to form the final watermark ---
    qr_pattern_mask = ImageOps.invert(qr_resized.convert("L"))
    module_alpha = max(0.0, min(1.0, opacity))
    final_mask = qr_pattern_mask.point(lambda p: int(p * module_alpha))
    final_qr_area.paste(final_module_layer, (0, 0), mask=final_mask)

    # --- 7. Apply watermark and save the final image ---
    base_image.alpha_composite(final_qr_area, dest=(x, y))
    output_path = ensure_unique_filename(SAVED_DIR / f"{base_image_path.stem}_watermarked.png")
    base_image.convert("RGB").save(output_path, "PNG")
    return output_path

def _find_dominant_colors(img: Image.Image, k: int) -> list[tuple[int, int, int]]:
    """
    Finds the 'k' most dominant colors in an image using palette quantization.
    """
    # Reduce image size and improves performance without losing color info
    sm_img = img.convert("RGB").resize((128, 128), Image.Resampling.BOX)
    # Find the best representative colors
    result = sm_img.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    palette = result.getpalette()

    # Extract the best colors from k
    colors = []
    for i in range(k):
        r, g, b = palette[i * 3:i * 3 + 3]
        colors.append((r, g, b))
    return colors

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
        min_ratio: float = 2.8,
        max_steps: int = 12
) -> tuple[int, int, int]:
    if _get_contrast_ratio(fg_rgb, bg_rgb) >= min_ratio:
        return bg_rgb

    fg_lum = _get_relative_luminance(fg_rgb)
    bg_lum = _get_relative_luminance(bg_rgb)
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in bg_rgb))

    # If the background is darker than the module, make it even darker. Otherwise, lighten it.
    make_bg_darker = bg_lum < fg_lum

    for i in range(1, max_steps + 1):
        # Increase the step size with each iteration to converge faster
        step_size = 0.06 + 0.02 * i
        if make_bg_darker:
            new_v = v * (1.0 - step_size)
        else:
            new_v = v + (1.0 - v) * step_size

        candidate_bg = _tune_color_brightness(bg_rgb, new_v)

        if _get_contrast_ratio(fg_rgb, candidate_bg) >= min_ratio:
            return candidate_bg

        v = new_v

    # Return the last calculated color if the ideal contrast isn't met
    return _tune_color_brightness(bg_rgb, v)