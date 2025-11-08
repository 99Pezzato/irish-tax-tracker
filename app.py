from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timezone
import os

from taxmeter import load_config, compute_state
from data_fetch import fetch_official_data

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.yaml")

# Fetch official data once when the server starts
try:
    df = fetch_official_data()
    print("✅ Loaded official government data")
except Exception as e:
    print("⚠️ Could not fetch official data:", e)
    from taxmeter import load_monthly_receipts
    data_cfg, est_cfg = load_config(CONFIG_PATH)
    df = load_monthly_receipts(os.path.join(APP_DIR, data_cfg.csv_path))
else:
    # use default estimation config
    import yaml
    with open(CONFIG_PATH, "r") as f:
        est_cfg = yaml.safe_load(f)["estimation"]

app = Flask(__name__, static_folder="static", static_url_path="")
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

