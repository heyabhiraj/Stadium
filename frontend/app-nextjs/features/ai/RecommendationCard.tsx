"use client";

/** A single AI recommendation with the "explain -> approve/reject" pattern. */

import type { Recommendation } from "@/lib/api";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-danger",
  high: "bg-orange-100 text-busy",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-success",
};

export function RecommendationCard({
  rec,
  onDecide,
}: {
  rec: Recommendation;
  onDecide?: (rec: Recommendation, approved: boolean) => void;
}) {
  const conf = Math.round(rec.confidence * 100);
  return (
    <div className="rounded-xl border border-slate-200 p-4 mb-3 bg-white">
      <div className="flex items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-brand font-bold">
          {rec.agent} agent
        </span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[rec.severity] ?? ""}`}>
          {rec.severity}
        </span>
      </div>
      <div className="font-bold mt-1">{rec.title}</div>
      <p className="text-slate-500 text-sm mt-1">{rec.explanation}</p>
      <div className="text-xs text-slate-500 mt-2">Confidence {conf}%</div>
      <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden mt-1">
        <div className="h-full bg-brand" style={{ width: `${conf}%` }} />
      </div>
      {rec.approved === null && onDecide && (
        <div className="flex gap-2 mt-3">
          <button
            className="rounded-lg bg-success text-white px-3 py-1.5 text-sm font-semibold"
            onClick={() => onDecide(rec, true)}
          >
            Approve
          </button>
          <button
            className="rounded-lg border border-danger text-danger px-3 py-1.5 text-sm font-semibold"
            onClick={() => onDecide(rec, false)}
          >
            Reject
          </button>
        </div>
      )}
      {rec.approved === true && (
        <div className="mt-3 text-xs font-bold text-success">Approved &amp; actioned</div>
      )}
      {rec.approved === false && (
        <div className="mt-3 text-xs font-bold text-danger">Rejected</div>
      )}
    </div>
  );
}
