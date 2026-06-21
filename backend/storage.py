import hashlib
import json
import mimetypes
import threading
import time
import uuid
from pathlib import Path

UPLOADS_DIR = Path("/app/uploads")
MEMES_FILE = UPLOADS_DIR / "memes.json"

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/avif",
    "video/mp4", "video/webm", "video/ogg", "video/quicktime", "video/x-matroska",
}
MAX_FILE_SIZE = 50 * 1024 * 1024

_lock = threading.Lock()


def get_memes() -> list[dict]:
    if not MEMES_FILE.exists():
        return []
    with open(MEMES_FILE) as f:
        return json.load(f)


def validate_mime(content_type: str | None, filename: str) -> str:
    mime = content_type or mimetypes.guess_type(filename)[0] or ""
    mime = mime.split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME:
        raise ValueError(f"MIME type not allowed: {mime or 'unknown'}")
    return mime


def save_upload(file_bytes: bytes, original_name: str, mime: str) -> tuple[str, str]:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix.lower() or _mime_ext(mime)
    sha_prefix = hashlib.sha256(file_bytes).hexdigest()[:12]
    filename = f"{sha_prefix}_{uuid.uuid4().hex[:8]}{ext}"
    (UPLOADS_DIR / filename).write_bytes(file_bytes)
    return filename, f"/uploads/{filename}"


def append_meme(
    filename: str, url: str, pubkey: str, mime: str,
    name: str | None = None, avatar: str | None = None,
) -> None:
    with _lock:
        memes = get_memes()
        entry: dict = {
            "filename": filename,
            "url": url,
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "uploader_pubkey": pubkey,
            "mime_type": mime,
        }
        if name:
            entry["uploader_name"] = name
        if avatar:
            entry["uploader_avatar"] = avatar
        memes.append(entry)
        MEMES_FILE.write_text(json.dumps(memes, indent=2))


def _mime_ext(mime: str) -> str:
    return {
        "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
        "image/webp": ".webp", "image/avif": ".avif",
        "video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogv",
        "video/quicktime": ".mov", "video/x-matroska": ".mkv",
    }.get(mime, "")
