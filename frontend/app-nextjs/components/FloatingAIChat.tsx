"use client";

import Link from "next/link";
import { MessageSquare } from "lucide-react";

export function FloatingAIChat() {
  return (
    <Link
      href="/fan/ai"
      className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg shadow-brand/40 transition-transform hover:scale-110 active:scale-95"
      aria-label="Ask AI"
    >
      <MessageSquare size={26} />
    </Link>
  );
}
