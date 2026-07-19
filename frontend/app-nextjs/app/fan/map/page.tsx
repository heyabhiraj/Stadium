"use client";

/** Full-screen live stadium map (Google satellite + congestion overlay). */

import { useEffect, useState } from "react";
import { GoogleStadiumMap } from "@/features/map/GoogleStadiumMap";
import { api, type VenueAnchor, type ZoneHeat } from "@/lib/api";

export default function FanMap() {
  const [zones, setZones] = useState<ZoneHeat[]>([]);
  const [anchor, setAnchor] = useState<VenueAnchor | null>(null);

  useEffect(() => {
    const load = () => api.heatmap().then(setZones).catch(() => {});
    api.venue().then((v) => setAnchor(v.anchor)).catch(() => {});
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <h3 className="text-xs uppercase tracking-wide text-slate-500 mb-2">
        Stadium map {anchor ? `· ${anchor.name}` : ""}
      </h3>
      <GoogleStadiumMap zones={zones} anchor={anchor} />
      <div className="flex gap-4 text-xs text-slate-500 mt-3">
        <span><i className="inline-block w-2.5 h-2.5 rounded-full mr-1" style={{ background: "#16a34a" }} />normal</span>
        <span><i className="inline-block w-2.5 h-2.5 rounded-full mr-1" style={{ background: "#f59e0b" }} />moderate</span>
        <span><i className="inline-block w-2.5 h-2.5 rounded-full mr-1" style={{ background: "#ea580c" }} />busy</span>
        <span><i className="inline-block w-2.5 h-2.5 rounded-full mr-1" style={{ background: "#dc2626" }} />congested</span>
      </div>
    </div>
  );
}
