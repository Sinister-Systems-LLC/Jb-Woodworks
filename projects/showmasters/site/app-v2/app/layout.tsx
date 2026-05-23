/* Author: RKOJ-ELENO :: 2026-05-23 */
import type { Metadata, Viewport } from 'next';
import { Inter, DM_Serif_Display } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',
});
const dmSerif = DM_Serif_Display({
  subsets: ['latin'],
  weight: ['400'],
  style: ['normal', 'italic'],
  display: 'swap',
  variable: '--font-dm-serif',
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'https://showmasters.com'),
  title: {
    default: 'Show Masters Production Logistics | Live Event Stagehands, Riggers & Crew | Orlando & Dallas',
    template: '%s | Show Masters Production Logistics',
  },
  description:
    'Stagehands, riggers, technicians and crew leads for live events since 2002. Two offices, eight operational hubs, 33 states crewed.',
  openGraph: {
    type: 'website',
    siteName: 'Show Masters Production Logistics',
    images: ['/public/img/og-card.svg'],
  },
  twitter: { card: 'summary_large_image' },
  icons: {
    icon: '/public/img/favicon.svg',
    apple: '/public/img/pfp-square.svg',
  },
  manifest: '/manifest.json',
};

export const viewport: Viewport = {
  themeColor: '#0A0A0F',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${dmSerif.variable} dark`}>
      <body>{children}</body>
    </html>
  );
}
