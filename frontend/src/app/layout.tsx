import type { Metadata, Viewport } from 'next';
import './globals.css';
import { site } from '@/config';

export const metadata: Metadata = {
  title: `Gloria · ${site.universityName}`,
  description: `Ask Gloria about ${site.universityName}: admissions, fees, programs, rules and contacts. Built by ${site.creator}.`,
  authors: [{ name: site.creator, url: site.creatorUrl }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

// The full-screen chat lives on the home page. To embed Gloria on another
// site as a floating button instead, render <Squiggle /> from
// '@/components/Squiggle/Squiggle' in that site's layout.
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-white font-sans text-neutral-900 antialiased">{children}</body>
    </html>
  );
}
