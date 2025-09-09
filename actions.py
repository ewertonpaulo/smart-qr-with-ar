import shutil
import uuid
import time

from utils.shortid import build_safe_name
from utils.utils import prompt, validate_file_exists, ensure_unique_filename, SAVED_DIR, get_local_ip
from utils.qr_utils import save_qr_code
from utils.image_utils import add_qr_watermark
from local_server import start_local_server, MEDIA_SUBDIR

def action_generate_qr():
    content = prompt("Enter QR Code content (text/URL): ").strip()
    if not content: return
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
    choice = "1"
    params = {"size": 0.15, "margin": 0.02, "opacity": 0.90}

    if choice == '1':
        try:
            print("\nApplying standard watermark...")
            out_path = add_qr_watermark(base_path, content, corner=position, size=params['size'], margin=params['margin'])
            print(f"Standard watermark applied. Image saved to: {out_path}")
        except Exception as e:
            print(f"Failed to apply watermark: {e}")

def action_media_qr_local():
    try:
        local_path = validate_file_exists(prompt("Path to the image/video file: ").strip())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)
    safe_name = build_safe_name(local_path, code_len=9, mode="hash+rand", include_slug=False)
    dest_path = ensure_unique_filename(MEDIA_SUBDIR / safe_name)
    print("Copying file to the public folder...")
    shutil.copy2(str(local_path), str(dest_path))
    try:
        port = start_local_server()
        ip = get_local_ip()
        url = f"http://{ip}:{port}/{dest_path.relative_to(MEDIA_SUBDIR.parent).as_posix()}"
        print(f"Local link generated: {url}")
        out_path = save_qr_code(url, "media_local_qrcode.png")
        print(f"Access QR Code saved to: {out_path}")
        print(f"Local server is active. Access files at http://{ip}:{port}/")
    except Exception as e:
        print(f"Failed to start server or generate QR Code: {e}")

def action_watermark_with_media_link():
    """
    Combines hosting a local media file and adding a QR code watermark to a base image.
    """
    try:
        base_path = validate_file_exists(prompt("Full path to the base image: ").strip())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        local_path = validate_file_exists(prompt("Path to the media file to be linked (image/video): ").strip())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        # Part 1: Host the media file and generate a URL
        MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)
        safe_name = build_safe_name(local_path, code_len=9, mode="hash+rand", include_slug=False)
        dest_path = ensure_unique_filename(MEDIA_SUBDIR / safe_name)
        print("Copying media file to the public folder...")
        shutil.copy2(str(local_path), str(dest_path))

        port = start_local_server()
        ip = get_local_ip()
        url = f"http://{ip}:{port}/{dest_path.relative_to(MEDIA_SUBDIR.parent).as_posix()}"
        print(f"Local link generated for QR Code: {url}")

        # Part 2: Add the QR code as a watermark to the base image
        position = prompt("Position (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"
        params = {"size": 0.15, "margin": 0.02}

        print("\nApplying QR Code watermark...")
        out_path = add_qr_watermark(base_path, url, corner=position, size=params['size'], margin=params['margin'])

        print(f"\nSuccess!")
        print(f"Watermarked image with media link QR Code saved to: {out_path}")
        print(f"Local server is active. Scan the QR on the image to access the media file at http://{ip}:{port}/")

    except Exception as e:
        print(f"An error occurred during the process: {e}")