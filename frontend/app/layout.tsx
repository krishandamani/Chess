import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Repertoire — Train the mistakes you actually make",
  description:
    "Analyze all your Chess.com and Lichess games. Find recurring patterns. Fix them.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className={`${inter.className} min-h-full flex flex-col bg-slate-50 text-slate-900`}>
        {children}
      </body>
    </html>
  );
}
