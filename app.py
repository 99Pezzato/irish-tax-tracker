from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timezone
import os
import yaml

from taxmeter import load_config, compute_state
from data_fetch import fetch_official_data

# --- Setup paths ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.yaml")

# --- Load data once ---
try:
    df = fetch_official_data()
    print("✅ Loaded official government data")
except Exception as e:
    print("⚠️ Could not fetch official data:", e)
    from taxmeter import load_monthly_receipts
    data_cfg, est_cfg = load_config(CONFIG_PATH)
    df = load_monthly_receipts(os.path.join(APP_DIR, data_cfg.csv_path))

# --- Flask app setup ---
app = Flask(__name__, static_folder="static", static_url_path="")

# --- Serve frontend ---
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

# --- API: raw data (optional debug) ---
@app.route("/data")
def get_data():
    try:
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API: summarized state for the frontend ---
@app.route("/api/state")
def api_state():
    try:
        latest = df.iloc[-1]
        ytd = float(latest.get("net_receipts_eur", 0))
        avg_rate = ytd / (365 * 24 * 3600)
        return jsonify({
            "ytd": ytd,
            "avg_rate": avg_rate,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print("❌ Error in /api/state:", e)
        return jsonify({"error": str(e)}), 500

# --- Run the app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
