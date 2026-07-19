"use client";

/**
 * SVG stadium map with a live congestion heatmap.
 *
 * Pure SVG (per the design system - no emoji, no raster tiles, no Mapbox key
 * needed). Each zone is a circle coloured by its congestion level; congested
 * zones pulse to draw the eye.
 */

import { LEVEL_COLOR, type ZoneHeat } from "@/lib/api";

const W = 640;
const H = 460;

function radiusFor(type: string): number {
  if (type === "seating") return 30;
  if (type === "concourse") return 20;
  return 15;
}

export function StadiumMap({
  zones,
  onSelect,
}: {
  zones: ZoneHeat[];
  onSelect?: (zone: ZoneHeat) => void;
}) {
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-xl">
      <rect x={0} y={0} width={W} height={H} rx={16} fill="#0b1f3a" />
      {/* Pitch */}
      <rect
        x={W * 0.3}
        y={H * 0.36}
        width={W * 0.4}
        height={H * 0.28}
        rx={10}
        fill="#0e7a34"
        stroke="#3ddc6b"
        strokeWidth={1.5}
      />
      <circle cx={W * 0.5} cy={H * 0.5} r={20} fill="none" stroke="#3ddc6b" />

      {zones.map((z) => {
        const cx = z.x * W;
        const cy = z.y * H;
        const r = radiusFor(z.type);
        const color = LEVEL_COLOR[z.level];
        return (
          <g key={z.id} onClick={() => onSelect?.(z)} style={{ cursor: "pointer" }}>
            <circle cx={cx} cy={cy} r={r} fill={color} fillOpacity={0.85} stroke="#fff" strokeWidth={1.2}>
              <title>
                {z.name}: {(z.ratio * 100).toFixed(0)}% ({z.level})
              </title>
            </circle>
            {z.level === "congested" && (
              <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={2}>
                <animate attributeName="r" values={`${r};${r + 10};${r}`} dur="1.4s" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" values="0.9;0;0.9" dur="1.4s" repeatCount="indefinite" />
              </circle>
            )}
            <text x={cx} y={cy + 3} textAnchor="middle" fontSize={9} fontWeight={600} fill="#fff">
              {z.name.split(" ")[0]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
