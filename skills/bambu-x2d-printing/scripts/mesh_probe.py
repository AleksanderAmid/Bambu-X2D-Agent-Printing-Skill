"""Measure a saved binary or ASCII STL in a known frame. Standard library only."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import struct


def triangles(path):
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(84)
        if len(header) == 84:
            count = struct.unpack_from("<I", header, 80)[0]
            if size == 84 + 50 * count:
                for _ in range(count):
                    data = struct.unpack("<12fH", stream.read(50))
                    yield (data[3:6], data[6:9], data[9:12])
                return
    with path.open(encoding="ascii") as stream:
        facet = None
        seen_solid = False
        for line in stream:
            words = line.lower().split()
            if not words:
                continue
            tag = words[0]
            if tag == "solid":
                seen_solid = True
            elif tag == "facet":
                if facet is not None:
                    raise ValueError("Unclosed STL facet")
                facet = []
            elif tag == "vertex":
                if facet is None or len(words) != 4:
                    raise ValueError("Malformed STL vertex")
                facet.append(tuple(map(float, words[1:])))
            elif tag == "endfacet":
                if facet is None or len(facet) != 3:
                    raise ValueError("Expected three vertices per STL facet")
                yield tuple(facet)
                facet = None
            elif tag not in {"outer", "endloop", "endsolid"}:
                raise ValueError("Unrecognized ASCII STL statement")
        if facet is not None or not seen_solid:
            raise ValueError("Incomplete ASCII STL")


def segment_at_z(points, height):
    if height < min(p[2] for p in points) or height > max(p[2] for p in points):
        return None
    if any(abs(p[2] - height) < 1e-8 for p in points):
        raise ValueError("Section meets a vertex or coplanar face. Pick a nearby interior Z.")
    hits = []
    for start, end in zip(points, points[1:] + points[:1]):
        if (start[2] < height) != (end[2] < height):
            ratio = (height - start[2]) / (end[2] - start[2])
            hits.append(tuple(round(start[i] + ratio * (end[i] - start[i]), 7) for i in (0, 1)))
    return hits or None


def loop_measure(points):
    xmin, ymin = map(min, zip(*points))
    xmax, ymax = map(max, zip(*points))
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    nearest = math.inf
    farthest = 0.0
    twice_area = 0.0
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        ax, ay, bx, by = ax - cx, ay - cy, bx - cx, by - cy
        dx, dy = bx - ax, by - ay
        t = min(1, max(0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
        nearest = min(nearest, math.hypot(ax + t * dx, ay + t * dy))
        farthest = max(farthest, math.hypot(ax, ay))
        twice_area += ax * by - bx * ay
    return {"center_xy_mm": [cx, cy], "span_xy_mm": [xmax - xmin, ymax - ymin],
            "radial_range_mm": [nearest, farthest], "area_mm2": abs(twice_area) / 2}


def closed_loops(segments):
    neighbors = defaultdict(list)
    for a, b in segments:
        if a == b:
            raise ValueError("Section collapsed at the reporting precision")
        neighbors[a].append(b)
        neighbors[b].append(a)
    if any(len(set(adjacent)) != 2 or len(adjacent) != 2 for adjacent in neighbors.values()):
        raise ValueError("Section has an open or branched contour")
    remaining = set(neighbors)
    loops = []
    while remaining:
        start = next(iter(remaining))
        points = [start]
        previous, current = start, neighbors[start][0]
        remaining.remove(start)
        while current != start:
            remaining.remove(current)
            points.append(current)
            a, b = neighbors[current]
            previous, current = current, b if a == previous else a
        loops.append(loop_measure(points))
    return sorted(loops, key=lambda loop: (-loop["area_mm2"], loop["center_xy_mm"]))


def measure(path, mm_per_unit, section_z=None):
    if not math.isfinite(mm_per_unit) or mm_per_unit <= 0:
        raise ValueError("mm-per-unit must be finite and positive")
    if section_z is not None and not math.isfinite(section_z):
        raise ValueError("section-z must be finite millimetres")
    low, high = [math.inf] * 3, [-math.inf] * 3
    occurrences, winding = Counter(), Counter()
    facet_count = degenerate = 0
    segments = []
    for raw in triangles(path):
        pts = [tuple(v * mm_per_unit for v in vertex) for vertex in raw]
        facet_count += 1
        for vertex in pts:
            for i, v in enumerate(vertex):
                if not math.isfinite(v):
                    raise ValueError("Non-finite mesh coordinate")
                low[i], high[i] = min(low[i], v), max(high[i], v)
        a, b, c = pts
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        if all(u[i] * v[(i + 1) % 3] == u[(i + 1) % 3] * v[i] for i in range(3)):
            degenerate += 1
        for start, end in zip(pts, pts[1:] + pts[:1]):
            key = tuple(sorted((start, end)))
            occurrences[key] += 1
            winding[key] += 1 if start < end else -1
        if section_z is not None:
            segment = segment_at_z(pts, section_z)
            if segment:
                segments.append(segment)
    if not facet_count:
        raise ValueError("STL contains no triangles")
    result = {"mm_per_input_unit": mm_per_unit, "facets": facet_count, "min_mm": low, "max_mm": high,
              "span_mm": [b - a for a, b in zip(low, high)], "boundary_edges": sum(n == 1 for n in occurrences.values()),
              "overused_edges": sum(n > 2 for n in occurrences.values()), "degenerate_faces": degenerate,
              "inconsistent_edge_pairs": sum(n == 2 and winding[e] != 0 for e, n in occurrences.items())}
    if section_z is not None:
        result.update(section_z_mm=section_z, loops=closed_loops(segments))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stl", type=Path)
    p.add_argument("--mm-per-unit", required=True, type=float, help="Known import/export conversion")
    p.add_argument("--section-z", type=float, help="Interior horizontal cut in mm")
    args = p.parse_args()
    try:
        print(json.dumps(measure(args.stl, args.mm_per_unit, args.section_z), indent=2, allow_nan=False))
    except (OSError, ValueError, struct.error) as exc:
        p.exit(2, f"Measurement failed: {exc}\n")


if __name__ == "__main__":
    main()
