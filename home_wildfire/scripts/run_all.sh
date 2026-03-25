#!/usr/bin/env bash
# =============================================================================
# run_all.sh
# ──────────
# Builds the wildfire Cell-DEVS model and runs all 7 validation scenarios.
#
# Usage (from project root):
#   chmod +x scripts/run_all.sh
#   bash scripts/run_all.sh
#
# Prerequisites:
#   - CMake >= 3.16, g++ with C++17 support
#   - Cadmium v2 at ~/cadmium_v2 (with submodules, i.e. json/ present)
#   - Python 3 (for scenario generation and visualisation)
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()   { echo -e "${GREEN}[ OK ]${NC}  $*"; }
fail() { echo -e "${RED}[FAIL]${NC}  $*"; }

echo "══════════════════════════════════════════════════════════"
echo " Wildfire Cell-DEVS  —  Karafyllidis & Thanailakis 1997"
echo " Cadmium v2 | Full Test Suite"
echo "══════════════════════════════════════════════════════════"
echo ""

# ── Step 1: Generate scenario JSON files ─────────────────────────────────────
info "Generating scenario JSON files..."
python3 config/generate_scenarios.py
echo ""

# ── Step 2: Build ─────────────────────────────────────────────────────────────
info "Building project..."
mkdir -p build
cmake -B build -DCMAKE_BUILD_TYPE=Release . -Wno-dev > logs/cmake.log 2>&1
cmake --build build --parallel 4 > logs/build.log 2>&1
ok "Build complete  →  ./build/wildfire"
echo ""

# ── Step 3: Run each test ─────────────────────────────────────────────────────
SIM_HOURS=50
declare -a TESTS=(
    "test1_no_wind:No wind — circular spread (Fig. 3)"
    "test2_wind:NW wind 10 m/s — elongated SE spread"
    "test3_fuel:Firebreaks — fire stops/slows at low-fuel strips"
    "test4_moisture:Moisture — wet quadrant suppresses fire"
    "test5_topography:Topography — faster uphill, slower downhill"
    "test6_inhomogeneous:Inhomogeneous forest R1>R2 (Fig. 4)"
    "test7_incombustible:Incombustible obstacle, fire wraps (Fig. 5)"
)

mkdir -p logs output

PASSED=0; FAILED=0
for entry in "${TESTS[@]}"; do
    name="${entry%%:*}"
    desc="${entry#*:}"
    info "Running: $name"
    echo "         $desc"

    log_file="logs/${name}.log"
    if ./build/wildfire "config/${name}.json" $SIM_HOURS > "$log_file" 2>&1; then
        mv wildfire_log.csv "output/${name}.csv" 2>/dev/null || true
        ok "  → output/${name}.csv"
        ((PASSED++))
    else
        fail "  Simulation failed — see $log_file"
        ((FAILED++))
    fi
    echo ""
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo "══════════════════════════════════════════════════════════"
echo -e " Passed: ${GREEN}${PASSED}${NC}  /  Failed: ${RED}${FAILED}${NC}"
echo "══════════════════════════════════════════════════════════"
echo ""
echo " To visualise a result:"
echo "   python3 scripts/visualize.py output/test1_no_wind.csv"
echo ""
echo " To convert for the ARSLab Web Viewer:"
echo "   python3 scripts/convert_to_webviewer.py output/test1_no_wind.csv"
echo ""
