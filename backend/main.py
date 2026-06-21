import logging
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import validate_nip98_auth
from members import load_members
from storage import MAX_FILE_SIZE, append_meme, get_memes, save_upload, validate_mime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("/app/uploads")
STATIC_DIR = Path("/app/static")

members, pubkey_to_name, pubkey_to_avatar = load_members()

app = FastAPI(title="memes.600.wtf")


@app.get("/api/memes")
async def list_memes():
    return JSONResponse(get_memes())


@app.post("/api/upload")
async def upload_meme(
    request: Request,
    file: UploadFile = File(...),
    authorization: str = Header(...),
):
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    try:
        mime = validate_mime(file.content_type, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    base = str(request.base_url).rstrip("/")
    expected_url = f"{base}/api/upload"

    pubkey = validate_nip98_auth(authorization, expected_url, file_bytes, members)
    name = pubkey_to_name.get(pubkey)
    avatar = pubkey_to_avatar.get(pubkey)

    filename, url = save_upload(file_bytes, file.filename or "upload", mime)
    append_meme(filename, url, pubkey, mime, name, avatar)

    logger.info("Upload: %s by %s (%s)", filename, name or "unknown", pubkey[:8])
    return {"filename": filename, "url": url, "uploader_pubkey": pubkey, "uploader_name": name}


UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
