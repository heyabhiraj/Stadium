"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Navigation, Utensils, TrainFront, Accessibility, AlertTriangle, MapPin, User, Ticket } from "lucide-react";
const GoogleStadiumMap = dynamic(() => import("@/features/map/GoogleStadiumMap").then(mod => mod.GoogleStadiumMap), {
  ssr: false,
  loading: () => <div className="w-full h-[460px] bg-slate-100 animate-pulse rounded-xl" />
});
import { RecommendationCard } from "@/features/ai/RecommendationCard";
import { NavigationAlert } from "@/features/navigation/NavigationAlert";
import { api, type Match, type Recommendation, type VenueAnchor, type ZoneHeat } from "@/lib/api";
import { I18N, LOCALES, flagColors, type Locale } from "@/lib/i18n";

type Step = "language" | "seat" | "dashboard";

function Flag({ locale }: { locale: Locale }) {
  const [top, bottom] = flagColors(locale);
  return (
    <svg width={34} height={24} viewBox="0 0 34 24" className="rounded-sm border border-black/10 shrink-0">
      <rect width={34} height={12} fill={top} />
      <rect y={12} width={34} height={12} fill={bottom} />
    </svg>
  );
}

const ACTIONS = [
  { icon: Navigation, label: "Navigate" },
  { icon: Utensils, label: "Food" },
  { icon: TrainFront, label: "Transport" },
  { icon: MapPin, label: "Washroom" },
  { icon: Accessibility, label: "Accessibility" },
  { icon: AlertTriangle, label: "Emergency" },
];

