#!/usr/bin/env python3
"""
visualize.py
────────────
Reads a Cadmium v2 Cell-DEVS CSV log and renders an animated wildfire heatmap.

Usage:
    python3 scripts/visualize.py <csv_file> [--save] [--fps 4]

Install deps (if needed):
    pip install matplotlib numpy
"""

import sys, re, argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument("csv_file")
parser.add_argument("--save",  action="store_true", help="Save as GIF")
parser.add_argument("--fps",   type=int, default=4)
parser.add_argument("--rows",  type=int, default=100)
parser.add_argument("--cols",  type=int, default=100)
args = parser.parse_args()

ROWS, COLS = args.rows, args.cols

# ── Parse CSV ─────────────────────────────────────────────────────────────────
# Cadmium v2 format: time;model_id;state_string
# Cell state string comes from WildfireState::operator<<:
#   burned;fuel;elevation;moisture
# Model ID format: wildfire(row,col)  or similar

# We use a regex to extract [row][col] or (row,col) from the model ID
coord_re = re.compile(r'[(\[](\d+)[,\s]+(\d+)[)\]]')

raw = defaultdict(dict)  # raw[t][(r,c)] = burned

print(f"Reading {args.csv_file} ...")
try:
    with open(args.csv_file) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(";")
            if len(parts) < 3: continue
            try:
                t = float(parts[0])
            except ValueError:
                continue  # header line
            # Find cell coordinates in the model ID
            m = coord_re.search(parts[1])
            if not m: continue
            r, c = int(m.group(1)), int(m.group(2))
            if not (0 <= r < ROWS and 0 <= c < COLS): continue
            # State is parts[2] = "burned;fuel;elevation;moisture"
            vals = parts[2].split(";")
            if len(vals) < 1: continue
            try:
                burned = float(vals[0])
            except ValueError:
                continue
            raw[t][(r, c)] = burned
except FileNotFoundError:
    print(f"[ERROR] File not found: {args.csv_file}"); sys.exit(1)

if not raw:
    print("[ERROR] No valid cell data found. Check CSV format."); sys.exit(1)

times = sorted(raw.keys())
print(f"  Steps: {len(times)},  t ∈ [{times[0]:.1f}, {times[-1]:.1f}] h")

# Build accumulated frames (burned ratio is monotonically non-decreasing)
accumulated = np.zeros((ROWS, COLS))
frames = []
for t in times:
    for (r, c), b in raw[t].items():
        accumulated[r, c] = max(accumulated[r, c], b)
    frames.append((t, accumulated.copy()))

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax_map, ax_area) = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle("Wildfire Cell-DEVS  (Karafyllidis & Thanailakis 1997)", fontsize=12)

cmap = plt.cm.hot_r
im = ax_map.imshow(frames[0][1], vmin=0, vmax=1, cmap=cmap,
                   origin="upper", extent=[0, COLS*10, ROWS*10, 0])
plt.colorbar(im, ax=ax_map, label="Burned ratio  S_{i,j}")
ax_map.set_xlabel("East [m]"); ax_map.set_ylabel("North [m]")
title = ax_map.set_title("")

# Burned area over time
def area_km2(grid): return np.sum(grid >= 1.0) * 100 / 1e6
burned_areas = [area_km2(g) for _, g in frames]
ax_area.set_xlim(times[0], times[-1])
ax_area.set_ylim(0, max(burned_areas) * 1.2 + 1e-4)
ax_area.set_xlabel("Time [hours]"); ax_area.set_ylabel("Fully burned area [km²]")
ax_area.set_title("Cumulative burned area"); ax_area.grid(True, alpha=0.3)
line, = ax_area.plot([], [], "r-", lw=2)
vline = ax_area.axvline(x=0, color="grey", ls="--", lw=1)

def update(i):
    t, grid = frames[i]
    im.set_data(grid)
    burning = int(np.sum((grid > 0) & (grid < 1)))
    burned  = int(np.sum(grid >= 1.0))
    title.set_text(f"t = {t:.1f} h  |  burning: {burning}  |  burned: {burned}")
    line.set_data([frames[j][0] for j in range(i+1)],
                  [area_km2(frames[j][1]) for j in range(i+1)])
    vline.set_xdata([t])
    return im, title, line, vline

ani = animation.FuncAnimation(fig, update, frames=len(frames),
                               interval=1000//args.fps, blit=False)
plt.tight_layout()

if args.save:
    out = args.csv_file.replace(".csv", ".gif")
    print(f"Saving → {out}")
    ani.save(out, writer="pillow", fps=args.fps)
    print("Done.")
else:
    plt.show()
