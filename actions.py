import shutil
from pathlib import Path

from utils.ar_utils import generate_mind_file, _create_img_light_version_if_needed
from utils.shortid import build_safe_name
from utils.utils import prompt, validate_file_exists, ensure_unique_filename, get_local_ip, _get_position_from_input
from utils.image_utils import add_qr_watermark
from local_server import MEDIA_SUBDIR, get_port

def action_add_watermark_qr():
    try:
        base_path = Path(validate_file_exists(prompt("Full path to the base image: ").strip()))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    content = prompt("Content for the QR Code: ").strip()
    if not content: return

    pos_input = prompt("Position (1: top-left, 2: top-right, 3: bottom-left, 4: bottom-right) [4]: ").strip() or "4"
    position = _get_position_from_input(pos_input)

    try:
        print("\nApplying QR Code...")
        out_path = add_qr_watermark(base_path, content, corner=position)
        print(f"QR Code applied. Image saved to: {out_path}")
    except Exception as e:
        print(f"Failed to apply QR Code: {e}")

def action_add_memory_qr():
    try:
        base_path = Path(validate_file_exists(prompt("Full path to the base image: ").strip()))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        local_path = Path(validate_file_exists(prompt("Path to the media file to be linked: ").strip()))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)
        safe_name = build_safe_name(local_path, code_len=9, mode="hash+rand", include_slug=False)
        dest_path = ensure_unique_filename(MEDIA_SUBDIR / safe_name)
        shutil.copy2(str(local_path), str(dest_path))

        port = get_port()
        ip = get_local_ip()
        url = f"http://{ip}:{port}/{dest_path.relative_to(MEDIA_SUBDIR.parent).as_posix()}"

        pos_input = prompt("Position (1: top-left, 2: top-right, 3: bottom-left, 4: bottom-right) [4]: ").strip() or "4"
        position = _get_position_from_input(pos_input)

        print("\nApplying QR Code watermark...")
        add_qr_watermark(base_path, url, corner=position)

        print(f"\nSuccess!")
        print(f"Scan the QR on the image to access the media file at http://{ip}:{port}/")

    except Exception as e:
        print(f"An error occurred during the process: {e}")

def action_create_ar_live_photo():
    """
    Creates a 'Live Photo' with AR (image tracking) using a .mind file.
    1) Generates .mind from the base image directly into /public/media
    2) Copies the video to /public/media
    3) Generates an HTML page from (template_ar.html) and copies to /public
    4) Applies a QR code to the base image with a link to template_ar created
    """
    resized_image_path = None
    try:
        print("\n--- Creating a 'Live Photo' Experience with AR ---")

        base_image_path = Path(validate_file_exists(prompt("Full path to the base image: ").strip()))
        video_path = Path(validate_file_exists(prompt("Path to the video to be linked: ").strip()))

        resized_image_path = _create_img_light_version_if_needed(base_image_path)

        MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)
        mind_filename = resized_image_path.with_suffix(".mind").name
        mind_dest_path = ensure_unique_filename(MEDIA_SUBDIR / mind_filename)

        mind_file = generate_mind_file(resized_image_path, mind_dest_path)

        if not mind_file:
            print("Creation canceled: failed to generate the .mind file.")
            return

        video_dest_path = ensure_unique_filename(MEDIA_SUBDIR / video_path.name)
        shutil.copy2(str(video_path), str(video_dest_path))

        ip = get_local_ip()
        port = get_port()

        video_url = f"{MEDIA_SUBDIR.name}/{video_dest_path.name}"
        mind_url = f"{MEDIA_SUBDIR.name}/{mind_dest_path.name}"

        template_path = Path("template_ar.html")
        if not template_path.exists():
            print(f"ERROR: The template file '{template_path}' was not found!")
            return

        html_content = template_path.read_text(encoding='utf-8')
        html_content = html_content.replace("__VIDEO_URL__", video_url)
        html_content = html_content.replace("__MIND_FILE_URL__", mind_url)

        final_html_name = f"{build_safe_name(base_image_path.stem, code_len=6)}.html"
        final_html_path = MEDIA_SUBDIR.parent / final_html_name
        final_html_path.write_text(html_content, encoding='utf-8')

        # TODO: Replace with your own ngrok URL (HTTPS is required).
        # For future implementation: The shorter the generated URL, the better for QR codes.
        ar_page_url = f"https://867bcdf3a993.ngrok-free.app/{final_html_name}"

        pos_input = prompt("\nQR Code Position (1: top-left, 2: top-right, 3: bottom-left, 4: bottom-right) [4]: ").strip() or "4"
        position = _get_position_from_input(pos_input)

        print("\nApplying QR Code that links to the AR experience...")
        out_path = add_qr_watermark(base_image_path, ar_page_url, corner=position)

        print("\n✅ Success! AR experience created.")
        print(f"Image with QR Code saved to: {out_path}")
        print(f"Experience URL: {ar_page_url}")
        print("\n=== INSTRUCTIONS ===")
        print("  1) Open the link on your phone and allow CAMERA access.")
        print("  2) Point it at the base image to see the video overlay.")

    except FileNotFoundError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the process: {e}")
    finally:
        if resized_image_path and resized_image_path != base_image_path:
            try:
                resized_image_path.unlink()
                print(f"Temporary file {resized_image_path} deleted.")
            except OSError as e:
                print(f"Error deleting temporary file {resized_image_path}: {e}")