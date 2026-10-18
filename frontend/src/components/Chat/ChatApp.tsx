'use client';

import { useEffect, useRef, useState } from 'react';
import { site } from '@/config';
import { useConversations } from './useConversations';
import Sidebar from './Sidebar';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { GloriaAvatar, MenuIcon, PlusIcon } from './Icons';

/** Full-screen, ChatGPT-style Gloria app. */
export default function ChatApp() {
  const { conversations, active, busy, error, send, newChat, select, remove } = useConversations();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);
  const messages = active?.messages ?? [];

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, busy]);

  return (
    <div className="flex h-dvh overflow-hidden bg-white">
      <Sidebar
        conversations={conversations}
        activeId={active?.id ?? null}
        onNew={newChat}
        onSelect={select}
        onDelete={remove}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {/* Top bar on small screens. */}
        <header className="flex items-center justify-between border-b px-3 py-2 md:hidden">
          <button onClick={() => setSidebarOpen(true)} className="rounded-lg p-2 hover:bg-neutral-100" aria-label="Open chat history">
            <MenuIcon className="h-5 w-5" />
          </button>
          <div className="font-semibold">Gloria</div>
          <button onClick={newChat} className="rounded-lg p-2 hover:bg-neutral-100" aria-label="New chat">
            <PlusIcon className="h-5 w-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-10 text-center">
              <GloriaAvatar className="h-14 w-14" />
              <h1 className="mt-5 text-3xl font-semibold text-neutral-900">How can I help you today?</h1>
              <p className="mt-2 text-neutral-500">
                Ask me anything about {site.universityName}: admissions, fees, programs, rules and contacts.
              </p>
              <div className="mt-8 grid w-full gap-3 sm:grid-cols-2">
                {site.suggestions.map((s) => (
                  <button
                    key={s.prompt}
                    onClick={() => send(s.prompt)}
                    className="rounded-2xl border border-neutral-200 p-4 text-left transition hover:border-gloria-primary/40 hover:bg-neutral-50"
                  >
                    <div className="text-sm font-medium text-neutral-900">{s.title}</div>
                    <div className="mt-1 text-sm text-neutral-500">{s.prompt}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
              {busy && (
                <div className="flex items-center gap-4" aria-live="polite">
                  <GloriaAvatar className="h-8 w-8 shrink-0" />
                  <span className="inline-flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400 [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400 [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400" />
                  </span>
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="mx-auto w-full max-w-3xl px-4 pb-4">
          {error && (
            <div className="mb-2 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
              {error}
            </div>
          )}
          <ChatInput disabled={busy} onSend={send} />
          <p className="mt-2 text-center text-xs text-neutral-400">
            Gloria answers from official university information and can still make mistakes.
            Check important details with the university. Built by {site.creator}.
          </p>
        </div>
      </main>
    </div>
  );
}
