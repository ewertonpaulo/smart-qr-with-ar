import shutil
from pathlib import Path

from utils.ar_utils import generate_mind_file
from utils.shortid import build_safe_name
from utils.utils import prompt, validate_file_exists, ensure_unique_filename, get_local_ip
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

    position = prompt("Position (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"
    params = {"size": 0.15, "margin": 0.02}

    try:
        print("\nApplying standard watermark...")
        out_path = add_qr_watermark(base_path, content, corner=position, size=params['size'], margin=params['margin'])
        print(f"Standard watermark applied. Image saved to: {out_path}")
    except Exception as e:
        print(f"Failed to apply watermark: {e}")

def action_watermark_with_media_link():
    try:
        base_path = Path(validate_file_exists(prompt("Full path to the base image: ").strip()))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        local_path = Path(validate_file_exists(prompt("Path to the media file to be linked (image/video): ").strip()))
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

        position = prompt("Position (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"
        params = {"size": 0.15, "margin": 0.02}

        print("\nApplying QR Code watermark...")
        add_qr_watermark(base_path, url, corner=position, size=params['size'], margin=params['margin'])

        print(f"\nSuccess!")
        print(f"Local server is active. Scan the QR on the image to access the media file at http://{ip}:{port}/")

    except Exception as e:
        print(f"An error occurred during the process: {e}")

def action_create_mindar_live_photo():
    """
    Cria 'Live Photo' com MindAR (image tracking) usando arquivo .mind.
    1) Gera .mind a partir da imagem base
    2) Copia .mind e o vídeo para /public/media
    3) Gera página HTML (template_mindar.html)
    4) Aplica QR na imagem base com link para a página
    """
    try:
        print("\n--- Criando uma Experiência 'Live Photo' com MindAR (Automatizado) ---")

        base_image_path = Path(validate_file_exists(prompt("Caminho completo para a imagem base (alvo): ").strip()))
        video_path = Path(validate_file_exists(prompt("Caminho para o vídeo a ser vinculado: ").strip()))
    except FileNotFoundError as e:
        print(f"Erro de arquivo: {e}")
        return

    mind_file = generate_mind_file(base_image_path)
    if not mind_file:
        print("Criação cancelada: falha ao gerar o arquivo .mind.")
        return

    try:
        MEDIA_SUBDIR.mkdir(parents=True, exist_ok=True)

        # copia mídia e mind
        video_dest_path = ensure_unique_filename(MEDIA_SUBDIR / video_path.name)
        shutil.copy2(str(video_path), str(video_dest_path))

        mind_dest_path = ensure_unique_filename(MEDIA_SUBDIR / mind_file.name)
        shutil.copy2(str(mind_file), str(mind_dest_path))

        ip = get_local_ip()
        port = get_port()

        video_url = f"{MEDIA_SUBDIR.name}/{video_dest_path.name}"
        mind_url = f"{MEDIA_SUBDIR.name}/{mind_dest_path.name}"

        template_path = Path("template_mind_ar.html")
        if not template_path.exists():
            print(f"ERRO: O arquivo de modelo '{template_path}' não foi encontrado!")
            return

        html_content = template_path.read_text(encoding='utf-8')
        html_content = html_content.replace("__VIDEO_URL__", video_url)
        html_content = html_content.replace("__MIND_FILE_URL__", mind_url)

        final_html_name = f"mindar_{build_safe_name(base_image_path, code_len=6)}.html"
        final_html_path = MEDIA_SUBDIR.parent / final_html_name
        final_html_path.write_text(html_content, encoding='utf-8')

        # ar_page_url = f"http://{ip}:{port}/{final_html_name}"
        ar_page_url = f"https://1880014aaa80.ngrok-free.app/{final_html_name}"

        position = prompt("\nPosição do QR Code (top-left/right, bottom-left/right) [bottom-right]: ").strip() or "bottom-right"
        params = {"size": 0.20, "margin": 0.02}

        print("\nAplicando QR Code que leva para a experiência MindAR...")
        out_path = add_qr_watermark(base_image_path, ar_page_url, corner=position, size=params['size'], margin=params['margin'])

        print("\n✅ Sucesso! Experiência MindAR criada.")
        print(f"Imagem com QR Code salva em: {out_path}")
        print(f"URL da experiência: {ar_page_url}")
        print("\n=== INSTRUÇÕES ===")
        print("  1) Abra o link no celular e permita o uso da CÂMERA.")
        print("  2) Aponte para a imagem base para ver o vídeo sobreposto.")
        print("  (iOS exige HTTPS fora do localhost).")

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processo: {e}")