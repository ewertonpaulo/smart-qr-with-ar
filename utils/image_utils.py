import colorsys
from pathlib import Path
from random import randint

from PIL import Image, ImageOps, ImageFilter, ImageChops, ImageDraw, ImageFont
from .qr_utils import generate_qr_image
from .utils import ensure_unique_filename, SAVED_DIR
from qrcode.constants import ERROR_CORRECT_M

def add_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str = "bottom-right",
        size: float = 0.20,
        margin: float = 0.02,
        tile_ratio: float = 0.22,
        noise_amount: float = 0.12,
        opacity: float = 0.80,
        bg_opacity: float = 0.40,
        color_contrast_amount: float = 0.15,
        min_contrast: float = 2.8,
) -> Path:
    """
    Adds a stylized QR code watermark to an image.

    The QR code is generated with colors extracted from the image itself to blend in
    visually, applying noise and textures for a more artistic finish while ensuring
    sufficient contrast for scannability.

    Args:
        base_image_path: The path to the base image.
        qr_content: The content to be encoded in the QR code (e.g., a URL).
        corner: The corner to position the QR code ('top-left', 'top-right', 'bottom-left', 'bottom-right').
        size: The width of the QR code as a fraction of the base image's width (e.g., 0.2 for 20%).
        margin: The margin from the image edges, as a fraction of the smaller dimension.
        tile_ratio: The fraction of the QR code area used to find a "texture" and extract colors.
        noise_amount: The intensity of luminance noise (grain) on the QR code modules.
        opacity: The opacity of the QR code modules (0.0 to 1.0).
        bg_opacity: The opacity of the QR code's background layer (0.0 to 1.0).
        color_contrast_amount: The intensity of chromatic noise (color mixing) on the modules.
        min_contrast: The minimum contrast ratio to be enforced between the QR code colors.

    Returns:
        The file path of the finalized and saved image.
    """
    base_image = Image.open(base_image_path).convert("RGBA")
    base_width, base_height = base_image.size

    # --- 1. Calculate QR code dimensions and position ---
    qr_side_px = int(round(base_width * size))
    margin_px = int(round(min(base_width, base_height) * margin))

    # Define the (x, y) coordinates of the top-left corner of the QR code
    if corner == "bottom-right":
        x, y = base_width - qr_side_px - margin_px, base_height - qr_side_px - margin_px
    elif corner == "bottom-left":
        x, y = margin_px, base_height - qr_side_px - margin_px
    elif corner == "top-right":
        x, y = base_width - qr_side_px - margin_px, margin_px
    else:  # Default to 'top-left'
        x, y = margin_px, margin_px

    # --- 2. Extract the patch from the image where the QR code will be placed ---
    patch = base_image.crop((x, y, x + qr_side_px, y + qr_side_px))

    # --- 3. Intelligently find colors from the image patch ---
    # Find a sub-region (tile) with high texture/contrast within the patch
    tile_px = max(16, int(qr_side_px * tile_ratio))
    texture_tile = _find_best_texture_tile(patch, tile_px)

    # Calculate the average luminance of the entire patch to help pick a contrasting color
    patch_avg_lum = _get_relative_luminance(ImageOps.fit(patch.convert("RGB"), (1, 1), Image.Resampling.BOX).getpixel((0, 0)))

    # Pick the color for the QR modules (from the tile) that most contrasts with the patch's average
    module_color_rgb = _pick_high_contrast_color(texture_tile, patch_avg_lum)

    # Pick a color for the QR background (from the patch) that contrasts with the module color
    background_color_rgb = _get_contrasting_color_from_patch(patch, module_color_rgb, tile=texture_tile)

    # Ensure the contrast between the two colors meets the scannability minimum
    background_color_rgb = _ensure_min_contrast(module_color_rgb, background_color_rgb, min_ratio=min_contrast)

    # --- 4. Generate the base QR code image ---
    qr_img_binary = generate_qr_image(qr_content, border=0, error_correction=ERROR_CORRECT_M)
    qr_resized = qr_img_binary.resize((qr_side_px, qr_side_px), resample=Image.Resampling.NEAREST)

    # --- 5. Create the stylized background layer ---
    # Create a solid color background with the defined opacity
    bg_alpha = int(max(0.0, min(1.0, bg_opacity)) * 255)
    bg_layer = Image.new("RGBA", (qr_side_px, qr_side_px), (*background_color_rgb, bg_alpha))

    # Composite the translucent background over the original image patch
    final_qr_area = Image.alpha_composite(patch, bg_layer)

    # --- 6. Create the QR module layer with noise and texture ---
    # a) Start with a solid color base for the modules
    module_color_base = Image.new("RGB", (qr_side_px, qr_side_px), module_color_rgb)

    # b) Add luminance noise (grain effect)
    gain_map = _make_gain_map((qr_side_px, qr_side_px), amount=noise_amount)
    gain_map_rgb = Image.merge("RGB", (gain_map, gain_map, gain_map))
    modules_with_luminance_noise = ImageChops.multiply(module_color_base, gain_map_rgb)

    # c) Add chromatic noise (sprinkles of the background color) for better blending
    # Create a noise mask to blend the colors
    noise_mask = _create_noise_image((qr_side_px, qr_side_px)).convert("L")
    mix_strength = max(0.0, min(1.0, color_contrast_amount))
    # The mask is weak and inverted, so the module color remains dominant
    mix_mask = noise_mask.point(lambda v: int(v * mix_strength))
    mix_mask = ImageOps.invert(mix_mask)

    # Create a layer with the background color to be "sprinkled" in
    bg_tint_layer = Image.new("RGB", (qr_side_px, qr_side_px), background_color_rgb)

    # Blend the grainy module color with the background color using the noise mask
    modules_with_full_noise = Image.composite(modules_with_luminance_noise, bg_tint_layer, mix_mask)

    # Convert to RGBA to apply the final opacity
    final_module_layer = modules_with_full_noise.convert("RGBA")

    # --- 7. Assemble the final QR code ---
    # Create a mask from the QR code pattern (white where modules should appear)
    qr_pattern_mask = ImageOps.invert(qr_resized.convert("L"))

    # Adjust the mask's opacity
    module_alpha = max(0.0, min(1.0, opacity))
    final_mask = qr_pattern_mask.point(lambda p: int(p * module_alpha))

    # "Paint" the textured modules onto the QR area, using the QR pattern as a mask
    final_qr_area.paste(final_module_layer, (0, 0), mask=final_mask)

    # --- 8. Composite the finished QR code back onto the base image ---
    base_image.alpha_composite(final_qr_area, dest=(x, y))

    # Save the final image
    output_path = ensure_unique_filename(SAVED_DIR / f"{base_image_path.stem}_watermarked.png")
    base_image.convert("RGB").save(output_path, "PNG")
    return output_path

