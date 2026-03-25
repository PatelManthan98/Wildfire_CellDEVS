#include <cadmium/celldevs/grid/coupled.hpp>
#include <cadmium/core/logger/csv.hpp>
#include <cadmium/core/simulation/root_coordinator.hpp>
#include <chrono>
#include <iostream>
#include <memory>
#include <string>
#include "include/wildfire_state.hpp"
#include "include/wildfire_cell.hpp"
using namespace cadmium::celldevs;

std::shared_ptr<GridCell<WildfireState, double>> addWildfireCell(
    const coordinates& cellId,
    const std::shared_ptr<const GridCellConfig<WildfireState, double>>& cellConfig)
{
    return std::make_shared<WildfireCell>(cellId, cellConfig);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0]
                  << " <scenario.json> [hours=50] [output.csv]\n";
        return 1;
    }
    std::string scenario  = argv[1];
    double      simHours  = (argc > 2) ? std::stod(argv[2]) : 50.0;
    std::string outputCSV = (argc > 3) ? argv[3] : "wildfire_log.csv";

    std::cout << "Scenario : " << scenario  << "\n"
              << "Hours    : " << simHours  << "\n"
              << "Output   : " << outputCSV << "\n\n";
    try {
        auto model = std::make_shared<GridCellDEVSCoupled<WildfireState,double>>(
                         "wildfire", addWildfireCell, scenario);
        model->buildModel();

        auto root   = cadmium::RootCoordinator(model);
        auto logger = std::make_shared<cadmium::CSVLogger>(outputCSV, ";");
        root.setLogger(logger);
        root.start();
        root.simulate(simHours);
        root.stop();
        std::cout << "Done -> " << outputCSV << "\n";
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] " << e.what() << "\n";
        return 1;
    }
    return 0;
}
