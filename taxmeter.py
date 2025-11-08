from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
import calendar
import yaml

@dataclass
class EstimationConfig:
    method: str = "rolling_3m"      # 'monthly' | 'rolling_3m' | 'annualized'
    anchor: str = "server_start"    # 'server_start' | 'month_end'
    timezone: str = "Europe/Dublin"

@dataclass
class DataConfig:
    csv_path: str

def load_config(path: str) -> tuple[DataConfig, EstimationConfig]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    data_cfg = DataConfig(csv_path=cfg["data"]["csv_path"])
    est_cfg = EstimationConfig(
        method=cfg["estimation"].get("method", "rolling_3m"),
        anchor=cfg["estimation"].get("anchor", "server_start"),
        timezone=cfg["estimation"].get("timezone", "Europe/Dublin"),
    )
    return data_cfg, est_cfg

def _seconds_in_month(year: int, month: int) -> int:
    days = calendar.monthrange(year, month)[1]
    return days * 24 * 60 * 60

def load_monthly_receipts(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # ensure types
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["net_receipts_eur"] = df["net_receipts_eur"].astype(float)
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str) + "-01")
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df

def ytd_total(df: pd.DataFrame, year: int) -> float:
    subset = df[df["year"] == year]
    return float(subset["net_receipts_eur"].sum())

def latest_month(df: pd.DataFrame, year: int):
    subset = df[df["year"] == year]
    if subset.empty:
        return None
    row = subset.iloc[-1]
    return int(row["year"]), int(row["month"]), float(row["net_receipts_eur"])

def rate_per_second(df: pd.DataFrame, year: int, method: str = "rolling_3m") -> float:
    subset = df[df["year"] == year].copy()
    if subset.empty:
        return 0.0
    if method == "monthly":
        y, m, val = latest_month(df, year)
        secs = _seconds_in_month(y, m)
        return val / secs
    elif method == "rolling_3m":
        last3 = subset.tail(3)
        secs = sum(_seconds_in_month(int(r["year"]), int(r["month"])) for _, r in last3.iterrows())
        val = float(last3["net_receipts_eur"].sum())
        return val / secs if secs > 0 else 0.0
    elif method == "annualized":
        # average month in the year so far, divided by average seconds per month elapsed
        months_elapsed = subset.shape[0]
        val = float(subset["net_receipts_eur"].sum())
        avg_month = val / months_elapsed
        secs = sum(_seconds_in_month(int(r["year"]), int(r["month"])) for _, r in subset.iterrows()) / months_elapsed
        return avg_month / secs if secs > 0 else 0.0
    else:
        raise ValueError(f"Unknown method: {method}")

def anchor_amount_and_time(df: pd.DataFrame, year: int, anchor: str = "server_start"):
    now = datetime.now(timezone.utc)
    total = ytd_total(df, year)
    if anchor == "month_end":
        # anchor to the end of the last reported month (no extrapolation up to 'now')
        y, m, _ = latest_month(df, year)
        # assume end of that month 23:59:59 UTC as anchor_time
        last_day = calendar.monthrange(y, m)[1]
        anchor_time = datetime(y, m, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return total, anchor_time
    # default: server_start (the API serves an anchor at runtime)
    return total, now

def compute_state(df: pd.DataFrame, year: int, cfg: EstimationConfig):
    r = rate_per_second(df, year, cfg.method)
    anchor_amount, anchor_time = anchor_amount_and_time(df, year, cfg.anchor)
    return {
        "ytd_anchor_eur": anchor_amount,
        "rate_per_second_eur": r,
        "anchor_time_iso": anchor_time.isoformat()
    }