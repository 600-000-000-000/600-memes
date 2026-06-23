import base64
import hashlib
import json
import time
from typing import Any

from coincurve._libsecp256k1 import ffi, lib
from fastapi import HTTPException

_CONTEXT_VERIFY = 257  # SECP256K1_CONTEXT_VERIFY
_ctx = lib.secp256k1_context_create(_CONTEXT_VERIFY)


def _compute_event_id(event: dict[str, Any]) -> str:
    serialized = json.dumps(
        [0, event["pubkey"], event["created_at"], event["kind"], event["tags"], event["content"]],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _verify_schnorr(pubkey_hex: str, sig_hex: str, msg_hex: str) -> bool:
    try:
        xonly_pk = ffi.new("secp256k1_xonly_pubkey *")
        pub_bytes = bytes.fromhex(pubkey_hex)
        if not lib.secp256k1_xonly_pubkey_parse(_ctx, xonly_pk, pub_bytes):
            return False
        sig_bytes = bytes.fromhex(sig_hex)
        msg_bytes = bytes.fromhex(msg_hex)
        return bool(lib.secp256k1_schnorrsig_verify(_ctx, sig_bytes, msg_bytes, len(msg_bytes), xonly_pk))
    except Exception:
        return False


def _parse_and_verify_nip98(authorization: str) -> dict[str, Any]:
    if not authorization.startswith("Nostr "):
        raise HTTPException(status_code=401, detail="Missing Nostr auth header")

    try:
        event_json = base64.b64decode(authorization[6:]).decode("utf-8")
        event: dict[str, Any] = json.loads(event_json)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid base64/JSON in auth header")

    required = {"id", "pubkey", "created_at", "kind", "tags", "content", "sig"}
    if not required.issubset(event.keys()):
        raise HTTPException(status_code=401, detail="Malformed Nostr event")

    if event["kind"] != 27235:
        raise HTTPException(status_code=401, detail="Expected kind 27235 (NIP-98)")

    if abs(int(time.time()) - event["created_at"]) > 60:
        raise HTTPException(status_code=401, detail="Event timestamp expired (>60s)")

    if event["id"] != _compute_event_id(event):
        raise HTTPException(status_code=401, detail="Event ID mismatch")

    if not _verify_schnorr(event["pubkey"], event["sig"], event["id"]):
        raise HTTPException(status_code=401, detail="Invalid Nostr signature")

    return event


def validate_nip98_auth(
    authorization: str,
    expected_url: str,
    file_bytes: bytes,
    members: set[str],
) -> str:
    event = _parse_and_verify_nip98(authorization)
    tags = {t[0]: t[1] for t in event["tags"] if len(t) >= 2}

    if tags.get("u") != expected_url:
        raise HTTPException(status_code=401, detail="URL mismatch in auth event")

    if tags.get("method", "").upper() != "POST":
        raise HTTPException(status_code=401, detail="Method mismatch in auth event")

    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    if tags.get("payload") != file_sha256:
        raise HTTPException(status_code=401, detail="Payload SHA256 mismatch")

    pubkey = event["pubkey"].lower()
    if pubkey not in members:
        raise HTTPException(status_code=403, detail="Not a 600.wtf member")

    return pubkey


def validate_nip98_delete_auth(
    authorization: str,
    expected_url: str,
    members: set[str],
) -> str:
    event = _parse_and_verify_nip98(authorization)
    tags = {t[0]: t[1] for t in event["tags"] if len(t) >= 2}

    if tags.get("u") != expected_url:
        raise HTTPException(status_code=401, detail="URL mismatch in auth event")

    if tags.get("method", "").upper() != "DELETE":
        raise HTTPException(status_code=401, detail="Method mismatch in auth event")

    pubkey = event["pubkey"].lower()
    if pubkey not in members:
        raise HTTPException(status_code=403, detail="Not a 600.wtf member")

    return pubkey
