import math
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple
from functools import lru_cache
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass
class PlayerProfile:
    name: str
    handedness: str  # 'R' or 'L'
    archetype: str   # 'BIG_SERVER', 'AGGRESSIVE_BASELINER', 'COUNTERPUNCHER', 'ALL_COURT'
    
    # Weighted Heavier: Service Dominance
    first_serve_in_pct: float
    first_serve_won_pct: float
    second_serve_won_pct: float
    aces_per_game: float
    double_faults_per_game: float

    # Weighted Heavier: Return Effectiveness
    return_first_won_pct: float
    return_second_won_pct: float
    return_games_won_pct: float

    # Weighted Heavier: High-Leverage / Break Point Efficiency
    bp_saved_pct: float
    bp_converted_pct: float

    # Weighted Heavier: Cumulative Fatigue, Workload & Injury Risk
    minutes_last_14d: float
    sets_last_14d: int
    days_rest: int
    injury_risk: float

    # Weighted Lighter: Surface Elo & Recent Form
    surface_elo: float
    recent_form_index: float


@dataclass
class MatchEnvironment:
    surface: str
    cpi: float
    altitude_m: float
    is_indoor: bool
    best_of: int = 3
    h2h_overall: Tuple[int, int] = (0, 0)
    h2h_surface: Tuple[int, int] = (0, 0)


# ==============================================================================
# PLAYER DATABASE / REGISTRY
# ==============================================================================

PLAYER_DATABASE: Dict[str, PlayerProfile] = {
    "carlos alcaraz": PlayerProfile(
        name="Carlos Alcaraz",
        handedness="R",
        archetype="ALL_COURT",
        first_serve_in_pct=0.64,
        first_serve_won_pct=0.74,
        second_serve_won_pct=0.56,
        aces_per_game=0.45,
        double_faults_per_game=0.20,
        return_first_won_pct=0.35,
        return_second_won_pct=0.55,
        return_games_won_pct=0.31,
        bp_saved_pct=0.66,
        bp_converted_pct=0.45,
        minutes_last_14d=360,
        sets_last_14d=10,
        days_rest=2,
        injury_risk=0.0,
        surface_elo=2190,
        recent_form_index=0.80
    ),
    "jannik sinner": PlayerProfile(
        name="Jannik Sinner",
        handedness="R",
        archetype="AGGRESSIVE_BASELINER",
        first_serve_in_pct=0.63,
        first_serve_won_pct=0.79,
        second_serve_won_pct=0.58,
        aces_per_game=0.68,
        double_faults_per_game=0.15,
        return_first_won_pct=0.34,
        return_second_won_pct=0.56,
        return_games_won_pct=0.30,
        bp_saved_pct=0.69,
        bp_converted_pct=0.44,
        minutes_last_14d=340,
        sets_last_14d=9,
        days_rest=3,
        injury_risk=0.0,
        surface_elo=2240,
        recent_form_index=0.88
    ),
    "novak djokovic": PlayerProfile(
        name="Novak Djokovic",
        handedness="R",
        archetype="ALL_COURT",
        first_serve_in_pct=0.66,
        first_serve_won_pct=0.76,
        second_serve_won_pct=0.57,
        aces_per_game=0.48,
        double_faults_per_game=0.14,
        return_first_won_pct=0.36,
        return_second_won_pct=0.56,
        return_games_won_pct=0.32,
        bp_saved_pct=0.67,
        bp_converted_pct=0.46,
        minutes_last_14d=310,
        sets_last_14d=8,
        days_rest=3,
        injury_risk=0.05,
        surface_elo=2180,
        recent_form_index=0.70
    ),
    "daniil medvedev": PlayerProfile(
        name="Daniil Medvedev",
        handedness="R",
        archetype="COUNTERPUNCHER",
        first_serve_in_pct=0.64,
        first_serve_won_pct=0.75,
        second_serve_won_pct=0.51,
        aces_per_game=0.60,
        double_faults_per_game=0.28,
        return_first_won_pct=0.33,
        return_second_won_pct=0.54,
        return_games_won_pct=0.28,
        bp_saved_pct=0.64,
        bp_converted_pct=0.41,
        minutes_last_14d=540,
        sets_last_14d=15,
        days_rest=1,
        injury_risk=0.10,
        surface_elo=2120,
        recent_form_index=0.55
    ),
    "alexander zverev": PlayerProfile(
        name="Alexander Zverev",
        handedness="R",
        archetype="AGGRESSIVE_BASELINER",
        first_serve_in_pct=0.69,
        first_serve_won_pct=0.76,
        second_serve_won_pct=0.52,
        aces_per_game=0.78,
        double_faults_per_game=0.22,
        return_first_won_pct=0.30,
        return_second_won_pct=0.51,
        return_games_won_pct=0.25,
        bp_saved_pct=0.66,
        bp_converted_pct=0.39,
        minutes_last_14d=480,
        sets_last_14d=13,
        days_rest=2,
        injury_risk=0.0,
        surface_elo=2110,
        recent_form_index=0.65
    ),
    "hubert hurkacz": PlayerProfile(
        name="Hubert Hurkacz",
        handedness="R",
        archetype="BIG_SERVER",
        first_serve_in_pct=0.66,
        first_serve_won_pct=0.79,
        second_serve_won_pct=0.53,
        aces_per_game=1.15,
        double_faults_per_game=0.12,
        return_first_won_pct=0.26,
        return_second_won_pct=0.46,
        return_games_won_pct=0.18,
        bp_saved_pct=0.70,
        bp_converted_pct=0.35,
        minutes_last_14d=380,
        sets_last_14d=10,
        days_rest=2,
        injury_risk=0.05,
        surface_elo=2040,
        recent_form_index=0.55
    ),
    "rafael nadal": PlayerProfile(
        name="Rafael Nadal",
        handedness="L",
        archetype="AGGRESSIVE_BASELINER",
        first_serve_in_pct=0.67,
        first_serve_won_pct=0.74,
        second_serve_won_pct=0.57,
        aces_per_game=0.25,
        double_faults_per_game=0.12,
        return_first_won_pct=0.36,
        return_second_won_pct=0.57,
        return_games_won_pct=0.34,
        bp_saved_pct=0.69,
        bp_converted_pct=0.47,
        minutes_last_14d=300,
        sets_last_14d=8,
        days_rest=3,
        injury_risk=0.15,
        surface_elo=2260,
        recent_form_index=0.60
    ),
    "ben shelton": PlayerProfile(
        name="Ben Shelton",
        handedness="L",
        archetype="BIG_SERVER",
        first_serve_in_pct=0.63,
        first_serve_won_pct=0.78,
        second_serve_won_pct=0.52,
        aces_per_game=0.95,
        double_faults_per_game=0.30,
        return_first_won_pct=0.26,
        return_second_won_pct=0.47,
        return_games_won_pct=0.20,
        bp_saved_pct=0.68,
        bp_converted_pct=0.36,
        minutes_last_14d=320,
        sets_last_14d=8,
        days_rest=2,
        injury_risk=0.0,
        surface_elo=2020,
        recent_form_index=0.58
    )
}