export default function FanHome() {
  const [step, setStep] = useState<Step>("language");
  const [locale, setLocale] = useState<Locale>("en");
  
  // Onboarding Data
  const [userName, setUserName] = useState("");
  const [seat, setSeat] = useState("");

  // Dashboard Data
  const [zones, setZones] = useState<ZoneHeat[]>([]);
  const [anchor, setAnchor] = useState<VenueAnchor | null>(null);
  const [match, setMatch] = useState<Match | null>(null);
  const [answer, setAnswer] = useState<Recommendation | null>(null);

  const t = I18N[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = I18N[locale].dir;
  }, [locale]);

  useEffect(() => {
    if (step === "dashboard") {
      api.heatmap().then(setZones).catch(() => setZones([]));
      api.venue().then((v) => setAnchor(v.anchor)).catch(() => setAnchor(null));
      api.match().then(setMatch).catch(() => setMatch(null));
    }
  }, [step]);

  async function ask() {
    try {
      setAnswer(await api.query("navigate", { origin: "gate_1", destination: "stand_n" }));
    } catch {
      /* backend offline */
    }
  }

  const alerts = zones.filter((z) => z.ratio >= 0.8).sort((a, b) => b.ratio - a.ratio).slice(0, 5);
  const kickoff = match?.kickoff_utc ? new Date(match.kickoff_utc).toLocaleString() : "TBD";

  if (step === "language") {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="w-full max-w-xl text-center bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50">
          <h2 className="text-2xl font-bold mb-6">{t.chooseLang || "Select Language"}</h2>
          <div className="grid grid-cols-2 gap-4 my-6">
            {LOCALES.map((l) => (
              <button
                key={l}
                onClick={() => setLocale(l)}
                className={`flex items-center gap-3 rounded-xl border-2 p-4 font-semibold text-start transition-all ${
                  l === locale ? "border-brand bg-brand-soft shadow-md shadow-brand/20" : "border-slate-100 hover:border-slate-300"
                }`}
              >
                <Flag locale={l} />
                <span className="text-lg">{I18N[l].name}</span>
              </button>
            ))}
          </div>
          <button
            onClick={() => setStep("seat")}
            className="w-full rounded-xl bg-brand text-white px-5 py-4 font-bold text-lg hover:bg-brand/90 transition-colors"
          >
            {t.continue || "Continue"}
          </button>
        </div>
      </div>
    );
  }

  if (step === "seat") {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="w-full max-w-md bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50">
          <h2 className="text-2xl font-bold mb-2">Welcome to StadiumMind</h2>
          <p className="text-slate-500 mb-6">Let's personalize your matchday experience.</p>
          
          <div className="space-y-4 mb-8">
            <div>
              <label htmlFor="userNameInput" className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-2">
                <User size={16} aria-hidden="true" /> Your Name
              </label>
              <input
                id="userNameInput"
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="e.g. John Doe"
                aria-label="Your Name"
                className="w-full border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
            </div>
            <div>
              <label htmlFor="seatInput" className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-2">
                <Ticket size={16} aria-hidden="true" /> Seat Location
              </label>
              <input
                id="seatInput"
                type="text"
                value={seat}
                onChange={(e) => setSeat(e.target.value)}
                placeholder="e.g. Block 101, Row A, Seat 1"
                aria-label="Seat Location"
                className="w-full border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
            </div>
          </div>

          <button
            onClick={() => setStep("dashboard")}
            disabled={!userName || !seat}
            className="w-full rounded-xl bg-brand text-white px-5 py-4 font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-brand/90 transition-colors"
          >
            Enter Fan App
          </button>
        </div>
      </div>
    );
  }

  // Dashboard (Full Screen Responsive)
  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Top Banner */}
      <div className="rounded-3xl p-8 text-white bg-gradient-to-br from-navy via-[#0A192F] to-brand shadow-xl">
        <div className="flex justify-between items-start">
          <div>
            <div className="text-brand-soft font-medium mb-1 opacity-80">Good evening, {userName || "Fan"}</div>
            <div className="text-4xl font-extrabold tracking-tight mb-2">
              {match ? `${match.home_team} vs ${match.away_team}` : "Loading match…"}
            </div>
            <div className="text-lg opacity-90 flex items-center gap-2">
              <MapPin size={18} />
              {match ? `${match.competition} · ${match.venue}` : "FIFA World Cup 2026"}
            </div>
            <div className="text-sm opacity-80 mt-3 bg-white/10 inline-block px-4 py-1.5 rounded-full backdrop-blur-md">
              {match?.status === "IN_PLAY" || match?.status === "LIVE"
                ? `Live · ${match.home_score ?? 0}–${match.away_score ?? 0} (${match.minute ?? 0}')`
                : `Kickoff: ${kickoff}`}
            </div>
          </div>
          <div className="hidden md:block bg-white/10 p-4 rounded-2xl backdrop-blur-md border border-white/10 text-right">
            <div className="text-xs uppercase tracking-wider opacity-70 mb-1">Your Seat</div>
            <div className="text-lg font-bold flex items-center gap-2 justify-end">
              <Ticket size={20} className="text-brand-soft" />
              {seat || "General Admission"}
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Actions & Alerts */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
            <h3 className="text-lg font-bold mb-4 text-slate-900">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              {ACTIONS.map(({ icon: Icon, label }) => (
                <button
                  key={label}
                  onClick={ask}
                  className="flex flex-col items-center justify-center gap-2 border border-slate-100 bg-slate-50 rounded-2xl p-4 hover:border-brand hover:bg-brand-soft hover:text-brand transition-all group"
                >
                  <Icon size={24} className="text-slate-600 group-hover:text-brand transition-colors" />
                  <span className="text-sm font-semibold">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {answer && (
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-brand/20 bg-brand-soft/50">
              <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-brand">
                <AlertTriangle size={20} /> AI Recommendation
              </h3>
              <RecommendationCard rec={answer} />
            </div>
          )}

          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-900">Live Alerts</h3>
              <Link href="/fan/ai" className="text-sm font-semibold text-brand hover:underline">Ask AI →</Link>
            </div>
            {alerts.length === 0 ? (
              <div className="text-slate-500 bg-slate-50 rounded-xl p-4 text-sm text-center">
                All clear — no congestion right now.
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((z) => (
                  <div key={z.id} className="flex items-center gap-3 p-3 rounded-xl bg-red-50 text-red-900 text-sm">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                    <div>
                      <span className="font-bold">{z.name}</span> is {z.level} ({(z.ratio * 100).toFixed(0)}%)
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Map */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 h-full min-h-[600px] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <MapPin size={20} className="text-brand" />
                Live Stadium Map {anchor ? `· ${anchor.name}` : ""}
              </h3>
              <Link href="/fan/map" className="text-sm font-semibold text-brand hover:underline">Full screen →</Link>
            </div>
            <div className="flex-1 rounded-2xl overflow-hidden border border-slate-200 min-h-[400px]">
              <GoogleStadiumMap zones={zones} anchor={anchor} />
            </div>
          </div>
        </div>
      </div>
      <NavigationAlert />
    </div>
  );
}
