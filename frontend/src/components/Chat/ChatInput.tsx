'use client';

import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { SendIcon } from './Icons';

export default function ChatInput({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState('');
  const ref = useRef<HTMLTextAreaElement | null>(null);

  // Grow with the content, up to about eight lines.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!text) {
      // Empty: let rows={1} size it. (Measuring on first load can run
      // before layout settles and lock in an oversized height.)
      el.style.height = '';
      return;
    }
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [text]);

  const submit = () => {
    const t = text.trim();
    if (!t || disabled) return;
    onSend(t);
    setText('');
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.nativeEvent.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex items-end gap-2 rounded-3xl border border-neutral-200 bg-white p-2 pl-5 shadow-sm focus-within:border-neutral-300 focus-within:shadow-md">
      <textarea
        ref={ref}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Ask Gloria about admissions, fees, programs..."
        aria-label="Message Gloria"
        className="max-h-[200px] flex-1 resize-none bg-transparent py-2 leading-6 text-neutral-900 placeholder:text-neutral-400 focus:outline-none"
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        aria-label="Send message"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gloria-primary text-white transition hover:opacity-90 disabled:bg-neutral-300"
      >
        <SendIcon className="h-4 w-4" />
      </button>
    </div>
  );
}