# ==============================================================================
# Helper Functions (with documentation)
# ==============================================================================

def _create_noise_image(size: tuple[int, int]) -> Image.Image:
    """Generates a Gaussian or simple random noise image."""
    w, h = size
    try:
        # Try the faster, higher-quality method if available
        return Image.effect_noise((w, h), 64.0)
    except Exception:
        # Fallback to pixel-by-pixel noise if the above fails
        noise = Image.new("L", (w, h))
        noise.putdata([randint(0, 255) for _ in range(w * h)])
        return noise

def _make_gain_map(size: tuple[int, int], amount: float = 0.10) -> Image.Image:
    """
    Creates a multiplicative noise map to simulate film grain.

    Args:
        size: The (width, height) dimensions of the map.
        amount: The intensity of the noise (0.05–0.20 is a good range).

    Returns:
        A grayscale ('L') image where each pixel represents a gain factor.
    """
    noise = _create_noise_image(size)

    # Maps the noise [0..255] to a gain factor around 1.0.
    # E.g., for amount=0.1, the gain will vary from 0.9 to 1.1.
    # The result is rescaled to [0..255] to be applied via `ImageChops.multiply`.
    table = []
    for v in range(256):
        factor = 1.0 + amount * ((v - 128) / 128.0)
        factor = max(0.0, min(2.0, factor))  # Clamp extreme values
        table.append(int(round(factor * 255)))
    return noise.point(table, mode="L")

