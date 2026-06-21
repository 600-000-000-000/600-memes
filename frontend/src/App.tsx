import { createSignal, onMount, onCleanup, Show } from 'solid-js'
import type { MemeItem } from './types'
import MemeGrid from './components/MemeGrid'
import MemeDetail from './components/MemeDetail'
import UploadModal from './components/UploadModal'

export default function App() {
  const [memes, setMemes] = createSignal<MemeItem[]>([])
  const [showUpload, setShowUpload] = createSignal(false)
  const [error, setError] = createSignal<string | null>(null)
  const [selectedFilename, setSelectedFilename] = createSignal<string | null>(null)

  const selectedMeme = () =>
    memes().find((m) => m.filename === selectedFilename()) ?? null

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
            memes.600.wtf
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
        <Show when={memes().length === 0} fallback={
          <MemeGrid memes={memes()} onSelect={openMeme} />
        }>
          <div class="empty">no memes yet. be the first.</div>
        </Show>
      }>
        {(meme) => <MemeDetail meme={meme()} onBack={closeMeme} />}
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
