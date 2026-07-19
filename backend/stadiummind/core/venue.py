"""The stadium venue graph.

A :class:`Venue` is an undirected graph of :class:`Zone` nodes. It is the
shared spatial model used by the simulator (where crowds accumulate), the
routing engine (shortest / least-congested paths) and the agents.

The default venue is a compact but realistic FIFA-style bowl: four gates, a
ring concourse, seating stands, food courts, washrooms, medical points,
parking and a metro station.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from stadiummind.core.models import Zone, ZoneType

# Metres per degree of latitude (roughly constant everywhere).
_M_PER_DEG_LAT = 111_320.0


@dataclass(frozen=True)
class GeoAnchor:
    """Anchors the normalised venue grid to a real-world location.

    ``footprint_m`` is the real width/height the normalised 0-1 grid maps onto,
    so a zone at normalised (x, y) is projected to a latitude/longitude offset
    from the anchor using an equirectangular approximation (accurate at the
    scale of a single stadium).
    """

    name: str
    lat: float
    lng: float
    footprint_m: float = 320.0


# Default anchor: MetLife Stadium, East Rutherford NJ - the FIFA World Cup 2026
# final venue. Coordinates are the stadium centroid.
METLIFE = GeoAnchor(
    name="MetLife Stadium", lat=40.81357, lng=-74.07429, footprint_m=320.0
)


@dataclass
class Venue:
    """An indexed, navigable collection of zones."""

    zones: dict[str, Zone] = field(default_factory=dict)
    anchor: GeoAnchor = METLIFE

    # -- construction -----------------------------------------------------
    def add(self, zone: Zone) -> None:
        self.zones[zone.id] = zone

    def connect(self, a: str, b: str) -> None:
        """Create an undirected edge between two zones."""
        if a not in self.zones or b not in self.zones:
            raise KeyError(f"cannot connect unknown zones {a!r} <-> {b!r}")
        if b not in self.zones[a].neighbours:
            self.zones[a].neighbours.append(b)
        if a not in self.zones[b].neighbours:
            self.zones[b].neighbours.append(a)

    # -- queries ----------------------------------------------------------
    def get(self, zone_id: str) -> Zone:
        return self.zones[zone_id]

    def __contains__(self, zone_id: str) -> bool:  # pragma: no cover - trivial
        return zone_id in self.zones

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self.zones.values())

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.zones)

    def of_type(self, zone_type: ZoneType) -> list[Zone]:
        return [z for z in self.zones.values() if z.type is zone_type]

    def distance(self, a: str, b: str) -> float:
        """Euclidean distance between two zones in metres.

        Normalised coordinates (0-1) are scaled by the anchor footprint.
        """
        za, zb = self.zones[a], self.zones[b]
        scale = self.anchor.footprint_m
        return math.hypot(za.x - zb.x, za.y - zb.y) * scale

    # -- geo projection ---------------------------------------------------
    def project(self, x: float, y: float) -> tuple[float, float]:
        """Project a normalised (x, y) grid point to real (lat, lng).

        x increases eastward, y increases *southward* (screen convention), so a
        smaller y is further north. Uses an equirectangular approximation, which
        is more than accurate enough over a ~300 m footprint.
        """
        east_m = (x - 0.5) * self.anchor.footprint_m
        north_m = (0.5 - y) * self.anchor.footprint_m
        lat = self.anchor.lat + north_m / _M_PER_DEG_LAT
        m_per_deg_lng = _M_PER_DEG_LAT * math.cos(math.radians(self.anchor.lat))
        lng = self.anchor.lng + east_m / m_per_deg_lng
        return round(lat, 6), round(lng, 6)

    def apply_geo(self) -> None:
        """Populate every zone's lat/lng from its grid position (unless already set)."""
        for zone in self.zones.values():
            if zone.lat is None or zone.lng is None:
                zone.lat, zone.lng = self.project(zone.x, zone.y)


