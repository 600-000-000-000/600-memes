import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import validate_nip98_auth, validate_nip98_delete_auth
from members import load_members
from storage import MAX_FILE_SIZE, append_meme, backfill_thumbnails, delete_meme, generate_thumbnail, get_memes, save_upload, validate_mime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("/app/uploads")
STATIC_DIR = Path("/app/static")

members, pubkey_to_name, pubkey_to_avatar = load_members()

_DNI_PUBKEY = next((pk for pk, name in pubkey_to_name.items() if name == "dni"), None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.get_event_loop().run_in_executor(None, backfill_thumbnails)
    yield


app = FastAPI(title="memes.600.wtf", lifespan=lifespan)


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
    generate_thumbnail(filename, mime)
    append_meme(filename, url, pubkey, mime, name, avatar)

    logger.info("Upload: %s by %s (%s)", filename, name or "unknown", pubkey[:8])
    return {"filename": filename, "url": url, "uploader_pubkey": pubkey, "uploader_name": name}


@app.delete("/api/memes/{filename}")
async def delete_meme_endpoint(
    filename: str,
    request: Request,
    authorization: str = Header(...),
):
    base = str(request.base_url).rstrip("/")
    expected_url = f"{base}/api/memes/{filename}"

    pubkey = validate_nip98_delete_auth(authorization, expected_url, members)

    all_memes = get_memes()
    meme = next((m for m in all_memes if m["filename"] == filename), None)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    if pubkey != meme["uploader_pubkey"] and pubkey != _DNI_PUBKEY:
        raise HTTPException(status_code=403, detail="Not allowed to delete this meme")

    if not delete_meme(filename):
        raise HTTPException(status_code=404, detail="Meme not found")

    logger.info("Delete: %s by %s (%s)", filename, pubkey_to_name.get(pubkey, "unknown"), pubkey[:8])
    return {"deleted": filename}


UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
