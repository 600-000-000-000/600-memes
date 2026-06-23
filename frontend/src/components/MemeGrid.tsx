import { For, Show } from 'solid-js'
import type { MemeItem } from '../types'

interface Props {
  memes: MemeItem[]
  onSelect: (m: MemeItem) => void
}

function thumbUrl(filename: string, mimeType: string) {
  const stem = filename.replace(/\.[^.]+$/, '')
  const ext = mimeType === 'image/gif' ? 'gif' : 'jpg'
  return `/uploads/${stem}_thumb.${ext}`
}

export default function MemeGrid(props: Props) {
  return (
    <div class="meme-grid">
      <For each={props.memes}>
        {(meme) => (
          <div class="meme-card" onClick={() => props.onSelect(meme)}>
            <div class="meme-thumb">
              <img src={thumbUrl(meme.filename, meme.mime_type)} alt={meme.filename} loading="lazy" />
              <Show when={meme.mime_type.startsWith('video/')}>
                <div class="play-badge">▶</div>
              </Show>
            </div>
            <div class="meme-meta">
              <span class="meme-uploader">
                <Show when={meme.uploader_avatar}>
                  <img class="avatar-xs" src={meme.uploader_avatar} alt="" />
                </Show>
                <span title={meme.uploader_pubkey}>
                  {meme.uploader_name ? `@${meme.uploader_name}` : meme.uploader_pubkey.slice(0, 8) + '…'}
                </span>
              </span>
              <span>{new Date(meme.uploaded_at).toLocaleDateString()}</span>
            </div>
          </div>
        )}
      </For>
    </div>
  )
}
