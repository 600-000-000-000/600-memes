import { createSignal, onMount, Show } from 'solid-js'
import type { MemeItem } from '../types'

const DNI_PUBKEY = '1c94c0b44577edf41509d473a92d9f7b6bc04e3ae07f705e709c2999b1d3e074'

interface Props {
  meme: MemeItem
  onBack: () => void
  onDelete: () => void
}

export default function MemeDetail(props: Props) {
  const [copied, setCopied] = createSignal(false)
  const [myPubkey, setMyPubkey] = createSignal<string | null>(null)
  const [deleting, setDeleting] = createSignal(false)
  const [deleteError, setDeleteError] = createSignal('')

  onMount(async () => {
    if (window.nostr) {
      try { setMyPubkey(await window.nostr.getPublicKey()) } catch {}
    }
  })

  const canDelete = () => {
    const pk = myPubkey()
    return !!pk && (pk === props.meme.uploader_pubkey || pk === DNI_PUBKEY)
  }

  function shareUrl() {
    return `${location.origin}/#${props.meme.filename}`
  }

  async function copyLink() {
    await navigator.clipboard.writeText(shareUrl())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  async function deleteMeme() {
    if (!window.nostr) return
    setDeleting(true)
    setDeleteError('')
    try {
      const url = `${location.origin}/api/memes/${props.meme.filename}`
      const unsigned = {
        kind: 27235,
        created_at: Math.floor(Date.now() / 1000),
        tags: [
          ['u', url],
          ['method', 'DELETE'],
        ],
        content: '',
      }
      const signed = await window.nostr.signEvent(unsigned)
      const res = await fetch(`/api/memes/${props.meme.filename}`, {
        method: 'DELETE',
        headers: { Authorization: `Nostr ${btoa(JSON.stringify(signed))}` },
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(body.detail ?? res.statusText)
      }
      props.onDelete()
    } catch (e) {
      setDeleteError((e as Error).message)
      setDeleting(false)
    }
  }

  const isVideo = () => props.meme.mime_type.startsWith('video/')
  const date = () => new Date(props.meme.uploaded_at).toLocaleString()

  return (
    <div class="detail">
      <button class="btn-back" onClick={props.onBack}>← back</button>

      <div class="detail-media">
        {isVideo() ? (
          <video src={props.meme.url} controls loop autoplay playsinline />
        ) : (
          <img src={props.meme.url} alt={props.meme.filename} />
        )}
      </div>

      <div class="detail-meta">
        <div class="detail-uploader">
          <Show when={props.meme.uploader_avatar}>
            <img class="avatar-md" src={props.meme.uploader_avatar} alt="" />
          </Show>
          <div class="detail-uploader-info">
            <div class="detail-uploader-name">
              {props.meme.uploader_name ? `@${props.meme.uploader_name}` : 'unknown'}
            </div>
            <div class="detail-pubkey">{props.meme.uploader_pubkey}</div>
          </div>
        </div>

        <div class="detail-row">
          <span class="detail-label">date</span>
          <span class="detail-value">{date()}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">file</span>
          <span class="detail-value detail-pubkey">{props.meme.filename}</span>
        </div>

        <div class="detail-actions">
          <button class="btn-share" onClick={copyLink}>
            {copied() ? '✓ copied' : 'copy link'}
          </button>
          <a class="btn-open" href={props.meme.url} target="_blank" rel="noreferrer">
            open original
          </a>
          <Show when={canDelete()}>
            <button class="btn-delete" onClick={deleteMeme} disabled={deleting()}>
              {deleting() ? 'deleting…' : 'delete'}
            </button>
          </Show>
        </div>

        <Show when={deleteError()}>
          <div class="delete-error">{deleteError()}</div>
        </Show>
      </div>
    </div>
  )
}
