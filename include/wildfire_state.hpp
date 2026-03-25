#ifndef WILDFIRE_STATE_HPP
#define WILDFIRE_STATE_HPP

/**
 * wildfire_state.hpp
 * ──────────────────
 * Cell state for the Karafyllidis & Thanailakis (1997) wildfire CA model.
 *
 * State variable S_{i,j} ∈ [0, 1] = ratio of burned cell area to total area
 * (equation 1 in the paper). S = 0 → unburned; S = 1 → fully burned.
 *
 * Cadmium v2 requirements for a state type:
 *   1. Default constructor
 *   2. operator== and operator!=
 *   3. from_json / to_json   (nlohmann/json, for scenario JSON parsing)
 *   4. operator<<            (for CSV logger output)
 */

#include <iostream>
#include <nlohmann/json.hpp>

struct WildfireState {
    double burned;    ///< S_{i,j}: fraction of cell burned [0.0 – 1.0]
    double fuel;      ///< Fuel load [kg/m²].  fuel=0 → incombustible cell
    double elevation; ///< Terrain elevation [m]
    double moisture;  ///< Relative humidity [% RH].  High → fire suppressed

    // ── Default constructor required by Cadmium v2 ───────────────────────────
    WildfireState()
        : burned(0.0), fuel(15.0), elevation(0.0), moisture(30.0) {}

    WildfireState(double b, double f, double e, double m)
        : burned(b), fuel(f), elevation(e), moisture(m) {}

    // ── Equality operators required by Cadmium v2 ────────────────────────────
    // Cadmium uses != to decide whether to enqueue a new output.
    // Use exact comparison: burning cells change burned by a calculable delta,
    // so equality only holds when the state truly has not changed.
    bool operator==(const WildfireState& o) const {
        return burned    == o.burned
            && fuel      == o.fuel
            && elevation == o.elevation
            && moisture  == o.moisture;
    }
    bool operator!=(const WildfireState& o) const { return !(*this == o); }
};

// ── JSON serialization (read from scenario JSON file) ────────────────────────
// Cadmium calls from_json when it reads "state": {...} from the config file.
inline void from_json(const nlohmann::json& j, WildfireState& s) {
    s.burned    = j.value("burned",    0.0);
    s.fuel      = j.value("fuel",      15.0);
    s.elevation = j.value("elevation", 0.0);
    s.moisture  = j.value("moisture",  30.0);
}

inline void to_json(nlohmann::json& j, const WildfireState& s) {
    j = {
        {"burned",    s.burned},
        {"fuel",      s.fuel},
        {"elevation", s.elevation},
        {"moisture",  s.moisture}
    };
}

// ── Stream output (required by Cadmium v2 CSV logger) ────────────────────────
// The logger calls logState() → stringstream << state → this operator.
inline std::ostream& operator<<(std::ostream& os, const WildfireState& s) {
    os << s.burned << ";" << s.fuel << ";" << s.elevation << ";" << s.moisture;
    return os;
}

#endif // WILDFIRE_STATE_HPP
