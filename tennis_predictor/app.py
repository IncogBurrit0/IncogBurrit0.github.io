from flask import Flask, render_template, request, jsonify
from sofascore_client import SofaScoreTennisClient
# (Include your PlayerProfile, MatchEnvironment, and TennisPredictionEngine classes here)

app = Flask(__name__)
sofascore = SofaScoreTennisClient()

@app.route("/")
def home():
    return render_template("tennis.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json() or {}
    name_a = data.get("playerA", "").strip()
    name_b = data.get("playerB", "").strip()
    surface = data.get("surface", "Hard")
    best_of = int(data.get("best_of", 3))

    if not name_a or not name_b:
        return jsonify({"error": "Please provide both player names."}), 400

    # 1. LIVE FETCH FROM SOFASCORE
    raw_a = sofascore.fetch_player_profile(name_a)
    if not raw_a:
        return jsonify({"error": f"Could not find tennis player '{name_a}' on SofaScore."}), 404

    raw_b = sofascore.fetch_player_profile(name_b)
    if not raw_b:
        return jsonify({"error": f"Could not find tennis player '{name_b}' on SofaScore."}), 404

    # 2. INSTANTIATE PLAYER PROFILES
    pA = PlayerProfile(**raw_a)
    pB = PlayerProfile(**raw_b)

    # 3. SET CONDITIONS
    cpi_defaults = {"Clay": 26.0, "Hard": 38.0, "Grass": 44.0, "Indoor Hard": 42.0}
    cpi = cpi_defaults.get(surface, 38.0)
    
    env = MatchEnvironment(
        surface=surface,
        cpi=cpi,
        altitude_m=50,
        is_indoor=(surface == "Indoor Hard"),
        best_of=best_of
    )

    # 4. RUN MARKOV CHAIN ENGINE
    result = TennisPredictionEngine.predict(pA, pB, env)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)