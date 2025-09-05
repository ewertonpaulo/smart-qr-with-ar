# actions.py

import shutil
import uuid
import time
from datetime import datetime
from PIL import Image

from utils.utils import prompt, validate_file_exists, ensure_unique_filename, SAVED_DIR, get_local_ip
from utils.qr_utils import save_qr_code
from utils.image_utils import add_qr_watermark
from ai_qr import generate_artistic_qr
from local_server import start_local_server, MEDIA_SUBDIR

def action_generate_qr():
    content = prompt("Digite o conteúdo do QR Code (texto/URL): ").strip()
    if not content:
        return

    prompt_text = prompt("Prompt artístico (ou Enter para QR padrão): ").strip()

    if prompt_text:
        negative_prompt = "low quality, blurry, text artifacts, deformed, ugly"
        artistic_image = generate_artistic_qr(content, prompt_text, negative_prompt)

        if artistic_image:
            out_path = ensure_unique_filename(SAVED_DIR / "qrcode_artistico.png")
            artistic_image.save(out_path)
            print(f"QR Code artístico salvo em: {out_path}")
    else:
        out_path = save_qr_code(content, "qrcode_simples.png")
        print(f"QR Code salvo em: {out_path}")

def action_add_watermark_qr():
    try:
        base_path = validate_file_exists(prompt("Caminho completo da imagem base: ").strip())
    except FileNotFoundError as e:
        print(f"Erro: {e}")
        return

    content = prompt("Conteúdo para o QR Code: ").strip()
    if not content: return

    position = prompt("Posição (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"

    params = {"size": 0.2, "margin": 0.02, "opacity": 0.90}

    prompt_text = prompt("Prompt artístico para a marca d'água (ou Enter para QR padrão): ").strip()

    if not prompt_text:
        # --- Fluxo Padrão (agora usando params) ---
        try:
            print("Aplicando marca d'água padrão...")
            out_path = add_qr_watermark(
                base_path,
                content,
                corner=position,
                size=params['size'],
                margin=params['margin']
            )
            print(f"Marca d'água padrão aplicada. Imagem salva em: {out_path}")
        except Exception as e:
            print(f"Falha ao aplicar marca d'água: {e}")
    else:
        # --- Fluxo Artístico com IA ---
        negative_prompt = "low quality, blurry, text artifacts, deformed, messy, ugly, nsfw"
        artistic_qr = generate_artistic_qr(content, prompt_text, negative_prompt)

        if not artistic_qr: return

        try:
            print("Aplicando marca d'água artística...")
            base = Image.open(base_path).convert("RGBA")
            W, H = base.size

            side = int(round(W * params['size']))
            margin_px = int(round(min(W, H) * params['margin']))

            if position == "top-left": x, y = margin_px, margin_px
            elif position == "top-right": x, y = W - side - margin_px, margin_px
            elif position == "bottom-left": x, y = margin_px, H - side - margin_px
            else: x, y = W - side - margin_px, H - side - margin_px

            watermark = artistic_qr.resize((side, side), Image.LANCZOS).convert("RGBA")

            alpha = watermark.getchannel('A')
            new_alpha = alpha.point(lambda p: int(p * params['opacity']))
            watermark.putalpha(new_alpha)

            base.alpha_composite(watermark, dest=(x, y))

            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_name = f"{base_path.stem}_art_watermark_{ts}.png"
            out_path = ensure_unique_filename(SAVED_DIR / out_name)
            base.convert("RGB").save(out_path, format="PNG")
            print(f"Marca d'água artística aplicada. Imagem salva em: {out_path}")

        except Exception as e:
            print(f"Falha ao aplicar marca d'água artística: {e}")

def action_media_qr_local():
    try:
        local_path = validate_file_exists(prompt("Caminho do arquivo de imagem/vídeo: ").strip())
    except FileNotFoundError as e:
        print(f"Erro: {e}")
        return

    MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)

    safe_name = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex}{local_path.suffix.lower()}"
    dest_path = MEDIA_SUBDIR / safe_name

    print("Copiando arquivo para a pasta pública...")
    shutil.copy2(str(local_path), str(dest_path))

    try:
        port = start_local_server()
        ip = get_local_ip()
        url = f"http://{ip}:{port}/{dest_path.relative_to(MEDIA_SUBDIR.parent).as_posix()}"

        print(f"Link local gerado: {url}")

        prompt_text = prompt("Prompt artístico para o QR Code do link (ou Enter para padrão): ").strip()

        if prompt_text:
            negative_prompt = "low quality, blurry, text artifacts, deformed, ugly"
            artistic_image = generate_artistic_qr(url, prompt_text, negative_prompt)
            if artistic_image:
                out_path = ensure_unique_filename(SAVED_DIR / "qrcode_midia_artistico.png")
                artistic_image.save(out_path)
                print(f"QR Code artístico de acesso salvo em: {out_path}")
        else:
            out_path = save_qr_code(url, "qrcode_midia_local.png")
            print(f"QR Code de acesso salvo em: {out_path}")

        print(f"Servidor local ativo. Acesse os arquivos em http://{ip}:{port}/")
    except Exception as e:
        print(f"Falha ao iniciar servidor ou gerar QR Code: {e}")