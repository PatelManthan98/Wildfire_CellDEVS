#!/usr/bin/env python3
"""
generate_scenarios.py
─────────────────────
Generates Cadmium v2 Cell-DEVS JSON scenario files for all 7 wildfire
validation test cases.

Run this ONCE before building / running the simulation:
    python3 config/generate_scenarios.py

Output files (in the same config/ directory):
    test1_no_wind.json        No wind, circular spread (Karafyllidis Fig. 3)
    test2_wind.json           Wind 10 m/s NW, elongated spread
    test3_fuel.json           Fuel variation / firebreaks
    test4_moisture.json       High moisture suppresses fire
    test5_topography.json     N–S slope, faster uphill
    test6_inhomogeneous.json  Two R-zones  (Karafyllidis Fig. 4)
    test7_incombustible.json  Solid obstacle (Karafyllidis Fig. 5)

JSON format (Cadmium v2 GridCellDEVSCoupled):
    {
      "scenario": {
        "shape":   [ROWS, COLS],
        "origin":  [0, 0],        # top-left cell coordinates
        "wrapped": false
      },
      "cells": {
        "default": {
          "delay": "inertial",
          "state": { burned, fuel, elevation, moisture },
          "config": { wind_speed, wind_direction, cell_size, R_base, time_step },
          "neighborhood": [{"type": "moore", "range": 1}]
        },
        "<name>": {
          # PATCH applied on top of default via JSON merge-patch
          # Only specify fields that differ from default
          "state": { ... },       # partial state — merged with default state
          "cell_map": [[r, c], ...]   # which cells get this config
        }
      }
    }

Notes:
  - Non-default configs PATCH the default.  Unspecified fields keep default values.
  - cell_map lists absolute [row, col] coordinates (must be within shape).
  - The "config" section maps to cellConfig->rawCellConfig in WildfireCell.
  - Env params (wind etc.) are shared across all cells in a scenario.
"""

import json
import os
import math

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS, COLS      = 100, 100
ORIGIN_R        = 50    # fire ignition row
ORIGIN_C        = 50    # fire ignition col

# ── Default environment parameters ───────────────────────────────────────────
BASE_ENV = {
    "wind_speed":     0.0,
    "wind_direction": 315.0,   # NW (degrees, FROM direction)
    "cell_size":      10.0,    # metres
    "R_base":         0.00278, # m/s  ≈ 10 m/h  → t_a = 10/0.00278 ≈ 3600 s = 1 h
    "time_step":      1.0      # hours per step
}

# Default state for unburned cells
DEFAULT_STATE = {
    "burned":    0.0,
    "fuel":      15.0,
    "elevation": 0.0,
    "moisture":  30.0
}

# Fully-burned initial cell (fire origin)
IGNITION_STATE = {
    "burned":    1.0,
    "fuel":      0.0,
    "elevation": 0.0,
    "moisture":  30.0
}

