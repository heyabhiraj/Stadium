"use client";

/**
 * Google Maps view of the real stadium with live congestion overlays.
 *
 * - Loads the Google Maps JS API using NEXT_PUBLIC_GOOGLE_MAPS_API_KEY.
 * - Drops a coloured circle on every geo-located zone (green→red by congestion).
 * - When a gate / exit / transit zone is clicked, fetches a walking route from
 *   the backend (/api/directions, which uses the Google Directions API) and
 *   draws it as a polyline.
 * - If no API key is configured, it transparently falls back to the built-in
 *   SVG map so the app still works offline.
 */

import { useEffect, useRef, useState } from "react";
import { StadiumMap } from "@/features/map/StadiumMap";
import { api, LEVEL_COLOR, type VenueAnchor, type ZoneHeat } from "@/lib/api";

// Zone types that make sense as a walking-route destination.
const ROUTABLE = new Set(["gate", "exit", "transit", "parking"]);

let mapsPromise: Promise<void> | null = null;

/** Load the Google Maps JS API exactly once. */
function loadGoogleMaps(key: string): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if ((window as any).google?.maps) return Promise.resolve();
  if (mapsPromise) return mapsPromise;
  mapsPromise = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=geometry`;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("failed to load Google Maps"));
    document.head.appendChild(s);
  });
  return mapsPromise;
}

export function GoogleStadiumMap({
  zones,
  anchor,
}: {
  zones: ZoneHeat[];
  anchor: VenueAnchor | null;
}) {
  const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const routeRef = useRef<any>(null);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  // Initialise the map once.
  useEffect(() => {
    if (!key || !anchor) return;
    loadGoogleMaps(key)
      .then(() => {
        const g = (window as any).google;
        if (!ref.current || !g) return;
        mapRef.current = new g.maps.Map(ref.current, {
          center: { lat: anchor.lat, lng: anchor.lng },
          zoom: 17,
          mapTypeId: "satellite",
          disableDefaultUI: true,
          zoomControl: true,
        });
        setReady(true);
      })
      .catch(() => setFailed(true));
  }, [key, anchor]);

  // Redraw markers whenever the congestion snapshot changes.
  useEffect(() => {
    const g = (window as any).google;
    if (!ready || !g || !mapRef.current) return;
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = zones
      .filter((z) => z.lat != null && z.lng != null)
      .map((z) => {
        const marker = new g.maps.Marker({
          position: { lat: z.lat, lng: z.lng },
          map: mapRef.current,
          title: `${z.name} — ${(z.ratio * 100).toFixed(0)}% (${z.level})`,
          icon: {
            path: g.maps.SymbolPath.CIRCLE,
            scale: z.type === "seating" ? 12 : 8,
            fillColor: LEVEL_COLOR[z.level],
            fillOpacity: 0.9,
            strokeColor: "#ffffff",
            strokeWeight: 1.5,
          },
        });
        if (ROUTABLE.has(z.type)) {
          marker.addListener("click", () => drawRoute("gate_1", z.id));
        }
        return marker;
      });
  }, [zones, ready]);

  async function drawRoute(origin: string, destination: string) {
    const g = (window as any).google;
    if (!g || !mapRef.current) return;
    try {
      const dir = await api.directions(origin, destination);
      routeRef.current?.setMap(null);
      routeRef.current = new g.maps.Polyline({
        path: dir.polyline.map(([lat, lng]) => ({ lat, lng })),
        strokeColor: "#2563eb",
        strokeWeight: 5,
        map: mapRef.current,
      });
    } catch {
      /* backend offline — ignore */
    }
  }

  // Graceful fallback to the SVG map when Maps is unavailable.
  if (!key || failed) return <StadiumMap zones={zones} />;

  return <div ref={ref} className="w-full rounded-xl" style={{ height: 460 }} />;
}
