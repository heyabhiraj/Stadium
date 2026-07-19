"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
const GoogleStadiumMap = dynamic(() => import("@/features/map/GoogleStadiumMap").then(mod => mod.GoogleStadiumMap), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-slate-100 animate-pulse rounded-2xl" />
});
import { RecommendationCard } from "@/features/ai/RecommendationCard";
import { api, type Recommendation, type ZoneHeat, type VenueAnchor } from "@/lib/api";
import { BrainCircuit, Activity, Users, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";

export function OpsDashboard() {
  const [zones, setZones] = useState<ZoneHeat[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [anchor, setAnchor] = useState<VenueAnchor | null>(null);
  const [minute, setMinute] = useState(0);
  const [token, setToken] = useState<string>("");

  useEffect(() => {
    // Authenticate as an operator so decisions are accepted by the backend.
    api.login("op", "operations").then((r) => setToken(r.access_token)).catch(() => {});
    
    // Fetch static venue anchor once
    api.venue().then((v) => setAnchor(v.anchor)).catch(() => {});

    const poll = async () => {
      try {
        const heat = await api.tick(); // advance + fetch heatmap
        setZones(heat);
        setRecs(await api.recommendations());
        setMinute((await api.health()).match_minute);
      } catch {
        /* backend offline */
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, []);

  async function decide(rec: Recommendation, approved: boolean) {
    if (!token) return;
    
    // Optimistic UI update for Efficiency score
    setRecs((prev) => prev.map((r) => (r.id === rec.id ? { ...r, approved } : r)));
    
    try {
      const updated = await api.decide(rec.id, approved, token);
      setRecs((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      if (approved) {
        localStorage.setItem('trigger_nav_update', 'true');
      }
    } catch {
      // Revert if failed
      setRecs((prev) => prev.map((r) => (r.id === rec.id ? rec : r)));
    }
  }

  const attendance = zones
    .filter((z) => z.type === "seating")
    .reduce((a, z) => a + z.occupancy, 0);
  const congested = zones.filter((z) => z.level === "congested").length;

  const pendingRecs = recs.filter((r) => r.approved === null);
  const processedRecs = recs.filter((r) => r.approved !== null).slice(0, 5);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col gap-6 w-full -mt-4">
      {/* Top Navigation / Status Bar */}
      <div className="bg-navy text-white rounded-3xl p-6 shadow-xl flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="bg-brand p-3 rounded-xl">
            <Cpu size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">AI Command Center</h1>
            <p className="text-sm opacity-80 text-brand-soft">Operations & Crowd Control</p>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="bg-white/10 px-5 py-3 rounded-2xl backdrop-blur-md flex flex-col items-end">
            <span className="text-xs uppercase tracking-wider opacity-70">Match Minute</span>
            <span className="text-xl font-extrabold text-brand-soft">{minute}'</span>
          </div>
          <div className="bg-white/10 px-5 py-3 rounded-2xl backdrop-blur-md flex flex-col items-end">
            <span className="text-xs uppercase tracking-wider opacity-70">Live Attendance</span>
            <span className="text-xl font-extrabold flex items-center gap-2">
              <Users size={18} /> {attendance.toLocaleString()}
            </span>
          </div>
          <div className={`px-5 py-3 rounded-2xl backdrop-blur-md flex flex-col items-end ${congested > 0 ? 'bg-red-500/20 text-red-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
            <span className="text-xs uppercase tracking-wider opacity-70">Congested Zones</span>
            <span className="text-xl font-extrabold flex items-center gap-2">
              <Activity size={18} /> {congested}
            </span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 items-start flex-1">
        
        {/* Left Column: AI Copilot & Decisions */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-brand/20 bg-gradient-to-b from-white to-brand-soft/10">
            <div className="flex items-center gap-2 mb-4">
              <BrainCircuit className="text-brand" size={24} />
              <h2 className="text-xl font-bold text-slate-900">AI Predictions & Actions</h2>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              The AI Engine is continuously monitoring crowd density and predicting bottlenecks. Review the recommended actions below.
            </p>

            {pendingRecs.length === 0 ? (
              <div className="text-center p-6 bg-slate-50 rounded-2xl border border-slate-100">
                <ShieldCheck size={32} className="text-emerald-500 mx-auto mb-2" />
                <p className="text-emerald-700 font-medium">All zones operating optimally.</p>
                <p className="text-xs text-slate-500 mt-1">AI is actively monitoring.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingRecs.map((r) => (
                  <div key={r.id} className="relative group">
                    {/* Visual indicator of "AI Thinking" */}
                    <div className="absolute -left-3 top-4 w-1 h-12 bg-brand rounded-r-md" />
                    <div className="pl-2">
                      <div className="flex items-center gap-2 mb-2 text-xs font-bold text-brand uppercase tracking-wider">
                        <AlertTriangle size={14} /> AI Predicts Congestion
                      </div>
                      <RecommendationCard rec={r} onDecide={decide} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Audit Log / History */}
          {processedRecs.length > 0 && (
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
              <h3 className="text-md font-bold text-slate-900 mb-4">Action Audit Log</h3>
              <div className="space-y-3">
                {processedRecs.map(r => (
                  <div key={r.id} className="flex justify-between items-center text-sm p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="truncate max-w-[200px] text-slate-700">{r.title}</span>
                    <span className={`px-2 py-1 rounded-md text-xs font-bold ${r.approved ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                      {r.approved ? 'APPROVED' : 'REJECTED'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live 3D Map */}
        <div className="lg:col-span-2 flex flex-col h-full min-h-[600px]">
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex-1 flex flex-col relative overflow-hidden">
            <div className="flex justify-between items-center mb-4 z-10">
              <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                Live Topographic Map
              </h2>
              <div className="flex items-center gap-2 text-sm text-slate-500 font-medium bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Live Feed
              </div>
            </div>
            <div className="flex-1 rounded-2xl overflow-hidden border border-slate-200 min-h-[500px]">
              <GoogleStadiumMap zones={zones} anchor={anchor} />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
