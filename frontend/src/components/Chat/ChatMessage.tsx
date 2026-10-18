'use client';

import { useState } from 'react';
import type { Message, Source } from '../Squiggle/types';
import Markdown from './Markdown';
import { GloriaAvatar } from './Icons';

/** One chip per distinct document: chunks of the same file share a title. */
function distinctSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sources.filter((s) => {
    const key = s.title || s.source_url || '';
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export default function ChatMessage({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false);

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-3xl bg-neutral-100 px-5 py-2.5 leading-7 text-neutral-900">
          {message.text}
        </div>
      </div>
    );
  }

  const sources = distinctSources(message.sources ?? []);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked (e.g. insecure context): nothing to do.
    }
  };

  return (
    <div className="flex gap-4">
      <GloriaAvatar className="mt-0.5 h-8 w-8 shrink-0" />
      <div className="min-w-0 flex-1 text-neutral-900">
        <Markdown text={message.text} />
        {sources.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {sources.map((s, i) =>
              s.source_url ? (
                <a
                  key={i}
                  href={s.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full border border-neutral-200 px-3 py-1 text-xs text-neutral-600 hover:border-gloria-primary hover:text-gloria-primary"
                >
                  {s.title || 'Source'}
                </a>
              ) : (
                <span key={i} className="rounded-full border border-neutral-200 px-3 py-1 text-xs text-neutral-600">
                  {s.title || 'Source'}
                </span>
              ),
            )}
          </div>
        )}
        <button
          onClick={copy}
          className="mt-2 rounded-md px-2 py-1 text-xs text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700"
          aria-label="Copy answer"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  );
}
