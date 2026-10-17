"""Splitting a route into legs along an itinerary, so each day can carry its own color.

An itinerary is an ordered list of stops. Every part of the route (OSM relations are often several pieces)
is cut wherever a stop lies on it; a piece whose two ends sit at consecutive stops i and i+1 is leg i.
Pieces that do not join consecutive stops are "rest": trail that exists but is not on the plan.
Two different paths between the same stops (a ridge and a coast road) are told apart by putting a
via-point on each one in the itinerary."""
from itertools import product
from shapely.geometry import Point
from shapely.ops import substring


def main_line(route):
    """The longest LineString of a route geometry."""
    if route is None: return None
    return max(route.geoms, key=lambda g: g.length) if hasattr(route, "geoms") else route


def legs(route, stops, tol=400.0):
    """Returns [(LineString, leg_index_or_None), ...] covering the whole route."""
    if route is None: return []
    parts = list(route.geoms) if hasattr(route, "geoms") else [route]
    pts = [Point(x, y) for x, y, *_ in stops]
    if not pts: return [(p, None) for p in parts]
    pieces = []
    for line in parts:
        ds = sorted({round(line.project(p), 1) for p in pts if line.distance(p) <= tol})
        ds = [d for d in ds if 30 < d < line.length - 30]
        cuts = [0.0] + ds + [line.length]
        pieces += [substring(line, a, b) for a, b in zip(cuts[:-1], cuts[1:]) if b - a > 1]
    out = []
    for piece in pieces:
        s, e = Point(piece.coords[0]), Point(piece.coords[-1])
        near_s = [i for i, p in enumerate(pts) if p.distance(s) <= tol]
        near_e = [i for i, p in enumerate(pts) if p.distance(e) <= tol]
        pairs = [(i, j) for i, j in product(near_s, near_e) if abs(i - j) == 1]
        out.append((piece, min(pairs[0]) if pairs else None))
    return out
