import { createSignal, createMemo, onMount, onCleanup, Show, For } from 'solid-js'
import type { MemeItem } from './types'
import MemeGrid from './components/MemeGrid'
import MemeDetail from './components/MemeDetail'
import UploadModal from './components/UploadModal'

export default function App() {
  const [memes, setMemes] = createSignal<MemeItem[]>([])
  const [showUpload, setShowUpload] = createSignal(false)
  const [error, setError] = createSignal<string | null>(null)
  const [selectedFilename, setSelectedFilename] = createSignal<string | null>(null)
  const [filterPubkey, setFilterPubkey] = createSignal<string | null>(null)

  const selectedMeme = () =>
    memes().find((m) => m.filename === selectedFilename()) ?? null

  const uploaders = createMemo(() => {
    const seen = new Set<string>()
    const list: { pubkey: string; name?: string; avatar?: string }[] = []
    for (const m of memes()) {
      if (!seen.has(m.uploader_pubkey)) {
        seen.add(m.uploader_pubkey)
        list.push({ pubkey: m.uploader_pubkey, name: m.uploader_name, avatar: m.uploader_avatar })
      }
    }
    return list
  })

  const visibleMemes = createMemo(() => {
    const pk = filterPubkey()
    return pk ? memes().filter((m) => m.uploader_pubkey === pk) : memes()
  })

  function readHash() {
    const h = location.hash.slice(1)
    setSelectedFilename(h || null)
  }

  const fetchMemes = async () => {
    try {
      const res = await fetch('/api/memes')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setMemes(await res.json())
    } catch (e) {
      setError((e as Error).message)
    }
  }

  onMount(() => {
    fetchMemes()
    readHash()
    window.addEventListener('hashchange', readHash)
  })

  onCleanup(() => window.removeEventListener('hashchange', readHash))

  function openMeme(m: MemeItem) {
    location.hash = m.filename
  }

  function closeMeme() {
    history.pushState(null, '', location.pathname)
    setSelectedFilename(null)
  }

  return (
    <div class="app">
      <header>
        <h1>
          <a href="/" onClick={(e) => { e.preventDefault(); closeMeme() }}>
            600 000 000 000 memes
          </a>
        </h1>
        <button class="btn-upload" onClick={() => setShowUpload(true)}>
          + Upload
        </button>
      </header>

      <Show when={error()}>
        <div class="error-bar">{error()}</div>
      </Show>

      <Show when={selectedMeme()} fallback={
        <>
          <Show when={uploaders().length > 1}>
            <div class="filter-bar">
              <button
                class={`filter-chip${filterPubkey() === null ? ' active' : ''}`}
                onClick={() => setFilterPubkey(null)}
              >
                all
              </button>
              <For each={uploaders()}>
                {(u) => (
                  <button
                    class={`filter-chip${filterPubkey() === u.pubkey ? ' active' : ''}`}
                    onClick={() => setFilterPubkey(filterPubkey() === u.pubkey ? null : u.pubkey)}
                  >
                    <Show when={u.avatar}>
                      <img class="avatar-xs" src={u.avatar} alt="" />
                    </Show>
                    {u.name ? `@${u.name}` : u.pubkey.slice(0, 8) + '…'}
                  </button>
                )}
              </For>
            </div>
          </Show>
          <Show when={visibleMemes().length === 0} fallback={
            <MemeGrid memes={visibleMemes()} onSelect={openMeme} />
          }>
            <div class="empty">
              {memes().length === 0 ? 'no memes yet. be the first.' : 'no memes from this member.'}
            </div>
          </Show>
        </>
      }>
        {(meme) => <MemeDetail meme={meme()} onBack={closeMeme} onDelete={() => { closeMeme(); fetchMemes() }} />}
      </Show>

      <Show when={showUpload()}>
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            setShowUpload(false)
            fetchMemes()
          }}
        />
      </Show>
    </div>
  )
}
