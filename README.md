# Wildfire Propagation Simulation (Cell-DEVS)

This project implements a forest fire spread model based on the **Karafyllidis & Thanailakis (1997)** cellular automata formalism using the **Cadmium CD++ framework**. It simulates how fire propagates across a 2D grid based on fuel load, moisture, elevation, and neighborhood interactions.

---

## 🌲 Model Description

The system is modeled as a **101×101 grid** where each cell represents a **10m × 10m** patch of forest.

### State Variables

| Variable | Description |
|----------|-------------|
| **Burned Ratio** | Continuous value from `0.0` (unburned) to `1.0` (fully consumed) |
| **Fuel Load** | Remaining biomass available to burn |
| **Elevation** | Terrain height influencing spread direction |
| **Moisture** | Dampness level suppressing ignition probability |

### Transition Logic

The model uses a **Moore Neighborhood** (8 neighbors). A cell's ignition is probabilistic and depends on the state of its neighbors:

```
spread_prob = R_base × Σ(Neighbors_burned)
```

**State Flow:** `UNBURNED → BURNING → BURNED`

---

## 🚀 Getting Started

### Prerequisites

- C++17 Compiler (GCC 7+ or Clang)
- CMake 3.10+
- Python 3.x (for visualization)
- Cadmium Library (headers must be in the include path)
- Python packages: `numpy`, `matplotlib`

```bash
pip install numpy matplotlib
```

### Build Instructions

From the project root directory:

```bash
# source build_sim.sh
```

The executable `wildfire` will be created in the `build/` directory.

---

## 🏃 Running Simulations

### Single Experiment

Run the binary with a simulation time (in hours) and a configuration file:

```bash
./build/wildfire config/wildfire_config.json 200
```

### All Experiments

Each test has its own config file. Run them all with:

```bash
./build/wildfire config/test1_no_wind.json 200
./build/wildfire config/test2_wind.json 200
./build/wildfire config/test3_fuel.json 200
./build/wildfire config/test4_moisture.json 200
./build/wildfire config/test5_topography.json 200
./build/wildfire config/test6_inhomogeneous.json 200
./build/wildfire config/test7_incombustible.json 200
```

### Output Format

Each simulation generates a CSV file in the `output/` folder with the format:

```
time;model_id;(row,col);port;burned;fuel;elevation;moisture
```

---

## 📊 Visualization

### Animate a Single Experiment

```bash
python3 scripts/visualize.py output/test1_no_wind.csv --fps 5
```

### Save a Single Experiment as GIF

```bash
python3 scripts/visualize.py output/test1_no_wind.csv --save --fps 5
```

The GIF is saved to `output/test1_no_wind.gif`.

### Save All Experiments as GIFs

```bash
for f in output/test*.csv; do python3 scripts/visualize.py "$f" --save --fps 5; done
```

### Visualizer Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `csv_file` | *(required)* | Path to the simulation CSV |
| `--save` | off | Save animation as GIF instead of displaying |
| `--fps` | `5` | Frames per second |
| `--rows` | `100` | Grid row count |
| `--cols` | `100` | Grid column count |

### Terminal ASCII Visualizer

```bash
python3 live_fire.py
```

**Legend:**

| Symbol | Meaning |
|--------|---------|
| `#` | Active fire / fully burned |
| `*` | Currently spreading |
| `.` | Healthy forest |

---


## 🧪 Experiments

| Test | Config | Description |
|------|--------|-------------|
| `test1_no_wind` | Baseline | Uniform fuel, no wind, flat terrain |
| `test2_wind` | Wind | Directional wind bias applied |
| `test3_fuel` | Fuel variation | Non-uniform fuel load distribution |
| `test4_moisture` | Moisture | High moisture zones suppressing spread |
| `test5_topography` | Elevation | Sloped terrain influencing propagation |
| `test6_inhomogeneous` | Mixed | Combined heterogeneous environment |
| `test7_incombustible` | Firebreak | Incombustible cells acting as barriers |

---

## 📚 References

- Karafyllidis, I., & Thanailakis, A. (1997). *A model for predicting forest fire spreading using cellular automata*. Ecological Modelling, 99(1), 87–97.
- Cadmium DEVS Framework: [https://github.com/SimulationEverywhere/cadmium](https://github.com/SimulationEverywhere/cadmium)
