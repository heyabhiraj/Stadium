import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { FloatingAIChat } from "@/features/ai/FloatingAIChat";

export const metadata: Metadata = {
  title: "StadiumMind AI",
  description: "GenAI operating system for FIFA World Cup 2026 stadiums",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <header className="max-w-6xl mx-auto flex items-center justify-between p-4">
          <div className="flex items-center gap-2 font-bold text-lg">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth={2}>
              <ellipse cx="12" cy="12" rx="9" ry="6" />
              <circle cx="12" cy="12" r="1.5" fill="#2563eb" />
            </svg>
            StadiumMind <span className="text-brand">AI</span>
          </div>
          <nav className="flex gap-2 text-sm font-semibold">
            <Link href="/" className="px-4 py-2 rounded-full hover:bg-white">Home</Link>
            <Link href="/fan" className="px-4 py-2 rounded-full hover:bg-white">Fan App</Link>
            <Link href="/ops" className="px-4 py-2 rounded-full hover:bg-white">Operations</Link>
          </nav>
        </header>
        <main className="max-w-6xl mx-auto p-4">{children}</main>
        <FloatingAIChat />
      </body>
    </html>
  );
}
