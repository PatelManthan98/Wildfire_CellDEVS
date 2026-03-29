#!/usr/bin/env python3
"""
visualize.py
CSV format: time;model_id;(row,col);port;burned;fuel;elevation;moisture
Usage: python3 scripts/visualize.py output/test1_no_wind.csv [--save] [--fps 5]
to generate the animatio for all experiment run this command:for f in output/test*.csv; do python3 scripts/visualize.py "$f" --save --fps 5; done
"""
import sys, re, argparse, os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument("csv_file")
parser.add_argument("--save", action="store_true")
parser.add_argument("--fps",  type=int, default=5)
parser.add_argument("--rows", type=int, default=100)
parser.add_argument("--cols", type=int, default=100)
args = parser.parse_args()

ROWS, COLS = args.rows, args.cols
coord_re   = re.compile(r'\((\d+),\s*(\d+)\)')

# raw[t][(r,c)] = burned value
raw = defaultdict(dict)

print(f"Reading {args.csv_file} ...")
count = 0
with open(args.csv_file) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("time"):
            continue
        # Split on semicolons — format has 8 fields:
        # [0]time [1]model_id [2](row,col) [3]port [4]burned [5]fuel [6]elev [7]moist
        p = line.split(";")
        if len(p) < 5:
            continue
        # Parse time
        try:
            t = float(p[0])
        except ValueError:
            continue
        # Parse coordinates from field 2
        m = coord_re.search(p[2])
        if not m:
            continue
        r, c = int(m.group(1)), int(m.group(2))
        if not (0 <= r < ROWS and 0 <= c < COLS):
            continue
        # Parse burned from field 4
        try:
            burned = float(p[4])
        except (ValueError, IndexError):
            continue
        raw[t][(r, c)] = burned
        count += 1

print(f"  Parsed {count} records, {len(raw)} time steps")

if not raw:
    print("[ERROR] No records parsed. Printing first 3 data lines for debug:")
    with open(args.csv_file) as f:
        for i, line in enumerate(f):
            if i > 3: break
            print(f"  [{i}] {repr(line.strip())}")
    sys.exit(1)

times = sorted(raw.keys())
print(f"  t in [{times[0]:.1f}, {times[-1]:.1f}] hours")

# Build accumulated frames (burned is monotone non-decreasing)
accumulated = np.zeros((ROWS, COLS))
frames = []
for t in times:
    for (r, c), b in raw[t].items():
        if b > accumulated[r, c]:
            accumulated[r, c] = b
    frames.append((t, accumulated.copy()))

print(f"  {len(frames)} frames built. Max burned = {accumulated.max():.3f}")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax_map, ax_area) = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle("Wildfire Cell-DEVS  (Karafyllidis & Thanailakis 1997)", fontsize=12)

cmap = plt.cm.hot_r
im   = ax_map.imshow(frames[0][1], vmin=0, vmax=1, cmap=cmap,
                     origin="upper", extent=[0, COLS*10, ROWS*10, 0])
plt.colorbar(im, ax=ax_map, label="Burned ratio S_{i,j}")
ax_map.set_xlabel("East [m]")
ax_map.set_ylabel("North [m]")
title = ax_map.set_title("")

def area_km2(grid):
    return np.sum(grid >= 1.0) * 100 / 1e6

burned_areas = [area_km2(g) for _, g in frames]
max_area = max(burned_areas) if max(burned_areas) > 0 else 0.01
ax_area.set_xlim(times[0], times[-1])
ax_area.set_ylim(0, max_area * 1.2)
ax_area.set_xlabel("Time [hours]")
ax_area.set_ylabel("Fully burned area [km²]")
ax_area.set_title("Cumulative burned area")
ax_area.grid(True, alpha=0.3)
line_plot, = ax_area.plot([], [], "r-", lw=2)
vline = ax_area.axvline(x=0, color="grey", ls="--", lw=1)

def update(i):
    t, grid = frames[i]
    im.set_data(grid)
    burning = int(np.sum((grid > 0) & (grid < 1)))
    burned  = int(np.sum(grid >= 1.0))
    title.set_text(f"t={t:.1f}h  |  burning:{burning}  |  fully burned:{burned}")
    line_plot.set_data([frames[j][0] for j in range(i+1)],
                       [area_km2(frames[j][1]) for j in range(i+1)])
    vline.set_xdata([t])
    return im, title, line_plot, vline

ani = animation.FuncAnimation(fig, update, frames=len(frames),
                               interval=1000//args.fps, blit=False)
plt.tight_layout()

if args.save:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(args.csv_file)))
    out = os.path.join(project_root, "output", os.path.basename(args.csv_file).replace(".csv", ".gif"))
    print(f"Saving → {out}")
    ani.save(out, writer="pillow", fps=args.fps)
    print("Done.")
else:
    plt.show()
