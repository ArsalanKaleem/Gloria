import type { Source } from './types';

export default function Sources({ items }: { items: Source[] }) {
  if (!items?.length) return null;
  return (
    <div className="mt-2 space-y-1">
      <div className="text-xs font-semibold text-neutral-600">Sources</div>
      {items.map((s, i) => (
        <div
          key={i}
          className="text-xs border rounded-md px-2 py-1 bg-white text-neutral-800"
        >
          {s.source_url ? (
            <a
              href={s.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-gloria-primary underline"
            >
              {s.title || 'Source'}
            </a>
          ) : (
            <span>{s.title || 'Source'}</span>
          )}
          {s.page ? (
            <span className="text-neutral-500">, p.{s.page}</span>
          ) : null}
          {s.organization ? (
            <span className="ml-1 text-neutral-500">({s.organization})</span>
          ) : null}
        </div>
      ))}
    </div>
  );
}
