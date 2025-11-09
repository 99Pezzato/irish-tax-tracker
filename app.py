from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timezone
import os

from taxmeter import load_config, compute_state
from data_fetch import fetch_official_data

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.yaml")

# --- Load official data on startup ---
try:
    df = fetch_official_data()
    print("✅ Loaded official government data — grand so!")
except Exception as e:
    print("⚠️ Couldn’t fetch official data:", e)
    from taxmeter import load_monthly_receipts
    data_cfg, est_cfg = load_config(CONFIG_PATH)
    df = load_monthly_receipts(os.path.join(APP_DIR, data_cfg.csv_path))
else:
    import yaml
    with open(CONFIG_PATH, "r") as f:
        est_cfg = yaml.safe_load(f)["estimation"]

# --- Flask setup ---
app = Flask(__name__, static_folder="static", static_url_path="")

# Serve the main webpage
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

# Serve all other static assets (JS, CSS, images)
@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

# --- API: Return dataset as JSON ---
@app.route("/data")
def get_data():
    try:
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API: Return live meter state ---
@app.route("/api/state")
def api_state():
    try:
        latest = df.iloc[-1]
        ytd = latest.get("net_receipts_eur", 0)
        avg_rate = ytd / (365 * 24 * 3600)
        return jsonify({
            "ytd": float(ytd),
            "avg_rate": float(avg_rate),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run the app (Render will call this automatically) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
