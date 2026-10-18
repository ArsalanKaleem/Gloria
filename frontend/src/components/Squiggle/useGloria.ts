'use client';

import { useCallback, useState } from 'react';
import type { Message, Source } from './types';

function uid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export function useGloria() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setError(null);

    const userMsg: Message = {
      id: uid(),
      role: 'user',
      text,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setBusy(true);

    try {
      const res = await fetch('/api/gloria', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      const botMsg: Message = {
        id: uid(),
        role: 'assistant',
        text: data.answer ?? '',
        sources: (data.sources ?? []) as Source[],
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      setError((e as Error).message ?? 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, busy, error, send, reset };
}
