'use client';

import { useEffect, useRef } from 'react';
import type { Message } from './types';
import MessageBubble from './Message';
import TypingIndicator from './TypingIndicator';

export default function MessageList({
  messages,
  busy,
}: {
  messages: Message[];
  busy: boolean;
}) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  return (
    <div className="px-3 py-3 space-y-3">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      {busy && <TypingIndicator />}
      <div ref={endRef} />
    </div>
  );
}
