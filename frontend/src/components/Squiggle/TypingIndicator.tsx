'use client';

export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl bg-neutral-100 px-3 py-2 text-sm text-neutral-500">
        <span className="inline-flex gap-1 items-center">
          Gloria is thinking
          <span className="inline-flex gap-0.5">
            <span className="w-1 h-1 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1 h-1 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1 h-1 rounded-full bg-neutral-400 animate-bounce" />
          </span>
        </span>
      </div>
    </div>
  );
}
