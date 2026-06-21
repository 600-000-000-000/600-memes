import { createSignal, Show } from 'solid-js'
import type { MemeItem } from '../types'

interface Props {
  meme: MemeItem
  onBack: () => void
}

export default function MemeDetail(props: Props) {
  const [copied, setCopied] = createSignal(false)

  function shareUrl() {
    return `${location.origin}/#${props.meme.filename}`
  }

  async function copyLink() {
    await navigator.clipboard.writeText(shareUrl())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
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
        </div>
      </div>
    </div>
  )
}
