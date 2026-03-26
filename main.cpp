#include <iostream>
#include <string>
#include <memory>

// Corrected Cadmium V2 includes
#include <cadmium/celldevs/grid/coupled.hpp>
#include <cadmium/core/logger/csv.hpp>
#include <cadmium/core/simulation/root_coordinator.hpp>

#include "include/wildfire_state.hpp"
#include "include/wildfire_cell.hpp"

using namespace cadmium::celldevs;
using namespace cadmium;

std::shared_ptr<GridCell<WildfireState, double>> addWildfireCell(
    const coordinates & cellId, 
    const std::shared_ptr<const GridCellConfig<WildfireState, double>>& cellConfig) 
{
    return std::make_shared<WildfireCell>(cellId, cellConfig);
}

int main(int argc, char ** argv) {
    std::string configFilePath = (argc > 1) ? argv[1] : "config/test1_no_wind.json";
    double simTime = (argc > 2) ? std::stod(argv[2]) : 50.0;
    std::string outputFilePath = (argc > 3) ? argv[3] : "wildfire_output.csv";

    try {
        auto model = std::make_shared<GridCellDEVSCoupled<WildfireState, double>>(
            "wildfire_model", addWildfireCell, configFilePath);
        model->buildModel();
        
        auto rootCoordinator = RootCoordinator(model);
        
        // Note: CSVLogger is usually in cadmium::core or cadmium namespace
        auto logger = std::make_shared<CSVLogger>(outputFilePath, ";");
        rootCoordinator.setLogger(logger);
        
        rootCoordinator.start();
        rootCoordinator.simulate(simTime);
        rootCoordinator.stop();

        std::cout << "Simulation complete. Results: " << outputFilePath << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}