"use client";

/** AI assistant chat: suggestion chips + free text, answered by the backend. */

import { useState } from "react";
import { api, type Recommendation } from "@/lib/api";

interface Msg { role: "me" | "ai"; text: string }

// Map a suggestion label to a backend intent + params.
const SUGGESTIONS: { label: string; intent: string; params: Record<string, unknown> }[] = [
  { label: "Where is my seat?", intent: "navigate", params: { origin: "gate_1", destination: "stand_n" } },
  { label: "Least crowded gate", intent: "navigate", params: { origin: "gate_1", destination: "stand_s" } },
  { label: "Wheelchair route", intent: "wheelchair_route", params: { origin: "gate_1", destination: "med_1" } },
  { label: "Best exit", intent: "best_exit", params: {} },
];

export default function FanAI() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");

  async function send(label: string, intent: string, params: Record<string, unknown>) {
    setMessages((m) => [...m, { role: "me", text: label }]);
    try {
      const rec: Recommendation = await api.query(intent, params);
      setMessages((m) => [...m, { role: "ai", text: `${rec.title}. ${rec.explanation}` }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "I couldn't reach the assistant. Is the backend running?" }]);
    }
  }

  return (
    <div className="max-w-2xl mx-auto rounded-xl border border-slate-200 bg-white p-4">
      <div className="rounded-xl p-4 text-white bg-gradient-to-br from-navy to-brand">
        <div className="text-lg font-extrabold">How can I help?</div>
        <div className="text-sm opacity-80">Tap a suggestion or type a question</div>
      </div>

      <div className="flex flex-wrap gap-2 my-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => send(s.label, s.intent, s.params)}
            className="rounded-full bg-brand-soft text-brand px-3 py-1.5 text-sm font-semibold"
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="space-y-2 min-h-[160px]">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "me" ? "justify-end" : ""}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${
                m.role === "me" ? "bg-brand text-white" : "bg-slate-100"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <form
        className="flex gap-2 mt-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (!input.trim()) return;
          // Free-text falls back to a navigation intent to the nearest stand.
          send(input, "navigate", { origin: "gate_1", destination: "stand_n" });
          setInput("");
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about seats, food, exits…"
          className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm"
        />
        <button className="rounded-lg bg-brand text-white px-4 py-2 text-sm font-semibold">Send</button>
      </form>
    </div>
  );
}
