#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p output logs build

echo "Generating scenarios..."
python3 config/generate_scenarios.py

echo "Building..."
cmake -B build -DCMAKE_BUILD_TYPE=Release . -Wno-dev > logs/cmake.log 2>&1
cmake --build build --parallel 4 > logs/build.log 2>&1
echo "Build done."

SIM=50
run_test() {
    name=$1
    desc=$2
    echo ""
    echo "--- $name : $desc"
    if ./build/wildfire "config/${name}.json" $SIM "output/${name}.csv" > "logs/${name}.log" 2>&1; then
        lines=$(wc -l < "output/${name}.csv" 2>/dev/null || echo 0)
        echo "    OK -> output/${name}.csv  ($lines lines)"
    else
        echo "    FAILED - see logs/${name}.log"
        cat "logs/${name}.log"
    fi
}

run_test test1_no_wind        "No wind - circular spread"
run_test test2_wind           "NW wind 10m/s - elongated spread"
run_test test3_fuel           "Firebreaks"
run_test test4_moisture       "Moisture suppression"
run_test test5_topography     "Slope effect"
run_test test6_inhomogeneous  "Inhomogeneous R zones"
run_test test7_incombustible  "Incombustible obstacle"

echo ""
echo "All done. CSVs in output/"
ls -lh output/*.csv 2>/dev/null
