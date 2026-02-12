#!/usr/bin/env python3
"""Hex-grid drawing template generator.

This generator intentionally requires build123d so the output is a *solid
plate* with subtractive through-slots (line/corner holes).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

try:
    from build123d import Box, BuildPart, Locations, Mode, Pos, Rot, export_stl

    HAS_BUILD123D = True
except (ModuleNotFoundError, ImportError):
    HAS_BUILD123D = False


INCH = 25.4


@dataclass(frozen=True)
class StencilConfig:
    # Overall size (A1 mini friendly: keep under 180x180 mm)
    width: float = 170.0
    height: float = 170.0
    thickness: float = 1.6

    # Grid geometry
    hex_flat_to_flat: float = INCH  # 1 inch

    # Frame margin where no cutouts are made
    border: float = 6.0

    # Feature width
    slot_width: float = 0.75

    # Dashed-slot geometry
    edge_gap_from_vertex: float = 2.2
    vertex_arm_length: float = 2.4

    # Numeric tolerance for point hashing
    precision: int = 3


Point = tuple[float, float]
Edge = tuple[Point, Point]
Segment = tuple[float, float, float, float]  # cx, cy, length, angle_deg


class Backend(Enum):
    BUILD123D = "build123d"


def _round_point(point: Point, precision: int) -> Point:
    return (round(point[0], precision), round(point[1], precision))


def _canonical_edge(p1: Point, p2: Point, precision: int) -> Edge:
    a = _round_point(p1, precision)
    b = _round_point(p2, precision)
    return (a, b) if a <= b else (b, a)


def _hex_corners(center: Point, side: float) -> list[Point]:
    # Pointy-top hex: corner angles 30, 90, ..., 330 degrees
    cx, cy = center
    corners: list[Point] = []
    for i in range(6):
        angle_deg = 30.0 + i * 60.0
        angle = math.radians(angle_deg)
        corners.append((cx + side * math.cos(angle), cy + side * math.sin(angle)))
    return corners


def _collect_grid_geometry(config: StencilConfig):
    side = config.hex_flat_to_flat / math.sqrt(3.0)

    # Pointy-top center spacing
    dx = config.hex_flat_to_flat
    dy = 1.5 * side

    min_x = -config.width / 2 + config.border
    max_x = config.width / 2 - config.border
    min_y = -config.height / 2 + config.border
    max_y = config.height / 2 - config.border

    cols = int(math.ceil((config.width - 2 * config.border) / dx)) + 3
    rows = int(math.ceil((config.height - 2 * config.border) / dy)) + 3

    centers: list[Point] = []
    start_x = min_x - dx
    start_y = min_y - dy
    for col in range(cols):
        cx = start_x + col * dx
        y_offset = 0.5 * dy if (col % 2) else 0.0
        for row in range(rows):
            cy = start_y + row * dy + y_offset
            centers.append((cx, cy))

    edges: dict[Edge, None] = {}
    vertex_neighbors: dict[Point, set[Point]] = {}

    for center in centers:
        corners = _hex_corners(center, side)
        for i in range(6):
            edge = _canonical_edge(corners[i], corners[(i + 1) % 6], config.precision)
            edges[edge] = None

    for p1, p2 in edges:
        vertex_neighbors.setdefault(p1, set()).add(p2)
        vertex_neighbors.setdefault(p2, set()).add(p1)

    edge_dash_length = max(0.2, side - 2 * config.edge_gap_from_vertex)

    edge_segments: list[Segment] = []
    for (x1, y1), (x2, y2) in edges:
        mx = 0.5 * (x1 + x2)
        my = 0.5 * (y1 + y2)
        if not (min_x <= mx <= max_x and min_y <= my <= max_y):
            continue
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        edge_segments.append((mx, my, edge_dash_length, angle))

    vertex_segments: list[Segment] = []
    for (vx, vy), neighbors in vertex_neighbors.items():
        if not (min_x <= vx <= max_x and min_y <= vy <= max_y):
            continue
        for nx, ny in neighbors:
            angle = math.degrees(math.atan2(ny - vy, nx - vx))
            ax = vx + 0.5 * config.vertex_arm_length * math.cos(math.radians(angle))
            ay = vy + 0.5 * config.vertex_arm_length * math.sin(math.radians(angle))
            vertex_segments.append((ax, ay, config.vertex_arm_length, angle))

    return edge_segments, vertex_segments


def build_hex_grid_template(config: StencilConfig):
    """Create a plate + cut-through slots using build123d."""
    if not HAS_BUILD123D:
        raise RuntimeError("build123d is not available")

    edge_segments, vertex_segments = _collect_grid_geometry(config)
    cut_depth = config.thickness + 0.8

    with BuildPart() as stencil:
        Box(config.width, config.height, config.thickness)

        for cx, cy, length, angle in edge_segments:
            with Locations(Pos(cx, cy, 0) * Rot(0, 0, angle)):
                Box(length, config.slot_width, cut_depth, mode=Mode.SUBTRACT)

        for cx, cy, length, angle in vertex_segments:
            with Locations(Pos(cx, cy, 0) * Rot(0, 0, angle)):
                Box(length, config.slot_width, cut_depth, mode=Mode.SUBTRACT)

    return stencil.part


def main() -> None:
    config = StencilConfig()
    output = "hex_grid_template_1in_a1mini.stl"

    if not HAS_BUILD123D:
        raise SystemExit(
            "build123d is required to generate the solid stencil-with-holes model. "
            "Install it with: pip install build123d"
        )

    part = build_hex_grid_template(config)
    export_stl(part, output)
    backend = Backend.BUILD123D

    print(f"Wrote {output} using backend={backend.value}")


if __name__ == "__main__":
    main()
