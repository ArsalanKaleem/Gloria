'use client';

import { useState } from 'react';
import ChatWindow from './ChatWindow';

export default function Squiggle() {
  const [open, setOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {open && (
        <div className="mb-3">
          <ChatWindow onClose={() => setOpen(false)} />
        </div>
      )}
      <button
        aria-label={open ? 'Close Gloria' : 'Open Gloria'}
        onClick={() => setOpen((o) => !o)}
        className="w-14 h-14 rounded-full shadow-xl bg-gloria-primary text-white text-2xl grid place-items-center hover:scale-105 transition"
      >
        {open ? '\u00d7' : '\u2728'}
      </button>
    </div>
  );
}
