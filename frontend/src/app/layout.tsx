import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { PWAProvider } from "@/components/pwa-provider";
import { StructuredData } from "@/components/structured-data";
import { generateWebAppStructuredData } from "@/lib/structured-data";
import { SentryProvider } from "@/components/sentry-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "GameChat AI - ゲーム攻略AIアシスタント",
    template: "%s | GameChat AI"
  },
  description: "AIを活用したゲーム攻略支援サービス。ゲームの質問に素早く正確に回答します。",
  keywords: ["ゲーム", "攻略", "AI", "アシスタント", "ポケモンカード", "チャットボット"],
  authors: [{ name: "GameChat AI Team" }],
  creator: "GameChat AI",
  publisher: "GameChat AI",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: "GameChat AI - ゲーム攻略AIアシスタント",
    description: "AIを活用したゲーム攻略支援サービス。ゲームの質問に素早く正確に回答します。",
    url: "/",
    siteName: "GameChat AI",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "GameChat AI - ゲーム攻略AIアシスタント",
      },
    ],
    locale: "ja_JP",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "GameChat AI - ゲーム攻略AIアシスタント",
    description: "AIを活用したゲーム攻略支援サービス。ゲームの質問に素早く正確に回答します。",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const structuredData = generateWebAppStructuredData();

  return (
    <html lang="ja">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        {process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY && (
          <script 
            src={`https://www.google.com/recaptcha/api.js?render=${process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}`}
            async
            defer
          />
        )}
        <StructuredData data={structuredData} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SentryProvider>
          <PWAProvider>
            {children}
          </PWAProvider>
        </SentryProvider>
      </body>
    </html>
  );
}