def build_default_venue() -> Venue:
    """Construct and wire the default demonstration stadium."""
    v = Venue()

    # Gates (service_points = turnstiles).
    v.add(Zone("gate_1", "Gate 1", ZoneType.GATE, 0.10, 0.15, 4000, 8, accessible=True))
    v.add(Zone("gate_3", "Gate 3", ZoneType.GATE, 0.90, 0.15, 4000, 8, accessible=True))
    v.add(Zone("gate_5", "Gate 5", ZoneType.GATE, 0.10, 0.85, 4000, 8, accessible=True))
    v.add(Zone("gate_7", "Gate 7", ZoneType.GATE, 0.90, 0.85, 4000, 8, accessible=True))

    # Concourse ring.
    v.add(Zone("conc_n", "North Concourse", ZoneType.CONCOURSE, 0.50, 0.20, 6000))
    v.add(Zone("conc_s", "South Concourse", ZoneType.CONCOURSE, 0.50, 0.80, 6000))
    v.add(Zone("conc_e", "East Concourse", ZoneType.CONCOURSE, 0.80, 0.50, 6000))
    v.add(Zone("conc_w", "West Concourse", ZoneType.CONCOURSE, 0.20, 0.50, 6000))

    # Seating stands.
    v.add(Zone("stand_n", "North Stand", ZoneType.SEATING, 0.50, 0.32, 15000))
    v.add(Zone("stand_s", "South Stand", ZoneType.SEATING, 0.50, 0.68, 15000))
    v.add(Zone("stand_e", "East Stand", ZoneType.SEATING, 0.68, 0.50, 15000))
    v.add(Zone("stand_w", "West Stand", ZoneType.SEATING, 0.32, 0.50, 15000))

    # Amenities (service_points = tills / stalls).
    v.add(Zone("food_a", "Food Court A", ZoneType.FOOD, 0.35, 0.25, 400, 6))
    v.add(Zone("food_b", "Food Court B", ZoneType.FOOD, 0.65, 0.75, 400, 6))
    v.add(Zone("wc_n", "Washroom North", ZoneType.WASHROOM, 0.42, 0.22, 120, 10))
    v.add(Zone("wc_s", "Washroom South", ZoneType.WASHROOM, 0.58, 0.78, 120, 10))
    v.add(Zone("med_1", "Medical Point 1", ZoneType.MEDICAL, 0.25, 0.55, 40, 2))

    # Transport / parking.
    v.add(Zone("parking", "Parking P1", ZoneType.PARKING, 0.05, 0.50, 3000))
    v.add(Zone("metro", "Metro Station", ZoneType.TRANSIT, 0.95, 0.50, 8000, 12))

    # -- edges: gates -> nearest concourse --------------------------------
    v.connect("gate_1", "conc_n")
    v.connect("gate_1", "conc_w")
    v.connect("gate_3", "conc_n")
    v.connect("gate_3", "conc_e")
    v.connect("gate_5", "conc_s")
    v.connect("gate_5", "conc_w")
    v.connect("gate_7", "conc_s")
    v.connect("gate_7", "conc_e")

    # Concourse ring.
    v.connect("conc_n", "conc_e")
    v.connect("conc_e", "conc_s")
    v.connect("conc_s", "conc_w")
    v.connect("conc_w", "conc_n")

    # Concourse -> stands.
    v.connect("conc_n", "stand_n")
    v.connect("conc_s", "stand_s")
    v.connect("conc_e", "stand_e")
    v.connect("conc_w", "stand_w")

    # Amenities hang off the nearest concourse.
    v.connect("conc_n", "food_a")
    v.connect("conc_n", "wc_n")
    v.connect("conc_s", "food_b")
    v.connect("conc_s", "wc_s")
    v.connect("conc_w", "med_1")

    # Transport.
    v.connect("gate_1", "parking")
    v.connect("gate_5", "parking")
    v.connect("gate_3", "metro")
    v.connect("gate_7", "metro")

    # Real-world landmark overrides (set before apply_geo so they are kept):
    #   Meadowlands Rail Station sits north-west of the stadium; the main
    #   parking lots sit to the south-west.
    v.get("metro").lat, v.get("metro").lng = 40.814890, -74.077260
    v.get("parking").lat, v.get("parking").lng = 40.811000, -74.079000

    # Project all remaining zones onto real coordinates around MetLife Stadium.
    v.apply_geo()
    return v
