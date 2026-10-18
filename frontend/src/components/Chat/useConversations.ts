'use client';

import { useCallback, useEffect, useState } from 'react';
import type { Message, Source } from '../Squiggle/types';

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

const STORAGE_KEY = 'gloria.conversations.v1';
const MAX_STORED = 50;

function uid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

function load(): Conversation[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Conversation[]) : [];
  } catch {
    return [];
  }
}

function save(conversations: Conversation[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, MAX_STORED)));
  } catch {
    // Storage full or blocked (private mode): the chat still works, it just isn't remembered.
  }
}

function titleFrom(text: string): string {
  const t = text.trim().replace(/\s+/g, ' ');
  return t.length > 48 ? `${t.slice(0, 45)}...` : t;
}

/** Chat history kept in the browser, plus sending messages to Gloria. */
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setConversations(load());
  }, []);

  const update = useCallback((fn: (prev: Conversation[]) => Conversation[]) => {
    setConversations((prev) => {
      const next = fn(prev).sort((a, b) => b.updatedAt - a.updatedAt);
      save(next);
      return next;
    });
  }, []);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  const newChat = useCallback(() => {
    setActiveId(null);
    setError(null);
  }, []);

  const select = useCallback((id: string) => {
    setActiveId(id);
    setError(null);
  }, []);

  const remove = useCallback(
    (id: string) => {
      update((prev) => prev.filter((c) => c.id !== id));
      setActiveId((cur) => (cur === id ? null : cur));
    },
    [update],
  );

  const append = useCallback(
    (convId: string, message: Message) => {
      update((prev) =>
        prev.map((c) =>
          c.id === convId
            ? { ...c, messages: [...c.messages, message], updatedAt: Date.now() }
            : c,
        ),
      );
    },
    [update],
  );

  const send = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || busy) return;
      setError(null);

      const userMsg: Message = { id: uid(), role: 'user', text: question, createdAt: Date.now() };
      let convId = activeId;
      if (!convId) {
        convId = uid();
        const conv: Conversation = {
          id: convId,
          title: titleFrom(question),
          messages: [userMsg],
          updatedAt: Date.now(),
        };
        update((prev) => [conv, ...prev]);
        setActiveId(convId);
      } else {
        append(convId, userMsg);
      }

      setBusy(true);
      try {
        const res = await fetch('/api/gloria', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: question, conversation_id: convId }),
        });
        if (!res.ok) {
          throw new Error(
            res.status === 401
              ? 'The chat service is not authorised. Check the Gloria API key.'
              : `Gloria could not answer right now (error ${res.status}).`,
          );
        }
        const data = await res.json();
        append(convId, {
          id: uid(),
          role: 'assistant',
          text: data.answer ?? '',
          sources: (data.sources ?? []) as Source[],
          createdAt: Date.now(),
        });
      } catch (e) {
        setError((e as Error).message || 'Something went wrong.');
      } finally {
        setBusy(false);
      }
    },
    [activeId, append, busy, update],
  );

  return { conversations, active, busy, error, send, newChat, select, remove };
}
