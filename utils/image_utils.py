import colorsys
from pathlib import Path
from random import random

from PIL import Image, ImageOps, ImageFilter, ImageChops
from .qr_utils import generate_qr_image
from .utils import ensure_unique_filename, SAVED_DIR
from qrcode.constants import ERROR_CORRECT_M

def add_qr_watermark(
        base_image_path: Path,
        qr_content: str,
        corner: str = "bottom-right",
        size: float = 0.20,
        margin: float = 0.02,
        tile_ratio: float = 0.22,      # janela para escolher a cor dentro do patch
        noise_amount: float = 0.12,    # ruído multiplicativo (0.05–0.20)
        opacity: float = 0.80,         # opacidade dos módulos pretos
        bg_opacity: float = 0.40,      # opacidade do background
        bg_source: str = "image",      # "image" (do patch) ou "complement"
        color_contrast_amount: float = 0.15,  # intensidade do ruído cromático (0.05–0.30)
        min_contrast: float = 2.8,
) -> Path:
    base = Image.open(base_image_path).convert("RGBA")
    W, H = base.size
    side = int(round(W * size))
    margin_px = int(round(min(W, H) * margin))

    # posicionamento
    if corner not in {"top-left","top-right","bottom-left","bottom-right"}:
        corner = "bottom-right"
    if corner == "bottom-right": x, y = W - side - margin_px, H - side - margin_px
    elif corner == "bottom-left": x, y = margin_px, H - side - margin_px
    elif corner == "top-right": x, y = W - side - margin_px, margin_px
    else: x, y = margin_px, margin_px

    # patch do canto (fundo fora do patch permanece intocado)
    patch = base.crop((x, y, x + side, y + side)).convert("RGBA")

    # sub-bloco mais contrastado para EXTRAIR A COR dos módulos
    tile_px = max(16, int(side * tile_ratio))
    tile = _find_best_texture_tile(patch, tile_px)

    # cor sólida dos módulos (auto-contraste vs luminância média do patch)
    patch_avg_lum = _rel_luminance(ImageOps.fit(patch.convert("RGB"), (1,1), Image.BOX).getpixel((0,0)))
    solid_color = _pick_high_contrast_color(tile, patch_avg_lum)  # (r,g,b,255)

    # cor de background: da própria imagem (tile/patch) ou complementar
    bg_rgb = _contrasting_color_from_patch(patch, solid_color, scope="tile", tile=tile, sat_floor=0.0)
    bg_rgb = _ensure_min_contrast_bg(solid_color[:3], bg_rgb, min_ratio=min_contrast)

    # QR binário (sem borda)
    qr_img = generate_qr_image(qr_content, border=0, error_correction=ERROR_CORRECT_M)
    qr_resized = qr_img.resize((side, side), resample=Image.NEAREST)

    # --- BACKGROUND translúcido (40%) apenas no quadrado do QR ---
    bg_alpha = int(max(0.0, min(1.0, bg_opacity)) * 255)
    bg_layer = Image.new("RGBA", (side, side), (bg_rgb[0], bg_rgb[1], bg_rgb[2], bg_alpha))
    final_qr_area = Image.alpha_composite(patch, bg_layer)  # patch permanece sem “efeitos”

    # ============================
    # MÓDULOS PRETOS (80% alpha)
    #   1) ruído multiplicativo (luminância)
    #   2) ruído cromático de contraste usando bg_rgb
    # ============================

    # 1) base colorida + ruído multiplicativo
    base_color_rgb = Image.new("RGB", (side, side), solid_color[:3])

    gain = _make_gain_map((side, side), amount=noise_amount)  # L (0..255) mapeado para ganho
    gain_rgb = Image.merge("RGB", (gain, gain, gain))
    noisy_rgb = ImageChops.multiply(base_color_rgb, gain_rgb)  # granulação luminosa

    # 2) ruído cromático com a cor de background (aumenta micro-contraste)
    #    cria máscara de mistura a partir de um ruído bruto e baixa intensidade
    try:
        raw_noise = Image.effect_noise((side, side), 64.0).convert("L")  # gaussian
    except Exception:
        raw_noise = Image.new("L", (side, side))
        raw_noise.putdata([random.randint(0, 255) for _ in range(side * side)])

    mix_s = max(0.0, min(1.0, color_contrast_amount))
    # máscara fraca (0..255*mix_s); invertida para manter a cor base predominante
    mix_mask = raw_noise.point(lambda v: int(v * mix_s))
    mix_mask = ImageOps.invert(mix_mask)

    bg_tint_rgb = Image.new("RGB", (side, side), bg_rgb)
    # mistura pontilhada: predominantemente a cor do módulo, com sprinkles da cor do BG
    noisy_contrast_rgb = Image.composite(noisy_rgb, bg_tint_rgb, mix_mask)

    # converte para RGBA para aplicar a máscara dos módulos com opacidade 80%
    color_layer = noisy_contrast_rgb.convert("RGBA")

    modules_mask = ImageOps.invert(qr_resized.convert("L"))   # 255 onde o QR é preto
    alpha = max(0.0, min(1.0, opacity))
    mask_alpha = modules_mask.point(lambda p: int(p * alpha))

    # aplica somente nos módulos pretos, em cima do background
    final_qr_area.paste(color_layer, (0, 0), mask=mask_alpha)

    # compõe de volta no canto escolhido
    base.alpha_composite(final_qr_area, dest=(x, y))
    out = ensure_unique_filename(SAVED_DIR / f"{base_image_path.stem}_qr_color_noise_bg_contrast.png")
    base.convert("RGB").save(out, "PNG")
    return out

