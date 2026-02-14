#!/usr/bin/env python3
"""Render an STL file to a README-friendly SVG preview (no third-party deps)."""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

Vec3 = tuple[float, float, float]
Vec2 = tuple[float, float]
Triangle = tuple[Vec3, Vec3, Vec3]


def _parse_ascii_stl(text: str) -> list[Triangle]:
    triangles: list[Triangle] = []
    current: list[Vec3] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("vertex "):
            continue
        _, x, y, z = line.split(maxsplit=3)
        current.append((float(x), float(y), float(z)))
        if len(current) == 3:
            triangles.append((current[0], current[1], current[2]))
            current = []

    return triangles


def _parse_binary_stl(data: bytes) -> list[Triangle]:
    if len(data) < 84:
        raise ValueError("Not enough bytes for a binary STL header")

    count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + count * 50
    if len(data) < expected:
        raise ValueError("Binary STL appears truncated")

    triangles: list[Triangle] = []
    offset = 84
    for _ in range(count):
        # skip normal (3 float32)
        offset += 12
        v1 = struct.unpack_from("<3f", data, offset)
        offset += 12
        v2 = struct.unpack_from("<3f", data, offset)
        offset += 12
        v3 = struct.unpack_from("<3f", data, offset)
        offset += 12
        offset += 2  # attribute byte count
        triangles.append((v1, v2, v3))

    return triangles


def load_stl(path: Path) -> list[Triangle]:
    data = path.read_bytes()
    header = data[:5].lower()
    if header == b"solid":
        try:
            text = data.decode("utf-8")
            triangles = _parse_ascii_stl(text)
            if triangles:
                return triangles
        except UnicodeDecodeError:
            pass

    return _parse_binary_stl(data)


def rotate(v: Vec3, yaw_deg: float, pitch_deg: float) -> Vec3:
    x, y, z = v
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)

    # Yaw around Z
    x1 = x * math.cos(yaw) - y * math.sin(yaw)
    y1 = x * math.sin(yaw) + y * math.cos(yaw)
    z1 = z

    # Pitch around X
    x2 = x1
    y2 = y1 * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y1 * math.sin(pitch) + z1 * math.cos(pitch)

    return (x2, y2, z2)


def shade_for_triangle(tri: Triangle) -> str:
    a, b, c = tri
    ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / mag, ny / mag, nz / mag

    light = (0.25, -0.35, 0.9)
    lmag = math.sqrt(sum(v * v for v in light))
    lx, ly, lz = (light[0] / lmag, light[1] / lmag, light[2] / lmag)
    intensity = max(0.0, nx * lx + ny * ly + nz * lz)

    base = 150
    cval = int(base + intensity * 85)
    return f"rgb({cval},{cval + 8},{cval + 16})"


def render_svg(
    triangles: list[Triangle],
    output_path: Path,
    width: int = 1400,
    height: int = 900,
    yaw_deg: float = -36,
    pitch_deg: float = -58,
) -> None:
    rotated: list[tuple[tuple[Vec3, Vec3, Vec3], float, str]] = []

    for tri in triangles:
        rtri = tuple(rotate(v, yaw_deg, pitch_deg) for v in tri)
        depth = sum(v[2] for v in rtri) / 3.0
        rotated.append((rtri, depth, shade_for_triangle(rtri)))

    all_x = [v[0] for tri, _, _ in rotated for v in tri]
    all_y = [v[1] for tri, _, _ in rotated for v in tri]

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    span_x = max_x - min_x or 1.0
    span_y = max_y - min_y or 1.0
    scale = min((width * 0.86) / span_x, (height * 0.86) / span_y)

    def proj(v: Vec3) -> Vec2:
        x = (v[0] - (min_x + max_x) / 2.0) * scale + width / 2.0
        y = height / 2.0 - (v[1] - (min_y + max_y) / 2.0) * scale
        return (x, y)

    rotated.sort(key=lambda item: item[1])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n')
        f.write('  <rect width="100%" height="100%" fill="white"/>\n')
        for tri, _, color in rotated:
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in (proj(v) for v in tri))
            f.write(f'  <polygon points="{pts}" fill="{color}" stroke="rgba(75,85,99,0.30)" stroke-width="0.45"/>\n')
        f.write("</svg>\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl", nargs="?", default="hex_grid_template_1in_a1mini.stl")
    parser.add_argument("output", nargs="?", default="assets/hex_grid_template_preview.svg")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    triangles = load_stl(Path(args.stl))
    if not triangles:
        raise ValueError("No triangles found in STL file")
    render_svg(triangles, Path(args.output))
    print(f"Wrote preview image: {args.output}")


if __name__ == "__main__":
    main()
