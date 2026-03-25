#ifndef WILDFIRE_CELL_HPP
#define WILDFIRE_CELL_HPP

/**
 * wildfire_cell.hpp
 * ─────────────────
 * Cadmium v2 GridCell implementation of the Karafyllidis & Thanailakis (1997)
 * wildfire cellular automaton model.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * PAPER MODEL  (Karafyllidis & Thanailakis, Ecological Modelling 99, 1997)
 * ══════════════════════════════════════════════════════════════════════════════
 *
 * STATE (eq. 1):
 *   S_{i,j}^t  =  A_burned / A_total  ∈ [0.0, 1.0]
 *   0 = unburned;   1 = fully burned out
 *
 * BURN-OUT TIMES (eqs. 3-4):
 *   t_a = a / R_{i,j}         adjacent neighbour burns out centre in t_a
 *   t_d = √2·a / R_{i,j}      diagonal neighbour burns out in t_d = √2·t_a
 *
 * LOCAL RULE (eq. 6), one step = t_a:
 *   S^{t+1}_{i,j} = S^t_{i,j}
 *     +  [ S^t_{i-1,j} + S^t_{i,j-1} + S^t_{i,j+1} + S^t_{i+1,j} ]
 *     + 0.83·[ S^t_{i-1,j-1} + S^t_{i-1,j+1} + S^t_{i+1,j-1} + S^t_{i+1,j+1} ]
 *   clamped to [0,1]
 *   0.83 = 2(√2−1)  from eq. 5 (diagonal area geometry)
 *
 * EXTENSIONS (for assignment):
 *   R_{i,j}       = R_base × fuel_factor × moisture_factor
 *   fuel_factor   = fuel / 15       (ref = medium forest)
 *   moist_factor  = 1 − moisture/100
 *   wind_factor   = exp(0.07·v·cos θ)   θ = spread vs downwind bearing
 *   slope_factor  = exp(3.533·|tan φ|^1.2)  uphill   (Rothermel)
 *               = exp(0.5·φ)               downhill
 *
 * INCOMBUSTIBLE CELLS (Fig. 5):
 *   fuel = 0 → R = 0 → cell never ignites. Fire wraps around it.
 *
 * INHOMOGENEOUS FOREST (Fig. 4):
 *   Different fuel loads give different R per zone (paper eq. 7).
 * ══════════════════════════════════════════════════════════════════════════════
 */

#include <cmath>
#include <memory>
#include <unordered_map>
#include <vector>

// Cadmium v2 Cell-DEVS headers
#include <cadmium/celldevs/grid/cell.hpp>
#include <cadmium/celldevs/grid/config.hpp>

#include "wildfire_state.hpp"

using namespace cadmium::celldevs;

// ── Environment parameters (read from JSON "config" section) ─────────────────
struct EnvConfig {
    double wind_speed;      ///< m/s
    double wind_direction;  ///< degrees, 0=North, 90=East, clockwise. FROM direction.
    double cell_size;       ///< a [m]  (paper symbol)
    double R_base;          ///< Reference fire spread rate [m/s]
    double time_step;       ///< Simulation Δt [hours per step]

    EnvConfig()
        : wind_speed(0.0), wind_direction(315.0),
          cell_size(10.0), R_base(0.00278), time_step(1.0) {}
};

