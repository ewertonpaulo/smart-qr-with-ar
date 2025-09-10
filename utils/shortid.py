from __future__ import annotations
import re, secrets, hashlib, unicodedata
from pathlib import Path
from typing import Union

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _slugify(text: str, max_len: int = 32) -> str:
    # remove acentos, baixa, troca espaços por '-', remove o que não for [a-z0-9-]
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9-]+", "", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:max_len] or "file"

def random_code(length: int = 9, alphabet: str = ALPHABET) -> str:
    # cada char escolhido com entropia ~log2(62)=5.95 bits. 9 chars ~53.6 bits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def _int_to_base62(n: int) -> str:
    if n == 0: return ALPHABET[0]
    chars = []
    base = len(ALPHABET)
    while n:
        n, r = divmod(n, base)
        chars.append(ALPHABET[r])
    return "".join(reversed(chars))

def hash_code_from_file(path: Path, length: int = 9, chunk: int = 1 << 20) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf: break
            sha.update(buf)
    n = int.from_bytes(sha.digest(), "big")
    return _int_to_base62(n)[:length]

def build_safe_name(
        source: Union[str, Path],
        code_len: int = 9,
        mode: str = "hash+rand",
        include_slug: bool = False
) -> str:
    """
    Retorna um nome curto e único, p.ex.: 'aB3fK9qP.jpg' ou 'banner-aB3fK9qP.jpg'
    mode:
      - "rand":      só aleatório (rápido)
      - "hash":      determinístico pelo conteúdo (mesmo arquivo => mesmo código)
      - "hash+rand": mistura hash do conteúdo com aleatório (ótimo equilíbrio)
    """
    p = Path(source)
    ext = p.suffix.lower()
    stem = p.stem

    slug = _slugify(stem) if include_slug else ""
    parts = []

    if "hash" in mode and p.exists():
        parts.append(hash_code_from_file(p, length=max(4, code_len // 2)))
    if "rand" in mode or not parts:
        parts.append(random_code(code_len - sum(len(x) for x in parts)))

    code = "".join(parts)[:code_len]
    return (f"{slug}-{code}{ext}" if slug else f"{code}{ext}")
