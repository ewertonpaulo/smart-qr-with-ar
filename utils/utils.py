import sys
import socket
from pathlib import Path

SAVED_DIR = Path("../saved")
SAVED_DIR.mkdir(exist_ok=True)

APP_NAME = "Photo Smart QR Code"

def prompt(message: str) -> str:
    try:
        return input(message)
    except (KeyboardInterrupt, EOFError):
        print("\nSaindo...")
        sys.exit(0)

def ensure_unique_filename(path: Path) -> Path:
    if not path.exists():
        return path

    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        new_path = path.with_name(f"{stem}({i}){suffix}")
        if not new_path.exists():
            return new_path
        i += 1

def validate_file_exists(path_str: str) -> Path:
    p = Path(path_str).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")
    return p

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"