def base_scenario(env, default_state=None, cells_extra=None):
    """Build a minimal Cadmium v2 scenario dict."""
    if default_state is None:
        default_state = DEFAULT_STATE.copy()
    scenario = {
        "scenario": {
            "shape":   [ROWS, COLS],
            "origin":  [0, 0],
            "wrapped": False
        },
        "cells": {
            "default": {
                "delay": "inertial",
                "state": default_state,
                "config": env,
                "neighborhood": [{"type": "moore", "range": 1}]
            }
        }
    }
    if cells_extra:
        scenario["cells"].update(cells_extra)
    return scenario


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — No wind, uniform fuel, flat terrain
# Expected: symmetric circular fire front (Karafyllidis Fig. 3)
# ─────────────────────────────────────────────────────────────────────────────
def test1_no_wind():
    env = {**BASE_ENV, "wind_speed": 0.0}
    extra = {
        "ignition": {
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Wind 10 m/s from NW (315°), flat, uniform fuel
# Expected: elliptical front elongated toward SE (downwind)
# ─────────────────────────────────────────────────────────────────────────────
def test2_wind():
    env = {**BASE_ENV, "wind_speed": 10.0, "wind_direction": 315.0}
    extra = {
        "ignition": {
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Fuel variation / firebreaks, no wind
#
# Firebreak 1: zero-fuel vertical strip at col 62  → complete barrier
# Firebreak 2: low-fuel vertical strip at col 70   → partial barrier
# Expected: fire stops at col 62, slows at col 70
# ─────────────────────────────────────────────────────────────────────────────
def test3_fuel():
    env = {**BASE_ENV, "wind_speed": 0.0}
    extra = {
        "ignition": {
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        },
        # Complete firebreak: fuel=0 → R=0 → never ignites
        "firebreak_zero": {
            "state": {"burned": 0.0, "fuel": 0.0, "elevation": 0.0, "moisture": 30.0},
            "cell_map": [[r, 62] for r in range(ROWS)]
        },
        # Partial barrier: fuel=3 kg/m² → R reduced to 20% → slow crossing
        "firebreak_low": {
            "state": {"burned": 0.0, "fuel": 3.0, "elevation": 0.0, "moisture": 30.0},
            "cell_map": [[r, 70] for r in range(ROWS)]
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Moisture effect, no wind
#
# NW quadrant (rows 0-49, cols 0-49): moisture = 90% RH
# moisture_factor = 1 - 90/100 = 0.10 → R reduced to 10% of normal
# Expected: fire does NOT propagate meaningfully into the wet quadrant
# ─────────────────────────────────────────────────────────────────────────────
def test4_moisture():
    env = {**BASE_ENV, "wind_speed": 0.0}
    # Build wet-zone cell_map (exclude origin)
    wet_cells = [
        [r, c]
        for r in range(50) for c in range(50)
        if not (r == ORIGIN_R and c == ORIGIN_C)
    ]
    extra = {
        "ignition": {
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        },
        "wet_zone": {
            # Only patch moisture; other fields inherit from default
            "state": {"burned": 0.0, "fuel": 15.0, "elevation": 0.0, "moisture": 90.0},
            "cell_map": wet_cells
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Topography, no wind
#
# N–S linear gradient: row 0 (north) = 297 m;  row 99 (south) = 0 m
# elevation = (99 − row) × 3  [m]
#
# Implemented as 10 elevation bands (10 rows each) to keep JSON manageable.
# Band i covers rows [10i … 10i+9], elevation = avg of that range.
#
# Expected: fire spreads faster northward (uphill), slower southward (downhill)
# ─────────────────────────────────────────────────────────────────────────────
def test5_topography():
    env = {**BASE_ENV, "wind_speed": 0.0}
    extra = {}

    # 10 bands × 10 rows each
    for band in range(10):
        row_start = band * 10
        row_end   = row_start + 10
        # Use the average elevation for this band
        avg_elev  = (((99 - row_start) + (99 - (row_end - 1))) / 2.0) * 3.0

        cells = [
            [r, c]
            for r in range(row_start, row_end)
            for c in range(COLS)
            if not (r == ORIGIN_R and c == ORIGIN_C)
        ]
        band_name = f"elevation_band_{band}"
        extra[band_name] = {
            "state": {
                "burned":    0.0,
                "fuel":      15.0,
                "elevation": round(avg_elev, 1),
                "moisture":  30.0
            },
            "cell_map": cells
        }

    # Fire origin (mid-slope at band 5, elevation ≈ 148.5 m)
    origin_elev = ((99 - ORIGIN_R) * 3.0)
    extra["ignition"] = {
        "state": {
            "burned":    1.0,
            "fuel":      0.0,
            "elevation": origin_elev,
            "moisture":  30.0
        },
        "cell_map": [[ORIGIN_R, ORIGIN_C]]
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Inhomogeneous forest  (Karafyllidis Fig. 4)
#
# Two zones with different spread rates R₁ > R₂:
#   Outer zone: fuel = 15 kg/m²  →  R₁ = R_base × 1.0
#   Inner zone (rows 30–69, cols 30–69): fuel = 6 kg/m²  →  R₂ ≈ 0.4 × R₁
#
# Expected: compressed (slower) fire fronts inside inner zone, circular outside.
# Matches Karafyllidis Fig. 4(b).
# ─────────────────────────────────────────────────────────────────────────────
def test6_inhomogeneous():
    env = {**BASE_ENV, "wind_speed": 0.0}
    # Inner slow zone
    inner_cells = [
        [r, c]
        for r in range(30, 70) for c in range(30, 70)
        if not (r == ORIGIN_R and c == ORIGIN_C)
    ]
    extra = {
        "inner_slow_zone": {
            "state": {"burned": 0.0, "fuel": 6.0, "elevation": 0.0, "moisture": 30.0},
            "cell_map": inner_cells
        },
        "ignition": {
            # Origin is inside the slow zone
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Incombustible obstacle  (Karafyllidis Fig. 5)
#
# A solid rectangular obstacle (fuel=0, moisture=100%) is placed east of the
# ignition point.  R = 0 → obstacle never ignites → fire wraps around it.
#
# Obstacle: rows 38–57, cols 55–63  (20 rows × 9 cols)
# Expected: fire fronts diffract around both sides; shadow zone behind joins.
# Matches Karafyllidis Fig. 5(b).
# ─────────────────────────────────────────────────────────────────────────────
def test7_incombustible():
    env = {**BASE_ENV, "wind_speed": 0.0}
    obstacle_cells = [
        [r, c]
        for r in range(38, 58) for c in range(55, 64)
    ]
    extra = {
        "obstacle": {
            # fuel=0 → R=0 → incombustible.  moisture=100 as belt-and-braces.
            "state": {"burned": 0.0, "fuel": 0.0, "elevation": 0.0, "moisture": 100.0},
            "cell_map": obstacle_cells
        },
        "ignition": {
            "state": IGNITION_STATE.copy(),
            "cell_map": [[ORIGIN_R, ORIGIN_C]]
        }
    }
    return base_scenario(env, cells_extra=extra)


# ─────────────────────────────────────────────────────────────────────────────
# Write all scenarios
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS = {
    "test1_no_wind":       (test1_no_wind,       "No wind — circular spread"),
    "test2_wind":          (test2_wind,           "NW wind — elongated SE spread"),
    "test3_fuel":          (test3_fuel,           "Firebreaks"),
    "test4_moisture":      (test4_moisture,       "Moisture suppression"),
    "test5_topography":    (test5_topography,     "N-S slope effect"),
    "test6_inhomogeneous": (test6_inhomogeneous,  "Inhomogeneous R zones (Fig. 4)"),
    "test7_incombustible": (test7_incombustible,  "Incombustible obstacle (Fig. 5)"),
}

print("Generating Cadmium v2 scenario JSON files...\n")
for name, (fn, desc) in SCENARIOS.items():
    path = os.path.join(OUT_DIR, f"{name}.json")
    scenario = fn()
    with open(path, "w") as f:
        json.dump(scenario, f, indent=2)
    n_extra = len(scenario["cells"]) - 1   # subtract "default"
    print(f"  ✓  {name}.json  ({n_extra} extra config(s))  —  {desc}")

print(f"\nAll 7 scenario files written to {OUT_DIR}/")
print("\nBuild and run:")
print("  mkdir -p build && cd build && cmake .. && make -j4 && cd ..")
print("  ./build/wildfire config/test1_no_wind.json 50")
