# Hex Grid Drawing Template (1-inch hexes)

This project contains a Python script that generates a printable hex-grid drawing aid for TTRPG maps.

- Common terms: **stencil** and **template** are both used for this kind of tool.
- For your use case, **template** is slightly more precise because it is meant to guide pen lines repeatedly on paper.

The generated layout follows the style in your reference image:
- short line dashes centered on each hex edge
- small 3-way “Y” junctions at each hex vertex

## Printer target

Defaults are chosen for a **Bambu Lab A1 mini** (PLA, FDM):
- Plate/envelope size target: `170 x 170 mm`
- Thickness: `1.6 mm`
- Hex size: `1 inch` flat-to-flat (`25.4 mm`)

## Files

- `hex_grid_template.py` – generator script
- `hex_grid_template_1in_a1mini.stl` – generated model

## Backends

The script supports two output backends:

1. **build123d backend (preferred):**
   - Creates a rectangular plate and subtracts dashed/Y cut-through slots.
2. **Fallback STL backend (automatic when build123d is unavailable):**
   - Emits a printable line-template lattice directly as an STL mesh.

This keeps generation working in restricted environments while preserving the 1-inch hex layout style.

## Requirements

- Python 3.10+
- Optional: `build123d` (for the preferred subtractive plate version)

Example install:

```bash
pip install build123d
```

## Generate STL

```bash
python hex_grid_template.py
```

This writes:

- `hex_grid_template_1in_a1mini.stl`

The script prints which backend was used.

## Render STL preview image

To create an SVG preview suitable for the README:

```bash
python render_stl_preview.py
```

This writes:

- `assets/hex_grid_template_preview.svg`

No third-party packages are required; the renderer only uses the Python standard library.

## Model preview

![Hex grid template STL preview](assets/hex_grid_template_preview.svg)

## Tuning parameters

Edit `StencilConfig` in `hex_grid_template.py`:

- `width`, `height`, `thickness`
- `hex_flat_to_flat` (default 25.4 mm)
- `slot_width`
- `edge_gap_from_vertex`
- `vertex_arm_length`
- `border`

## Suggested PLA print settings (starting point)

- Layer height: `0.20 mm`
- Wall loops: `3`
- Top/bottom layers: `4`
- Infill: `15–25%` (for plate variants)
- Brim: optional (2–4 mm) if bed adhesion is weak
- No supports

Tip: use a fine-tip pen and keep the template flat on paper for best line consistency.