// ═════════════════════════════════════════════════════════════════════════════
// WildfireCell  —  Cadmium v2 GridCell<WildfireState, double>
//
// Template params: S = WildfireState, V = double (vicinity weight, unused here)
// ═════════════════════════════════════════════════════════════════════════════
class WildfireCell : public GridCell<WildfireState, double> {
private:
    EnvConfig env;          ///< Environment parameters for this cell
    coordinates cellId_;    ///< Stored cell ID (for relative-position computation)

public:
    // ── Constructor ──────────────────────────────────────────────────────────
    // Cadmium v2 factory function calls this exact signature.
    WildfireCell(const coordinates& id,
                 const std::shared_ptr<const GridCellConfig<WildfireState, double>>& config)
        : GridCell<WildfireState, double>(id, config), cellId_(id)
    {
        // rawCellConfig is the JSON object under "config" key in the scenario file.
        // It is inherited via JSON merge-patch from the default config.
        const auto& raw = config->rawCellConfig;
        if (!raw.is_null() && raw.is_object()) {
            env.wind_speed     = raw.value("wind_speed",     0.0);
            env.wind_direction = raw.value("wind_direction", 315.0);
            env.cell_size      = raw.value("cell_size",      10.0);
            env.R_base         = raw.value("R_base",         0.00278);
            env.time_step      = raw.value("time_step",      1.0);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  Physical factor helpers
    // ─────────────────────────────────────────────────────────────────────────

    /// Fuel factor: linear, normalised to 15 kg/m² reference (medium forest)
    static double fuelFactor(double fuel) noexcept {
        return std::max(0.0, fuel / 15.0);
    }

    /// Moisture factor: 0% RH → 1.0 (max spread);  100% RH → 0.0 (no spread)
    static double moistureFactor(double moisture) noexcept {
        return std::max(0.0, 1.0 - moisture / 100.0);
    }

    /**
     * Wind enhancement factor for a given fire-spread compass bearing.
     *
     * Wind blows FROM env.wind_direction; fire is pushed toward
     *   downwind_bearing = (wind_direction + 180) mod 360.
     *
     * f_w = exp( c · cos θ ),   c = 0.07 × wind_speed
     *   θ = 0°  → spread aligned with wind → maximum enhancement
     *   θ = 180° → spread opposes wind    → maximum reduction
     */
    double windFactor(double spread_bearing_deg) const noexcept {
        if (env.wind_speed <= 0.0) return 1.0;
        double downwind = std::fmod(env.wind_direction + 180.0, 360.0);
        double diff = std::fabs(spread_bearing_deg - downwind);
        if (diff > 180.0) diff = 360.0 - diff;
        double diff_rad = diff * M_PI / 180.0;
        return std::exp(0.07 * env.wind_speed * std::cos(diff_rad));
    }

    /**
     * Slope factor (Rothermel formulation).
     *
     * dz > 0 → fire spreading uphill   → exp(3.533 · |tan φ|^1.2)
     * dz < 0 → fire spreading downhill → exp(0.5 · φ)  [mild reduction]
     *
     * @param this_elev  elevation of this (receiving) cell [m]
     * @param nbr_elev   elevation of the burning neighbour [m]
     * @param diagonal   true if neighbour is at a diagonal (distance = √2·a)
     */
    double slopeFactor(double this_elev, double nbr_elev, bool diagonal) const noexcept {
        double dist     = diagonal ? env.cell_size * M_SQRT2 : env.cell_size;
        double dz       = this_elev - nbr_elev;  // positive = spreading uphill
        double slope_rad = std::atan2(dz, dist);
        if (slope_rad >= 0.0) {
            double tan_s = std::tan(slope_rad);
            return std::exp(3.533 * std::pow(tan_s, 1.2));
        } else {
            return std::exp(0.5 * slope_rad);  // slope_rad < 0 → factor < 1
        }
    }

    /**
     * Compass bearing of the fire-spread direction FROM a burning neighbour
     * TO this cell, in degrees (0° = North, 90° = East, clockwise).
     *
     * Grid convention: row 0 = NORTH (top); row increases SOUTHWARD.
     *                  col 0 = WEST  (left); col increases EASTWARD.
     *
     * nbr_id  = absolute coordinates of the burning neighbour.
     * cellId_ = absolute coordinates of this cell.
     *
     * Spread vector (FROM nbr TO this) in grid coords = cellId_ - nbr_id
     * In geographic (N/E) coords:
     *   north_component = -(cellId_[0] - nbr_id[0])  = nbr[0] - id[0]
     *   east_component  =  (cellId_[1] - nbr_id[1])  = id[1]  - nbr[1]
     *
     * Verification:
     *   Nbr at (id[0]-1, id[1]) = NORTH → spread SOUTH → bearing 180° ✓
     *   Nbr at (id[0]+1, id[1]) = SOUTH → spread NORTH → bearing   0° ✓
     *   Nbr at (id[0], id[1]-1) = WEST  → spread EAST  → bearing  90° ✓
     *   Nbr at (id[0], id[1]+1) = EAST  → spread WEST  → bearing 270° ✓
     *   Nbr at (id[0]-1,id[1]-1)= NW    → spread SE    → bearing 135° ✓
     */
    double spreadBearing(const coordinates& nbr_id) const noexcept {
        double north_comp = static_cast<double>(nbr_id[0] - cellId_[0]);
        double east_comp  = static_cast<double>(cellId_[1] - nbr_id[1]);
        double bearing    = std::atan2(east_comp, north_comp) * 180.0 / M_PI;
        return std::fmod(bearing + 360.0, 360.0);
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  DEVS local computation function  (Karafyllidis eq. 6, extended)
    // ─────────────────────────────────────────────────────────────────────────
    /**
     * Cadmium v2 calls this at every external transition (when a neighbour's
     * state changes).  Returns the new state of this cell.
     *
     * @param state        copy of this cell's current state
     * @param neighborhood map { neighbour_id → NeighborData{.state, .vicinity} }
     * @return             next state
     */
    WildfireState localComputation(
        WildfireState state,
        const std::unordered_map<coordinates,
                                 NeighborData<WildfireState, double>>& neighborhood
    ) const override
    {
        // ── CASE 1: Incombustible cell (rock, building, firebreak) ───────────
        // fuel = 0 AND never started burning → R = 0, never ignites.
        // Fire propagation wraps around these cells (Fig. 5 in paper).
        if (state.fuel <= 0.0 && state.burned <= 0.0) {
            return state;   // unchanged — incombustible
        }

        // ── CASE 2: Fully burned cell (passive) ──────────────────────────────
        if (state.burned >= 1.0 || state.fuel <= 0.0) {
            state.burned = 1.0;
            state.fuel   = 0.0;
            return state;   // unchanged — already burned out
        }

        // ── CASE 3: Active cell — compute spread ─────────────────────────────

        // Local fire spread rate R_{i,j} [m/s]  (Karafyllidis eq. 7)
        //   R = R_base × fuel_factor × moisture_factor
        double R = env.R_base * fuelFactor(state.fuel) * moistureFactor(state.moisture);
        if (R <= 0.0) return state;   // no spread possible (too wet or no fuel)

        // Normalised spread increment per time step (from eq. 3):
        //   α = Δt[s] × R / a
        //   Δt[s] = time_step[h] × 3600
        double alpha = env.time_step * 3600.0 * R / env.cell_size;

        // ── Accumulate contributions from burning neighbours (eq. 6) ─────────
        double delta = 0.0;

        for (const auto& [nbr_id, nbr_data] : neighborhood) {
            if (!nbr_data.state) continue;
            const WildfireState& n = *nbr_data.state;

            // Only burning or burned neighbours contribute
            if (n.burned <= 0.0) continue;

            int row_diff = nbr_id[0] - cellId_[0];  // + = nbr is south
            int col_diff = nbr_id[1] - cellId_[1];  // + = nbr is east
            bool diagonal = (row_diff != 0 && col_diff != 0);

            // ── Karafyllidis base coefficient (eqs. 5–6) ─────────────────────
            // Adjacent  coefficient = 1.0
            // Diagonal  coefficient = 2(√2 − 1) ≈ 0.828
            //   Derived: fraction of cell area burned by one fully-ignited diagonal
            //   neighbour in one t_a step (paper eq. 5).
            double base_coeff = diagonal ? 2.0 * (M_SQRT2 - 1.0) : 1.0;

            // ── Directional modifiers ─────────────────────────────────────────
            double bearing = spreadBearing(nbr_id);
            double w_fact  = windFactor(bearing);
            double s_fact  = slopeFactor(state.elevation, n.elevation, diagonal);

            delta += base_coeff * n.burned * alpha * w_fact * s_fact;
        }

        if (delta <= 0.0) return state;   // no change — no burning neighbours

        // ── Update burned ratio and fuel ──────────────────────────────────────
        WildfireState next = state;
        next.burned = std::min(1.0, state.burned + delta);

        // Fuel depletion: fuel(S) = fuel_initial × (1 − S)
        // fuel_initial = state.fuel / (1 − state.burned)
        double remaining_capacity = 1.0 - state.burned;
        if (remaining_capacity > 1e-9) {
            double fuel_initial = state.fuel / remaining_capacity;
            next.fuel = std::max(0.0, fuel_initial * (1.0 - next.burned));
        } else {
            next.fuel = 0.0;
        }

        return next;
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  DEVS output delay function
    // ─────────────────────────────────────────────────────────────────────────
    /**
     * Returns the delay between computing a new state and outputting it.
     * We use a fixed 1-hour step (matches the paper's time unit t_a).
     *
     * Cadmium uses this as: scheduled_output_time = clock + outputDelay(nextState)
     * With "inertial" delay type, if state changes again before the scheduled
     * output, the previous output is cancelled (last-state-wins semantics).
     */
    double outputDelay(const WildfireState& /*state*/) const override {
        return env.time_step;   // 1 hour (or as configured)
    }
};

#endif // WILDFIRE_CELL_HPP