def resolve_player(name_query: str) -> PlayerProfile:
    """Fuzzy / partial case-insensitive lookup."""
    query = name_query.strip().lower()
    if query in PLAYER_DATABASE:
        return PLAYER_DATABASE[query]
    
    # Try partial matching (e.g. typing "alcaraz" finds "Carlos Alcaraz")
    for key, profile in PLAYER_DATABASE.items():
        if query in key or key in query:
            return profile
            
    return None


# ==============================================================================
# PREDICTION ENGINE CORE
# ==============================================================================

class TennisPredictionEngine:
    TOUR_SERVE_WIN = 0.640
    TOUR_RETURN_WIN = 0.360
    TOUR_BP_SAVED = 0.600
    TOUR_BP_CONVERTED = 0.400

    @staticmethod
    def _prob_game(p: float) -> float:
        p = max(0.01, min(0.99, p))
        q = 1.0 - p
        win_love = p**4
        win_15 = 4.0 * (p**4) * q
        win_30 = 10.0 * (p**4) * (q**2)
        deuce = 20.0 * (p**3) * (q**3)
        win_from_deuce = (p**2) / (p**2 + q**2)
        return win_love + win_15 + win_30 + (deuce * win_from_deuce)

    @staticmethod
    def _prob_tiebreak(pA: float, pB: float) -> float:
        @lru_cache(maxsize=None)
        def dp(a_pts: int, b_pts: int) -> float:
            if a_pts >= 7 and a_pts - b_pts >= 2:
                return 1.0
            if b_pts >= 7 and b_pts - a_pts >= 2:
                return 0.0
            if a_pts >= 6 and b_pts >= 6:
                p1, p2 = pA, 1.0 - pB
                return (p1 * p2) / ((p1 * p2) + ((1.0 - p1) * (1.0 - p2)))
            n = a_pts + b_pts
            p = pA if ((n + 1) // 2) % 2 == 0 else (1.0 - pB)
            return p * dp(a_pts + 1, b_pts) + (1.0 - p) * dp(a_pts, b_pts + 1)

        return dp(0, 0)

    @classmethod
    def _prob_set(cls, hold_A: float, hold_B: float, pA_serve: float, pB_serve: float) -> float:
        p_break_A = 1.0 - hold_B
        tb_A = cls._prob_tiebreak(pA_serve, pB_serve)

        @lru_cache(maxsize=None)
        def dp(gA: int, gB: int, server: int) -> float:
            if gA == 6 and gB <= 4: return 1.0
            if gB == 6 and gA <= 4: return 0.0
            if gA == 7 and gB == 5: return 1.0
            if gB == 7 and gA == 5: return 0.0
            if gA == 6 and gB == 6: return tb_A
            if server == 0:
                return hold_A * dp(gA + 1, gB, 1) + (1.0 - hold_A) * dp(gA, gB + 1, 1)
            else:
                return p_break_A * dp(gA + 1, gB, 0) + (1.0 - p_break_A) * dp(gA, gB + 1, 0)

        return 0.5 * (dp(0, 0, 0) + dp(0, 0, 1))

    @staticmethod
    def _prob_match(p_set: float, best_of: int = 3) -> float:
        if best_of == 3:
            return (p_set ** 2) * (3.0 - 2.0 * p_set)
        elif best_of == 5:
            return (p_set ** 3) * (10.0 - 15.0 * p_set + 6.0 * (p_set ** 2))
        return p_set

    @classmethod
    def predict(cls, pA: PlayerProfile, pB: PlayerProfile, env: MatchEnvironment) -> Dict[str, Any]:
        match_format_mult = 1.30 if env.best_of == 5 else 1.0

        # Fatigue & Injury Workload
        def calc_fatigue(p: PlayerProfile):
            workload = max(0.0, (p.minutes_last_14d - 400.0) / 450.0) * 0.5 + max(0.0, (p.sets_last_14d - 9) / 10.0) * 0.3
            rest_relief = min(1.0, p.days_rest / 2.5)
            net_workload = workload * (1.25 - 0.45 * rest_relief)
            return min(1.0, max(0.0, net_workload + 0.65 * p.injury_risk))

        fatigue_A = calc_fatigue(pA)
        fatigue_B = calc_fatigue(pB)

        s2_loss_A = 0.080 * fatigue_A * match_format_mult
        s1_loss_A = 0.030 * fatigue_A * match_format_mult
        s2_loss_B = 0.080 * fatigue_B * match_format_mult
        s1_loss_B = 0.030 * fatigue_B * match_format_mult

        adj_s1_A = pA.first_serve_won_pct - s1_loss_A
        adj_s2_A = pA.second_serve_won_pct - s2_loss_A
        adj_s1_B = pB.first_serve_won_pct - s1_loss_B
        adj_s2_B = pB.second_serve_won_pct - s2_loss_B

        # Service Dominance & Return Interaction
        ace_adj_A = max(-0.015, min(0.015, 0.003 * (pA.aces_per_game - 2.2 * pA.double_faults_per_game)))
        ace_adj_B = max(-0.015, min(0.015, 0.003 * (pB.aces_per_game - 2.2 * pB.double_faults_per_game)))

        serve_A = (pA.first_serve_in_pct * adj_s1_A) + ((1.0 - pA.first_serve_in_pct) * adj_s2_A) + ace_adj_A
        serve_B = (pB.first_serve_in_pct * adj_s1_B) + ((1.0 - pB.first_serve_in_pct) * adj_s2_B) + ace_adj_B

        ret_A = (pB.first_serve_in_pct * pA.return_first_won_pct) + ((1.0 - pB.first_serve_in_pct) * pA.return_second_won_pct)
        ret_B = (pA.first_serve_in_pct * pB.return_first_won_pct) + ((1.0 - pA.first_serve_in_pct) * pB.return_second_won_pct)

        base_pA_serve = serve_A - (ret_B - cls.TOUR_RETURN_WIN)
        base_pB_serve = serve_B - (ret_A - cls.TOUR_RETURN_WIN)

        # Environmental CPI & Altitude
        effective_cpi = env.cpi + (env.altitude_m / 100.0) * 0.75 + (2.5 if env.is_indoor else 0.0)
        cpi_dev = (effective_cpi - 35.0) / 100.0

        cpi_mod_A = cpi_dev * (serve_A - cls.TOUR_SERVE_WIN) * 0.65
        cpi_mod_B = cpi_dev * (serve_B - cls.TOUR_SERVE_WIN) * 0.65

        # Tactical & Handedness
        hand_mod_A = 0.015 if (pA.handedness == 'L' and pB.handedness == 'R') else 0.0
        hand_mod_B = 0.015 if (pB.handedness == 'L' and pA.handedness == 'R') else 0.0

        style_mod_A, style_mod_B = 0.0, 0.0
        if pA.archetype == "BIG_SERVER" and pB.archetype == "COUNTERPUNCHER":
            if effective_cpi >= 38.0: style_mod_A += 0.014
            elif effective_cpi <= 32.0: style_mod_B += 0.014
        elif pB.archetype == "BIG_SERVER" and pA.archetype == "COUNTERPUNCHER":
            if effective_cpi >= 38.0: style_mod_B += 0.014
            elif effective_cpi <= 32.0: style_mod_A += 0.014

        # Light Weight: Surface Elo and Recent Form
        elo_adj = ((pA.surface_elo - pB.surface_elo) / 400.0) * 0.012
        form_adj = (pA.recent_form_index - pB.recent_form_index) * 0.007

        pA_serve = max(0.40, min(0.85, base_pA_serve + cpi_mod_A + hand_mod_A + (style_mod_A - style_mod_B) + elo_adj + form_adj))
        pB_serve = max(0.40, min(0.85, base_pB_serve + cpi_mod_B + hand_mod_B + (style_mod_B - style_mod_A) - elo_adj - form_adj))

        # Leverage / Break Point Clutch
        raw_hold_A = cls._prob_game(pA_serve)
        raw_hold_B = cls._prob_game(pB_serve)

        bp_clutch_A = (pA.bp_saved_pct - cls.TOUR_BP_SAVED) - (pB.bp_converted_pct - cls.TOUR_BP_CONVERTED) - (0.06 * fatigue_A * match_format_mult)
        bp_clutch_B = (pB.bp_saved_pct - cls.TOUR_BP_SAVED) - (pA.bp_converted_pct - cls.TOUR_BP_CONVERTED) - (0.06 * fatigue_B * match_format_mult)

        hold_A = max(0.05, min(0.98, raw_hold_A + 0.11 * bp_clutch_A))
        hold_B = max(0.05, min(0.98, raw_hold_B + 0.11 * bp_clutch_B))

        p_set = cls._prob_set(hold_A, hold_B, pA_serve, pB_serve)
        p_match = cls._prob_match(p_set, env.best_of)

        winner = pA.name if p_match >= 0.50 else pB.name
        confidence = p_match if p_match >= 0.50 else (1.0 - p_match)

        return {
            "winner": winner,
            "confidence_pct": round(confidence * 100.0, 1),
            "playerA": {
                "name": pA.name,
                "match_win_pct": round(p_match * 100.0, 1),
                "set_win_pct": round(p_set * 100.0, 1),
                "hold_pct": round(hold_A * 100.0, 1),
                "break_pct": round((1.0 - hold_B) * 100.0, 1),
                "point_serve_pct": round(pA_serve * 100.0, 1),
                "fatigue": round(fatigue_A, 2),
                "handedness": pA.handedness,
                "archetype": pA.archetype
            },
            "playerB": {
                "name": pB.name,
                "match_win_pct": round((1.0 - p_match) * 100.0, 1),
                "set_win_pct": round((1.0 - p_set) * 100.0, 1),
                "hold_pct": round(hold_B * 100.0, 1),
                "break_pct": round((1.0 - hold_A) * 100.0, 1),
                "point_serve_pct": round(pB_serve * 100.0, 1),
                "fatigue": round(fatigue_B, 2),
                "handedness": pB.handedness,
                "archetype": pB.archetype
            },
            "effective_cpi": round(effective_cpi, 1)
        }


# ==============================================================================
# FLASK WEB ROUTES
# ==============================================================================

@app.route("/")
def home():
    # Return available player names for datalist autocomplete
    player_names = sorted([p.name for p in PLAYER_DATABASE.values()])
    return render_template("index.html", players=player_names)

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json() or {}
    name_a = data.get("playerA", "")
    name_b = data.get("playerB", "")
    surface = data.get("surface", "Hard")
    best_of = int(data.get("best_of", 3))

    pA = resolve_player(name_a)
    pB = resolve_player(name_b)

    if not pA:
        return jsonify({"error": f"Player '{name_a}' was not found in the database."}), 404
    if not pB:
        return jsonify({"error": f"Player '{name_b}' was not found in the database."}), 404
    if pA.name == pB.name:
        return jsonify({"error": "Please select two different players."}), 400

    # Surface CPI defaults
    cpi_defaults = {"Clay": 26.0, "Hard": 38.0, "Grass": 44.0, "Indoor Hard": 42.0}
    cpi = cpi_defaults.get(surface, 38.0)
    is_indoor = (surface == "Indoor Hard")

    env = MatchEnvironment(
        surface=surface,
        cpi=cpi,
        altitude_m=50,
        is_indoor=is_indoor,
        best_of=best_of
    )

    result = TennisPredictionEngine.predict(pA, pB, env)
    return jsonify(result)


if __name__ == "__main__":
    print("Serving Tennis Predictor at http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)