def _get_relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculates the relative luminance (perceived brightness) of an RGB color."""
    r, g, b = [v / 255.0 for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _get_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """Calculates the WCAG contrast ratio between two RGB colors."""
    l1 = _get_relative_luminance(rgb1)
    l2 = _get_relative_luminance(rgb2)
    if l1 < l2:
        l1, l2 = l2, l1  # Ensure l1 is the lighter color
    return (l1 + 0.05) / (l2 + 0.05)

def _find_best_texture_tile(patch: Image.Image, tile_px: int) -> Image.Image:
    """
    Finds a sub-region (tile) within an image patch that has the most
    "texture" (edges/details).
    """
    gray = patch.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)

    # Downsample the edge map to a grid to find the most intense cell
    w, h = edges.size
    grid_w, grid_h = max(1, w // tile_px), max(1, h // tile_px)
    agg = edges.resize((grid_w, grid_h), resample=Image.Resampling.BOX)

    # Find the index of the "brightest" cell (the one with the most edges)
    edge_data = list(agg.getdata())
    max_edge_index = edge_data.index(max(edge_data))

    # Convert the index back to coordinates and crop the tile from the original image
    cx, cy = max_edge_index % grid_w, max_edge_index // grid_w
    x0, y0 = min(w - tile_px, cx * tile_px), min(h - tile_px, cy * tile_px)
    return patch.crop((x0, y0, x0 + tile_px, y0 + tile_px))

def _get_contrasting_color_from_patch(
        patch: Image.Image,
        avoid_rgb: tuple[int, int, int],
        tile: Image.Image | None = None,
        sat_floor: float = 0.40,
) -> tuple[int, int, int]:
    """
    Scans an image area (patch or tile) to find the color that maximizes
    contrast against a color to be avoided (`avoid_rgb`).

    Args:
        patch: The larger image piece.
        avoid_rgb: The color to contrast against (usually the QR module color).
        tile: An optional high-texture sub-region to prioritize the search.
        sat_floor: Minimum saturation for the resulting color, to avoid grays.

    Returns:
        The found RGB color tuple.
    """
    src_image = tile if tile is not None else patch
    img_sample = src_image.resize((64, 64), Image.Resampling.BOX).convert("RGB")

    best_rgb, best_score = (0, 0, 0), -1.0
    for rgb in img_sample.getdata():
        cr = _get_contrast_ratio(rgb, avoid_rgb)
        # Bonus for saturation to prefer more vivid colors
        h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
        score = cr + 0.12 * s
        if score > best_score:
            best_rgb, best_score = rgb, score

    # Ensure a minimum saturation without altering brightness, to avoid "washed out" colors
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in best_rgb))
    s = max(s, sat_floor)
    r, g, b = [int(round(x * 255)) for x in colorsys.hsv_to_rgb(h, s, v)]
    return (r, g, b)

def _pick_high_contrast_color(tile: Image.Image, patch_avg_lum: float) -> tuple[int, int, int]:
    """
    Picks the color from the `tile` that differs most in brightness from the
    average luminance of the entire `patch`.
    """
    t = tile.resize((64, 64), Image.Resampling.BOX).convert("RGB")
    best_rgb, best_score = (0, 0, 0), -1.0
    for rgb in t.getdata():
        lum = _get_relative_luminance(rgb)
        score = abs(lum - patch_avg_lum)
        if score > best_score:
            best_rgb, best_score = rgb, score
    return best_rgb

def _tune_color_brightness(rgb: tuple[int, int, int], new_v: float) -> tuple[int, int, int]:
    """Adjusts a color's brightness (HSV Value), keeping Hue and Saturation."""
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
    """
    Adjusts the background color's (`bg_rgb`) brightness to ensure it has
    a minimum contrast with the foreground color (`fg_rgb`).

    If the background is darker than the foreground, it makes it even darker.
    If it's lighter, it makes it even lighter, preserving hue and saturation.
    """
    if _get_contrast_ratio(fg_rgb, bg_rgb) >= min_ratio:
        return bg_rgb

    fg_lum = _get_relative_luminance(fg_rgb)
    bg_lum = _get_relative_luminance(bg_rgb)

    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in bg_rgb))

    # Determine whether to lighten or darken the background to increase contrast
    make_bg_darker = bg_lum < fg_lum

    # Iteratively adjust brightness until the desired contrast is met
    for i in range(1, max_steps + 1):
        step_size = 0.06 + 0.02 * i  # Steps get larger to converge faster

        if make_bg_darker:
            new_v = v * (1.0 - step_size)
        else:
            new_v = v + (1.0 - v) * step_size

        candidate_bg = _tune_color_brightness(bg_rgb, new_v)

        if _get_contrast_ratio(fg_rgb, candidate_bg) >= min_ratio:
            return candidate_bg
        v = new_v  # Update brightness for the next iteration

    return _tune_color_brightness(bg_rgb, v)