def _make_gain_map(size, amount=0.10):
    """
    Gera um mapa de ganho (L 0..255) para ruído multiplicativo.
    amount ~ intensidade do ruído (0.05–0.20 recomendado).
    """
    w, h = size
    # tenta usar effect_noise (se existir); senão cai no aleatório puro
    try:
        noise = Image.effect_noise((w, h), 64.0)
    except Exception:
        noise = Image.new("L", (w, h))
        noise.putdata([random.randint(0, 255) for _ in range(w * h)])

    # mapeia o ruído [0..255] p/ um ganho em torno de 1.0:
    # gain = 1 + amount * ((v - 128)/128)  ⇒  depois escala para [0..255]
    table = []
    for v in range(256):
        factor = 1.0 + amount * ((v - 128) / 128.0)
        factor = max(0.0, min(2.0, factor))
        table.append(int(round(factor * 255)))
    return noise.point(table, mode="L")

def _rel_luminance(rgb):  # rgb = (0..255)
    r, g, b = [v / 255.0 for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _find_best_texture_tile(patch: Image.Image, tile_px: int) -> Image.Image:
    gray = patch.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    w, h = edges.size
    gw, gh = max(1, w // tile_px), max(1, h // tile_px)
    agg = edges.resize((gw, gh), resample=Image.BOX)  # média por bloco
    arr = list(agg.getdata())
    k = arr.index(max(arr))
    cx, cy = k % gw, k // gw
    x0, y0 = min(w - tile_px, cx * tile_px), min(h - tile_px, cy * tile_px)
    return patch.crop((x0, y0, x0 + tile_px, y0 + tile_px))

def _contrast_ratio(rgb1, rgb2):
    # usa a mesma luminância relativa do teu helper _rel_luminance
    L1 = _rel_luminance(rgb1[:3])
    L2 = _rel_luminance(rgb2[:3])
    if L1 < L2:
        L1, L2 = L2, L1
    return (L1 + 0.05) / (L2 + 0.05)

def _contrasting_color_from_patch(
        patch: Image.Image,
        avoid_rgb,                 # cor do QR (r,g,b[,a])
        scope: str = "tile",       # "tile" usa o melhor sub-bloco; "patch" usa o patch todo
        tile: Image.Image | None = None,
        sat_floor: float = 0.40,   # saturação mínima
        sample_size: int = 64      # downsample p/ acelerar a varredura
):
    """
    Escolhe uma cor *do próprio patch* que maximize o contraste contra `avoid_rgb`.
    Se scope="tile" e `tile` vier preenchido, varre o tile; senão varre o patch inteiro.
    """
    src = tile if (scope == "tile" and tile is not None) else patch
    img = src.resize((sample_size, sample_size), Image.BOX).convert("RGB")

    best_rgb, best_score = (0, 0, 0), -1.0
    for rgb in img.getdata():
        cr = _contrast_ratio(rgb, avoid_rgb)
        # bônus leve por saturação para evitar acinzentado que “sujaria” o véu
        h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
        score = cr + 0.12 * s
        if score > best_score:
            best_rgb, best_score = rgb, score

    # garante saturação mínima, mas *sem* alterar brilho global
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in best_rgb))
    s = max(s, sat_floor)
    rr, gg, bb = [int(round(x * 255)) for x in colorsys.hsv_to_rgb(h, s, v)]
    return (rr, gg, bb)

