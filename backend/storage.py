import hashlib
import json
import logging
import mimetypes
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("/app/uploads")
MEMES_FILE = UPLOADS_DIR / "memes.json"

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/avif",
    "video/mp4", "video/webm", "video/ogg", "video/quicktime", "video/x-matroska",
}
MAX_FILE_SIZE = 50 * 1024 * 1024
THUMB_SIZE = (600, 600)

_lock = threading.Lock()

# Filenames must be lowercase alphanumeric with underscores and a single dot extension.
# This is enforced at upload time (save_upload) and re-checked at every
# filesystem operation so path traversal is impossible even with a corrupt DB.
_SAFE_FILENAME_RE = re.compile(r"^[a-z0-9][a-z0-9_]*\.[a-z0-9]+$")


def assert_safe_filename(filename: str) -> None:
    """Raise ValueError if filename could cause path traversal or filesystem issues."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise ValueError(f"Unsafe filename: {filename!r}")
    # Resolved path must stay inside UPLOADS_DIR (catches any symlink tricks too).
    try:
        (UPLOADS_DIR / filename).resolve().relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        raise ValueError(f"Filename escapes upload directory: {filename!r}")


def _thumb_path(filename: str) -> Path:
    return UPLOADS_DIR / f"{Path(filename).stem}_thumb.jpg"


def _load_memes() -> list[dict]:
    if not MEMES_FILE.exists():
        return []
    with open(MEMES_FILE) as f:
        return json.load(f)


def get_memes() -> list[dict]:
    return sorted(_load_memes(), key=lambda m: m.get("uploaded_at", ""), reverse=True)


def validate_mime(content_type: str | None, filename: str) -> str:
    mime = content_type or mimetypes.guess_type(filename)[0] or ""
    mime = mime.split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME:
        raise ValueError(f"MIME type not allowed: {mime or 'unknown'}")
    return mime


def save_upload(file_bytes: bytes, original_name: str, mime: str) -> tuple[str, str]:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    raw_ext = Path(original_name).suffix.lower()
    # Strip to [a-z0-9] only so the generated filename always satisfies _SAFE_FILENAME_RE.
    clean_ext = re.sub(r"[^a-z0-9]", "", raw_ext.lstrip("."))
    ext = f".{clean_ext}" if clean_ext else _mime_ext(mime)
    sha_prefix = hashlib.sha256(file_bytes).hexdigest()[:12]
    filename = f"{sha_prefix}_{uuid.uuid4().hex[:8]}{ext}"
    (UPLOADS_DIR / filename).write_bytes(file_bytes)
    return filename, f"/uploads/{filename}"


def generate_thumbnail(filename: str, mime: str) -> bool:
    assert_safe_filename(filename)
    src = UPLOADS_DIR / filename
    thumb = _thumb_path(filename)

    try:
        if mime.startswith("image/"):
            with Image.open(src) as img:
                img = img.convert("RGB")
                img.thumbnail(THUMB_SIZE)
                img.save(thumb, "JPEG", quality=85, optimize=True)
            return True

        if mime.startswith("video/"):
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(src),
                    "-ss", "0", "-vframes", "1",
                    "-vf", f"scale={THUMB_SIZE[0]}:-2",
                    str(thumb),
                ],
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and thumb.exists():
                return True
            logger.warning("ffmpeg thumbnail failed for %s: %s", filename, result.stderr[-200:])

    except Exception as e:
        logger.warning("Thumbnail generation failed for %s: %s", filename, e)

    return False


def append_meme(
    filename: str, url: str, pubkey: str, mime: str,
    name: str | None = None, avatar: str | None = None,
) -> None:
    with _lock:
        memes = _load_memes()
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


def backfill_thumbnails() -> None:
    memes = _load_memes()
    to_fill = [m for m in memes if not _thumb_path(m["filename"]).exists()]
    if not to_fill:
        logger.info("Thumbnail check: all %d memes have thumbnails", len(memes))
        return

    logger.info("Thumbnail check: generating thumbnails for %d/%d memes…", len(to_fill), len(memes))
    ok = sum(generate_thumbnail(m["filename"], m["mime_type"]) for m in to_fill)
    failed = len(to_fill) - ok
    logger.info("Thumbnail check: done — %d generated, %d failed", ok, failed)


def delete_meme(filename: str) -> bool:
    assert_safe_filename(filename)
    with _lock:
        memes = _load_memes()
        new_memes = [m for m in memes if m["filename"] != filename]
        if len(new_memes) == len(memes):
            return False
        MEMES_FILE.write_text(json.dumps(new_memes, indent=2))
        for path in [UPLOADS_DIR / filename, _thumb_path(filename)]:
            if path.exists():
                path.unlink()
        return True


def _mime_ext(mime: str) -> str:
    return {
        "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
        "image/webp": ".webp", "image/avif": ".avif",
        "video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogv",
        "video/quicktime": ".mov", "video/x-matroska": ".mkv",
    }.get(mime, "")
