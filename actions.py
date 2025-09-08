import shutil
import uuid
import time
from datetime import datetime
from PIL import Image

from utils.utils import prompt, validate_file_exists, ensure_unique_filename, SAVED_DIR, get_local_ip
from utils.qr_utils import save_qr_code
from utils.image_utils import add_qr_watermark, add_textured_qr_watermark
from ai_qr import generate_artistic_qr
from local_server import start_local_server, MEDIA_SUBDIR

def action_generate_qr():
    content = prompt("Enter QR Code content (text/URL): ").strip()
    if not content: return
    prompt_text = prompt("Artistic prompt (or Enter for standard QR): ").strip()
    if prompt_text:
        negative_prompt = "low quality, blurry, text artifacts, deformed, ugly"
        artistic_image = generate_artistic_qr(content, prompt_text, negative_prompt)
        if artistic_image:
            out_path = ensure_unique_filename(SAVED_DIR / "artistic_qrcode.png")
            artistic_image.save(out_path)
            print(f"Artistic QR Code saved to: {out_path}")
    else:
        out_path = save_qr_code(content, "simple_qrcode.png")
        print(f"QR Code saved to: {out_path}")

def action_add_watermark_qr():
    try:
        base_path = validate_file_exists(prompt("Full path to the base image: ").strip())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    content = prompt("Content for the QR Code: ").strip()
    if not content: return

    position = prompt("Position (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"

    print("\nChoose watermark style:")
    print("  1) Standard (black and white)")
    print("  2) Artistic (AI, requires a prompt)")
    choice = prompt("Style option [1]: ").strip() or "1"

    params = {"size": 0.20, "margin": 0.02, "opacity": 0.90}

    if choice == '1':
        try:
            print("\nApplying standard watermark...")
            out_path = add_qr_watermark(base_path, content, corner=position, size=params['size'], margin=params['margin'])
            print(f"Standard watermark applied. Image saved to: {out_path}")
        except Exception as e:
            print(f"Failed to apply watermark: {e}")

    elif choice == '2':
        prompt_text = prompt("Artistic prompt for the watermark: ").strip()
        if not prompt_text:
            print("A prompt is required for the artistic style. Operation cancelled.")
            return

        negative_prompt = "low quality, blurry, text artifacts, deformed, messy, ugly, nsfw"
        artistic_qr = generate_artistic_qr(content, prompt_text, negative_prompt)

        if not artistic_qr: return
        try:
            print("\nApplying artistic watermark...")
            base = Image.open(base_path).convert("RGBA")
            W, H = base.size
            side = int(round(W * params['size']))
            margin_px = int(round(min(W, H) * params['margin']))

            if position == "top-left": x, y = margin_px, margin_px
            elif position == "top-right": x, y = W - side - margin_px, margin_px
            elif position == "bottom-left": x, y = margin_px, H - side - margin_px
            else: x, y = W - side - margin_px, H - side - margin_px

            watermark = artistic_qr.resize((side, side), Image.LANCZOS).convert("RGBA")
            alpha = watermark.getchannel('A'); new_alpha = alpha.point(lambda p: int(p * params['opacity'])); watermark.putalpha(new_alpha)
            base.alpha_composite(watermark, dest=(x, y))

            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_name = f"{base_path.stem}_art_watermark_{ts}.png"
            out_path = ensure_unique_filename(SAVED_DIR / out_name)
            base.convert("RGB").save(out_path, format="PNG")
            print(f"Artistic watermark applied. Image saved to: {out_path}")
        except Exception as e:
            print(f"Failed to apply artistic watermark: {e}")

def action_media_qr_local():
    try:
        local_path = validate_file_exists(prompt("Path to the image/video file: ").strip())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex}{local_path.suffix.lower()}"
    dest_path = MEDIA_SUBDIR / safe_name
    print("Copying file to the public folder...")
    shutil.copy2(str(local_path), str(dest_path))
    try:
        port = start_local_server()
        ip = get_local_ip()
        url = f"http://{ip}:{port}/{dest_path.relative_to(MEDIA_SUBDIR.parent).as_posix()}"
        print(f"Local link generated: {url}")
        prompt_text = prompt("Artistic prompt for the link's QR Code (or Enter for standard): ").strip()
        if prompt_text:
            negative_prompt = "low quality, blurry, text artifacts, deformed, ugly"
            artistic_image = generate_artistic_qr(url, prompt_text, negative_prompt)
            if artistic_image:
                out_path = ensure_unique_filename(SAVED_DIR / "media_artistic_qrcode.png")
                artistic_image.save(out_path)
                print(f"Artistic access QR Code saved to: {out_path}")
        else:
            out_path = save_qr_code(url, "media_local_qrcode.png")
            print(f"Access QR Code saved to: {out_path}")
        print(f"Local server is active. Access files at http://{ip}:{port}/")
    except Exception as e:
        print(f"Failed to start server or generate QR Code: {e}")