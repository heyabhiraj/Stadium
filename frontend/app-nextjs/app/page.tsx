"use client";

import { useRouter } from "next/navigation";
import { LayoutDashboard, Map as MapIcon, Smartphone } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();

  const cards = [
    { 
      icon: Smartphone, 
      title: "Fan Experience", 
      desc: "Navigate, find food, and chat with AI", 
      href: "/fan",
      gradient: "from-blue-500 to-cyan-400"
    },
    { 
      icon: MapIcon, 
      title: "Live Stadium Map", 
      desc: "Interactive 3D zones and crowd heatmaps", 
      href: "/fan/map",
      gradient: "from-purple-500 to-pink-500"
    },
    { 
      icon: LayoutDashboard, 
      title: "Operations Dashboard", 
      desc: "Real-time AI insights for venue staff", 
      href: "/ops",
      gradient: "from-emerald-500 to-teal-400"
    },
  ];

  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background glowing orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
      
      <div className="z-10 text-center mb-12">
        <div className="inline-flex items-center justify-center gap-3 font-extrabold text-4xl tracking-tight mb-4 text-slate-900">
          <svg width={36} height={36} viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth={2}>
            <ellipse cx="12" cy="12" rx="9" ry="6" /><circle cx="12" cy="12" r="1.5" fill="#2563eb" />
          </svg>
          StadiumMind <span className="text-brand">AI</span>
        </div>
        <p className="text-xl text-slate-600 max-w-xl mx-auto font-medium">
          The GenAI operating system for FIFA World Cup 2026. Select your portal to begin.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 z-10 w-full max-w-5xl px-4">
        {cards.map(({ icon: Icon, title, desc, href, gradient }) => (
          <button
            key={href}
            onClick={() => router.push(href)}
            className="group relative flex flex-col items-center justify-center p-8 rounded-[2rem] bg-white/60 backdrop-blur-xl border border-white/50 shadow-xl shadow-slate-200/50 hover:-translate-y-2 hover:shadow-2xl hover:shadow-slate-200/80 transition-all duration-300"
          >
            <div className={`absolute inset-0 rounded-[2rem] bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
            
            <div className={`flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br ${gradient} text-white shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300`}>
              <Icon size={36} strokeWidth={1.5} />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-2">{title}</h3>
            <p className="text-slate-500 font-medium text-center">{desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