def _pick_high_contrast_color(tile: Image.Image, patch_avg_lum: float):
    # escolhe a cor do próprio tile que mais difere na luminância do patch
    t = tile.resize((64, 64), Image.BOX).convert("RGB")
    best_rgb, best_score = (0, 0, 0), -1.0
    for rgb in t.getdata():
        L = _rel_luminance(rgb)
        score = abs(L - patch_avg_lum)
        if score > best_score:
            best_rgb, best_score = rgb, score
    return (best_rgb[0], best_rgb[1], best_rgb[2], 255)

def _contrast_ratio(rgb1, rgb2):
    L1 = _rel_luminance(rgb1[:3])
    L2 = _rel_luminance(rgb2[:3])
    if L1 < L2:
        L1, L2 = L2, L1
    return (L1 + 0.05) / (L2 + 0.05)

def _tune_v(rgb, new_v):
    """Retorna rgb com o mesmo H/S e V ajustado para new_v (0..1)."""
    r, g, b = [c / 255.0 for c in rgb[:3]]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = max(0.0, min(1.0, new_v))
    rr, gg, bb = [int(round(x * 255)) for x in colorsys.hsv_to_rgb(h, s, v)]
    return (rr, gg, bb)

def _ensure_min_contrast_bg(fg_rgb, bg_rgb, min_ratio=2.8, max_steps=12):
    """
    Se contraste(fg,bg) < min_ratio, empurra o *background*:
      - se bg é mais escuro que fg => escurece ainda mais o bg (v ↓)
      - se bg é mais claro que fg  => clareia ainda mais o bg (v ↑)
    Mantém hue/saturação do bg.
    """
    fgL = _rel_luminance(fg_rgb)
    bgL = _rel_luminance(bg_rgb)
    if _contrast_ratio(fg_rgb, bg_rgb) >= min_ratio:
        return bg_rgb

    # trabalha no canal V (HSV) para preservar cor
    r, g, b = [c / 255.0 for c in bg_rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # direção: afasta o bg do fg
    make_bg_darker = (bgL < fgL)  # bg já é mais escuro -> empurra mais p/ escuro
    # passos progressivos (crescentes) para convergir rápido
    for i in range(1, max_steps + 1):
        step = 0.06 + 0.02 * i      # 0.08 → ~0.30 ao longo das iterações
        vv = v * (1.0 - step) if make_bg_darker else v + (1.0 - v) * step
        cand = _tune_v(bg_rgb, vv)
        if _contrast_ratio(fg_rgb, cand) >= min_ratio:
            return cand
        v = vv
    return _tune_v(bg_rgb, v)

