'use client';

import { useState, KeyboardEvent } from 'react';

export default function Composer({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (t: string) => void;
}) {
  const [text, setText] = useState('');

  const submit = () => {
    const t = text.trim();
    if (!t || disabled) return;
    onSend(t);
    setText('');
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // guard against IME composition
    // @ts-ignore - isComposing is on the native event
    if (e.nativeEvent?.isComposing) return;
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t px-3 py-2 flex gap-2 bg-white">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        disabled={disabled}
        placeholder="Ask Gloria..."
        className="flex-1 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gloria-primary/30"
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="bg-gloria-primary text-white px-3 rounded-lg text-sm disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
