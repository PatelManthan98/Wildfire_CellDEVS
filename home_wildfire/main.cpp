/**
 * main.cpp
 * ────────
 * Wildfire Propagation Cell-DEVS  —  Cadmium v2 simulation runner.
 * Based on Karafyllidis & Thanailakis (1997), Ecological Modelling 99, 87–97.
 *
 * Usage:
 *   ./wildfire <scenario.json> [simulation_hours]
 *
 * Examples:
 *   ./wildfire config/test1_no_wind.json 50
 *   ./wildfire config/test2_wind.json    50
 *   ./wildfire config/test3_fuel.json    50
 *   ./wildfire config/test4_moisture.json  50
 *   ./wildfire config/test5_topography.json 50
 *   ./wildfire config/test6_inhomogeneous.json 50
 *   ./wildfire config/test7_incombustible.json 50
 *
 * Output:
 *   wildfire_log.csv  — Cadmium v2 simulation log (semicolon-delimited)
 */

// ── Cadmium v2 headers ────────────────────────────────────────────────────────
#include <cadmium/celldevs/grid/coupled.hpp>
#include <cadmium/core/logger/csv.hpp>
#include <cadmium/core/simulation/root_coordinator.hpp>

// ── Standard library ──────────────────────────────────────────────────────────
#include <chrono>
#include <iostream>
#include <memory>
#include <string>

// ── Project headers ───────────────────────────────────────────────────────────
#include "include/wildfire_state.hpp"
#include "include/wildfire_cell.hpp"

using namespace cadmium::celldevs;

// ─────────────────────────────────────────────────────────────────────────────
// Factory function
// ─────────────────────────────────────────────────────────────────────────────
// Cadmium v2 GridCellDEVSCoupled calls this for every cell in the grid.
// The exact signature must match:
//   std::shared_ptr<GridCell<S,V>>(*)(const coordinates&,
//                                     const std::shared_ptr<const GridCellConfig<S,V>>&)
//
// We have only one cell type (WildfireCell) so we always return it.
// If you add specialised cells (e.g., observer cells), add branches here.
// ─────────────────────────────────────────────────────────────────────────────
std::shared_ptr<GridCell<WildfireState, double>> addWildfireCell(
    const coordinates& cellId,
    const std::shared_ptr<const GridCellConfig<WildfireState, double>>& cellConfig)
{
    return std::make_shared<WildfireCell>(cellId, cellConfig);
}

// ─────────────────────────────────────────────────────────────────────────────
int main(int argc, char** argv) {

    if (argc < 2) {
        std::cout << "Wildfire Cell-DEVS Simulator (Karafyllidis 1997)\n"
                  << "Usage: " << argv[0] << " <scenario.json> [sim_hours=50]\n\n"
                  << "Example:\n"
                  << "  " << argv[0] << " config/test1_no_wind.json 50\n";
        return 1;
    }

    std::string scenarioFile = argv[1];
    double      simHours     = (argc > 2) ? std::stod(argv[2]) : 50.0;

    std::cout << "══════════════════════════════════════════════════\n"
              << "  Wildfire Cell-DEVS  (Karafyllidis & Thanailakis 1997)\n"
              << "  Scenario : " << scenarioFile   << "\n"
              << "  Duration : " << simHours << " hours\n"
              << "══════════════════════════════════════════════════\n\n";

    try {
        // ── 1. Build coupled Cell-DEVS model from JSON scenario ───────────────
        auto t0 = std::chrono::high_resolution_clock::now();

        auto model = std::make_shared<GridCellDEVSCoupled<WildfireState, double>>(
            "wildfire",      // model ID (appears in log file cell paths)
            addWildfireCell, // factory function
            scenarioFile     // path to scenario JSON
        );
        model->buildModel();

        auto t1 = std::chrono::high_resolution_clock::now();
        std::cout << "Model build time: "
                  << std::chrono::duration<double>(t1 - t0).count()
                  << " s\n";

        // ── 2. Set up root coordinator + CSV logger ───────────────────────────
        auto rootCoord = cadmium::RootCoordinator(model);
        auto logger    = std::make_shared<cadmium::CSVLogger>("wildfire_log.csv", ";");
        rootCoord.setLogger(logger);

        // ── 3. Run simulation ─────────────────────────────────────────────────
        rootCoord.start();
        auto t2 = std::chrono::high_resolution_clock::now();

        rootCoord.simulate(simHours);

        auto t3 = std::chrono::high_resolution_clock::now();
        rootCoord.stop();

        std::cout << "Simulation time: "
                  << std::chrono::duration<double>(t3 - t2).count()
                  << " s\n";
        std::cout << "\nOutput written to: wildfire_log.csv\n";
        std::cout << "Visualise with:\n"
                  << "  python3 scripts/visualize.py wildfire_log.csv\n";

    } catch (const std::exception& e) {
        std::cerr << "[ERROR] " << e.what() << "\n";
        return 1;
    }

    return 0;
}
