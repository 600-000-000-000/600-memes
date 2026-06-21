# memes.600.wtf

Meme board for the [600.wtf](https://600.wtf) Nostr community. Members can upload images and videos, anyone can browse.

## Auth

Uploads require a [NIP-07](https://github.com/nostr-protocol/nips/blob/master/07.md) browser extension (Alby, nos2x). The server validates a [NIP-98](https://github.com/nostr-protocol/nips/blob/master/98.md) signed event and checks the uploader's pubkey against `nostr.json`.

## Stack

- **Frontend** — SolidJS + Vite
- **Backend** — Python FastAPI, `coincurve` for Schnorr verification
- **Auth** — NIP-98 HTTP Auth (kind 27235), members from `nostr.json`

## Build & run

```bash
make build
make run
```

Runs on port `8000`. Uploads are persisted in `./uploads/`.

## Local dev

```bash
# Backend
cd backend && uv sync && uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev   # :5173, proxies /api → :8000
```
