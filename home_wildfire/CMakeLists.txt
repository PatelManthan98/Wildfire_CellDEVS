cmake_minimum_required(VERSION 3.16)
project(wildfire_celldevs LANGUAGES CXX)

# ── C++17 required for Cadmium v2 ─────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Build type ────────────────────────────────────────────────────────────────
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ── Locate Cadmium v2 ─────────────────────────────────────────────────────────
# Looks in ~/cadmium_v2 by default (adjust if your installation is elsewhere).
# Override from command line:
#   cmake -B build . -DCADMIUM_DIR=/path/to/cadmium_v2
if(NOT DEFINED CADMIUM_DIR)
    set(CADMIUM_DIR "$ENV{HOME}/cadmium_v2" CACHE PATH "Path to cadmium_v2 root")
endif()

# Verify the key header exists so we get a clear error message
if(NOT EXISTS "${CADMIUM_DIR}/include/cadmium/celldevs/grid/cell.hpp")
    message(FATAL_ERROR
        "Cadmium v2 headers not found at ${CADMIUM_DIR}/include.\n"
        "Please set CADMIUM_DIR:\n"
        "  cmake -B build . -DCADMIUM_DIR=/path/to/cadmium_v2\n"
        "Or ensure cadmium_v2 is cloned at ~/cadmium_v2 with submodules:\n"
        "  git clone --recursive https://github.com/SimulationEverywhere/cadmium_v2.git ~/cadmium_v2"
    )
endif()

# ── Include paths ─────────────────────────────────────────────────────────────
include_directories(
    ${CADMIUM_DIR}/include          # cadmium/celldevs/*, cadmium/core/*
    ${CADMIUM_DIR}/json/include     # nlohmann/json.hpp
    ${CMAKE_SOURCE_DIR}             # allows #include "include/wildfire_cell.hpp"
    ${CMAKE_SOURCE_DIR}/include     # allows #include "wildfire_cell.hpp"
)

# ── Wildfire simulation executable ───────────────────────────────────────────
add_executable(wildfire main.cpp)

# ── Compiler warnings ─────────────────────────────────────────────────────────
target_compile_options(wildfire PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -O2>
)

# ── Print build instructions ──────────────────────────────────────────────────
message(STATUS "")
message(STATUS "  Cadmium v2 path : ${CADMIUM_DIR}")
message(STATUS "")
message(STATUS "  Build:")
message(STATUS "    mkdir -p build && cd build")
message(STATUS "    cmake .. && make -j4")
message(STATUS "")
message(STATUS "  Generate scenario files (one-time):")
message(STATUS "    python3 config/generate_scenarios.py")
message(STATUS "")
message(STATUS "  Run all tests:")
message(STATUS "    bash scripts/run_all.sh")
message(STATUS "")
message(STATUS "  Run a single test:")
message(STATUS "    ./wildfire config/test1_no_wind.json 50")
message(STATUS "")
