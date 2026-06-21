export interface MemeItem {
  filename: string
  url: string
  uploaded_at: string
  uploader_pubkey: string
  uploader_name?: string
  uploader_avatar?: string
  mime_type: string
}

export interface NostrEvent {
  id: string
  pubkey: string
  created_at: number
  kind: number
  tags: string[][]
  content: string
  sig: string
}

declare global {
  interface Window {
    nostr?: {
      getPublicKey(): Promise<string>
      signEvent(event: Omit<NostrEvent, 'id' | 'sig' | 'pubkey'>): Promise<NostrEvent>
    }
  }
}
