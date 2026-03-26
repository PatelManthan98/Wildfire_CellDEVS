Wildfire Propagation Simulation (Cell-DEVS)
This project implements a forest fire spread model based on the Karafyllidis & Thanailakis (1997) cellular automata formalism using the Cadmium CD++ framework. It simulates how fire propagates across a 2D grid based on fuel load, moisture, and neighborhood interactions.

🌲 Model Description
The system is modeled as a 101×101 grid where each cell represents a 10m × 10m patch of forest.

State Variables
Burned Ratio: A continuous value from 0.0 (unburned) to 1.0 (fully consumed).

Fuel Load: Remaining biomass available to burn.

Environmental Factors: Support for elevation and moisture levels per cell.

Transition Logic
The model uses a Moore Neighborhood (8 neighbors). A cell's ignition is probabilistic and depends on the state of its neighbors:

Spread Rule: spread_prob = R_base * Σ(Neighbors_burned)

State Flow: UNBURNED → BURNING → BURNED

🚀 Getting Started
Prerequisites
C++17 Compiler (GCC 7+ or Clang)

CMake (3.10+)

Python 3.x (for visualization)

Cadmium Library (Headers must be in the include path)

Build Instructions
From the project root directory, run the following commands:

Bash
# 1. Create and enter the build directory
mkdir -p build
cd build

# 2. Configure and Compile
cmake ..
make -j4
The executable wildfire will be created in the build/ directory.

🏃 Running Simulations
To run the simulation, execute the binary with the desired simulation time (in hours) and the configuration file:

Bash
./build/wildfire config/wildfire_config.json 200
Output
The simulation generates a wildfire_results.csv file. The data is formatted as:
Time; Cell_Coordinates; Burned_Ratio; Fuel; Elevation; Moisture

📊 Visualization
To visualize the fire spread in your terminal as an animated ASCII matrix:

Bash
# Run the visualizer from the project root
python3 live_fire.py
Legend:

#  Active Fire / Fully Burned Area

* : Currently Spreading

. : Healthy Forest

📂 Project Structure
main.cpp - Entry point and simulation coordinator setup.

wildfire_cell.hpp - Core transition logic and spread equations.

state.hpp - Definition of the Cell-DEVS state and CSV output format.

live_fire.py - Terminal-based animation script.

config/ - JSON configuration files for different scenarios (Wind, No-Wind, etc.).


Framework: Cadmium DEVS

Reference Paper: Karafyllidis, I., & Thanailakis, A. (1997). "A model for predicting forest fire spreading using cellular automata".
