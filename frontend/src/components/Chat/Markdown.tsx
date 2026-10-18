import { Fragment, type ReactNode } from 'react';

/**
 * Minimal Markdown for Gloria's answers: paragraphs, bullet and numbered
 * lists, **bold**, and clickable URLs / emails. Builds React elements
 * directly (no innerHTML), so model output can never inject markup.
 */

const INLINE_RX = /(\*\*[^*]+\*\*|https?:\/\/[^\s)]+|www\.[^\s)]+|[\w.+-]+@[\w-]+\.[\w.]+)/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE_RX).map((part, i) => {
    if (!part) return null;
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (/^(https?:\/\/|www\.)/.test(part)) {
      const href = part.startsWith('www.') ? `https://${part}` : part;
      return (
        <a key={i} href={href} target="_blank" rel="noreferrer" className="text-gloria-primary underline underline-offset-2">
          {part}
        </a>
      );
    }
    if (/^[\w.+-]+@[\w-]+\.[\w.]+$/.test(part)) {
      const email = part.replace(/\.$/, '');
      return (
        <a key={i} href={`mailto:${email}`} className="text-gloria-primary underline underline-offset-2">
          {part}
        </a>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export default function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r/g, '').split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    const bullet = /^\s*[-*•]\s+/;
    const numbered = /^\s*\d+[.)]\s+/;
    if (bullet.test(line) || numbered.test(line)) {
      const ordered = numbered.test(line);
      const rx = ordered ? numbered : bullet;
      const items: string[] = [];
      while (i < lines.length && rx.test(lines[i])) {
        items.push(lines[i].replace(rx, ''));
        i++;
      }
      const List = ordered ? 'ol' : 'ul';
      blocks.push(
        <List key={blocks.length} className={`${ordered ? 'list-decimal' : 'list-disc'} space-y-1 pl-6`}>
          {items.map((item, j) => (
            <li key={j}>{inline(item)}</li>
          ))}
        </List>,
      );
      continue;
    }
    const para: string[] = [];
    while (i < lines.length && lines[i].trim() && !bullet.test(lines[i]) && !numbered.test(lines[i])) {
      para.push(lines[i]);
      i++;
    }
    blocks.push(<p key={blocks.length}>{inline(para.join(' '))}</p>);
  }

  return <div className="space-y-3 leading-7">{blocks}</div>;
}
