import { createSignal } from 'solid-js'

interface Props {
  onClose: () => void
  onSuccess: () => void
}

const MAX_SIZE = 50 * 1024 * 1024
const ALLOWED = ['image/', 'video/']

async function sha256hex(file: File): Promise<string> {
  const buf = await file.arrayBuffer()
  const hash = await crypto.subtle.digest('SHA-256', buf)
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export default function UploadModal(props: Props) {
  const [file, setFile] = createSignal<File | null>(null)
  const [dragging, setDragging] = createSignal(false)
  const [status, setStatus] = createSignal('')
  const [error, setError] = createSignal('')
  const [success, setSuccess] = createSignal(false)
  const [uploading, setUploading] = createSignal(false)

  function validateFile(f: File): string | null {
    if (!ALLOWED.some((p) => f.type.startsWith(p)))
      return `Type "${f.type}" not allowed. Images and videos only.`
    if (f.size > MAX_SIZE) return 'File too large (max 50 MB).'
    return null
  }

  function pick(f: File) {
    const err = validateFile(f)
    if (err) { setError(err); return }
    setError('')
    setFile(f)
  }

  function onInputChange(e: Event) {
    const input = e.currentTarget as HTMLInputElement
    if (input.files?.[0]) pick(input.files[0])
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer?.files[0]
    if (f) pick(f)
  }

  async function upload() {
    const f = file()
    if (!f) return

    if (!window.nostr) {
      setError('No Nostr extension found. Install Alby or nos2x.')
      return
    }

    setUploading(true)
    setError('')

    try {
      setStatus('Computing SHA256…')
      const sha256 = await sha256hex(f)

      setStatus('Requesting signature…')
      const unsigned = {
        kind: 27235,
        created_at: Math.floor(Date.now() / 1000),
        tags: [
          ['u', `${location.origin}/api/upload`],
          ['method', 'POST'],
          ['payload', sha256],
        ],
        content: '',
      }
      const signed = await window.nostr.signEvent(unsigned)

      setStatus('Uploading…')
      const form = new FormData()
      form.append('file', f)

      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { Authorization: `Nostr ${btoa(JSON.stringify(signed))}` },
        body: form,
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(body.detail ?? res.statusText)
      }

      setSuccess(true)
      setStatus('')
      setTimeout(props.onSuccess, 800)
    } catch (e) {
      setError((e as Error).message)
      setStatus('')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div class="modal-overlay" onClick={(e) => e.target === e.currentTarget && props.onClose()}>
      <div class="modal">
        <h2>Upload Meme</h2>

        <label
          class={`drop-zone${dragging() ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <input type="file" accept="image/*,video/*" onChange={onInputChange} />
          <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <div>Drop file here or click to browse</div>
          <p>Images & videos up to 50 MB</p>
          {file() && <div class="file-name">{(file() as File).name}</div>}
        </label>

        {!window.nostr && (
          <p class="nostr-warning">
            Requires a Nostr browser extension to sign uploads.{' '}
            <a href="https://getalby.com" target="_blank" rel="noreferrer">Alby</a>{' '}
            or{' '}
            <a href="https://github.com/fiatjaf/nos2x" target="_blank" rel="noreferrer">nos2x</a>.
          </p>
        )}

        {error() && <div class="modal-error">{error()}</div>}
        {success() && <div class="modal-success">Uploaded!</div>}
        {status() && <div class="status-text">{status()}</div>}

        <div class="modal-actions">
          <button
            class="btn-primary"
            onClick={upload}
            disabled={!file() || uploading()}
          >
            {uploading() ? 'Uploading…' : 'Upload'}
          </button>
          <button class="btn-secondary" onClick={props.onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
