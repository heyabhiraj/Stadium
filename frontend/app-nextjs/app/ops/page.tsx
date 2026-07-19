"use client";

/**
 * Operations centre: KPI strip, AI copilot recommendations (approve/reject) and
 * the live heatmap. Polls the backend once per second, mirroring the WebSocket
 * feed for simplicity.
 */

import { useEffect, useState } from "react";
import { StadiumMap } from "@/components/StadiumMap";
import { RecommendationCard } from "@/components/RecommendationCard";
import { api, type Recommendation, type ZoneHeat } from "@/lib/api";

export default function OpsDashboard() {
  const [zones, setZones] = useState<ZoneHeat[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [minute, setMinute] = useState(0);
  const [token, setToken] = useState<string>("");

  useEffect(() => {
    // Authenticate as an operator so decisions are accepted by the backend.
    api.login("op", "operations").then((r) => setToken(r.access_token)).catch(() => {});
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
    try {
      const updated = await api.decide(rec.id, approved, token);
      setRecs((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch {
      /* ignore */
    }
  }

  const attendance = zones
    .filter((z) => z.type === "seating")
    .reduce((a, z) => a + z.occupancy, 0);
  const congested = zones.filter((z) => z.level === "congested").length;

  const Kpi = ({ n, l }: { n: string | number; l: string }) => (
    <div className="bg-navy text-white rounded-xl p-3">
      <div className="text-2xl font-extrabold">{n}</div>
      <div className="text-xs opacity-80">{l}</div>
    </div>
  );

  return (
    <div>
      <div className="grid grid-cols-4 gap-3 mb-4">
        <Kpi n={`${minute}'`} l="Match minute" />
        <Kpi n={attendance.toLocaleString()} l="Attendance" />
        <Kpi n={congested} l="Congested zones" />
        <Kpi n={recs.length} l="Active recs" />
      </div>
      <div className="grid md:grid-cols-2 gap-4 items-start">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-xs uppercase tracking-wide text-slate-500 mb-2">
            AI copilot — recommendations
          </h3>
          {recs.length === 0 ? (
            <p className="text-slate-500 text-sm">Stadium running smoothly.</p>
          ) : (
            recs.map((r) => <RecommendationCard key={r.id} rec={r} onDecide={decide} />)
          )}
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Live heatmap</h3>
          <StadiumMap zones={zones} />
        </div>
      </div>
    </div>
  );
}
