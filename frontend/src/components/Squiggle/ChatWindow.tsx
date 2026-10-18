'use client';

import { useGloria } from './useGloria';
import MessageList from './MessageList';
import Composer from './Composer';
import { site } from '@/config';

export default function ChatWindow({ onClose }: { onClose: () => void }) {
  const { messages, busy, error, send, reset } = useGloria();

  return (
    <div
      className="w-[360px] max-w-[92vw] max-h-[70vh] rounded-2xl bg-white shadow-2xl flex flex-col overflow-hidden border"
      role="dialog"
      aria-label="Gloria chat"
    >
      <header className="bg-gloria-primary text-white px-4 py-3 flex items-center justify-between">
        <div>
          <div className="font-bold flex items-center gap-1">
            Gloria <span aria-hidden>{'\u2728'}</span>
          </div>
          <div className="text-xs opacity-80">{site.universityName}</div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <button
            onClick={reset}
            className="opacity-80 hover:opacity-100"
            aria-label="New conversation"
            title="New conversation"
          >
            New
          </button>
          <button
            onClick={onClose}
            className="text-xl leading-none opacity-80 hover:opacity-100"
            aria-label="Close"
          >
            {'\u00d7'}
          </button>
        </div>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="p-4 text-sm text-neutral-600">
            <p>How can I help you?</p>
            <div className="mt-3 flex flex-col gap-2">
              {site.suggestions.map((s) => (
                <button
                  key={s.prompt}
                  onClick={() => send(s.prompt)}
                  className="text-left rounded-lg border px-3 py-2 hover:bg-neutral-50"
                >
                  {s.prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <MessageList messages={messages} busy={busy} />
        )}
      </div>

      {error && (
        <div className="px-4 py-2 text-red-600 text-sm border-t">
          {error}
        </div>
      )}

      <Composer disabled={busy} onSend={send} />
    </div>
  );
}
