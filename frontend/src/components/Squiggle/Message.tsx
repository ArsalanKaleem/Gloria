'use client';

import type { Message } from './types';
import Sources from './Sources';

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={
          isUser
            ? 'max-w-[85%] rounded-2xl bg-gloria-primary text-white px-3 py-2 text-sm'
            : 'max-w-[92%] rounded-2xl bg-neutral-100 text-neutral-900 px-3 py-2 text-sm'
        }
      >
        <div className="whitespace-pre-wrap leading-relaxed">{message.text}</div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <Sources items={message.sources} />
        )}
      </div>
    </div>
  );
}
