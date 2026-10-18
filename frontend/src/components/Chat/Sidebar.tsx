'use client';

import { site } from '@/config';
import type { Conversation } from './useConversations';
import { GloriaAvatar, PlusIcon, TrashIcon } from './Icons';

export default function Sidebar({
  conversations,
  activeId,
  onNew,
  onSelect,
  onDelete,
  open,
  onClose,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      {/* Dimmed backdrop on small screens while the sidebar is open. */}
      {open && <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onClose} aria-hidden />}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-neutral-950 text-neutral-200 transition-transform md:static md:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-4 pb-2 pt-4">
          <GloriaAvatar className="h-8 w-8" />
          <div className="min-w-0">
            <div className="font-semibold text-white">Gloria</div>
            <div className="truncate text-xs text-neutral-400">{site.universityName}</div>
          </div>
        </div>

        <div className="px-3 py-2">
          <button
            onClick={() => {
              onNew();
              onClose();
            }}
            className="flex w-full items-center gap-2 rounded-lg border border-neutral-800 px-3 py-2 text-sm hover:bg-neutral-900"
          >
            <PlusIcon className="h-4 w-4" />
            New chat
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-2" aria-label="Chat history">
          {conversations.length > 0 && (
            <div className="px-2 pb-1 text-xs font-medium text-neutral-500">Recent</div>
          )}
          <ul className="space-y-0.5">
            {conversations.map((c) => (
              <li key={c.id} className="group relative">
                <button
                  onClick={() => {
                    onSelect(c.id);
                    onClose();
                  }}
                  className={`w-full truncate rounded-lg px-3 py-2 pr-9 text-left text-sm ${
                    c.id === activeId ? 'bg-neutral-800 text-white' : 'hover:bg-neutral-900'
                  }`}
                  title={c.title}
                >
                  {c.title}
                </button>
                <button
                  onClick={() => onDelete(c.id)}
                  className="absolute right-1.5 top-1/2 hidden -translate-y-1/2 rounded p-1 text-neutral-500 hover:text-red-400 group-hover:block"
                  aria-label={`Delete chat: ${c.title}`}
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="border-t border-neutral-800 px-4 py-4">
          <div className="text-xs text-neutral-500">Built by</div>
          <a
            href={site.creatorUrl}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-semibold tracking-wide text-white hover:underline"
          >
            {site.creator.toUpperCase()}
          </a>
        </div>
      </aside>
    </>
  );
}
