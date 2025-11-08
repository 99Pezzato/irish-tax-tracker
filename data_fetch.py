# data_fetch.py
import io, requests, pandas as pd

CSV_URL = (
    "https://data.gov.ie/dataset/Monthly_Exchequer_Tax_Receipts_1984___Present/resource.csv"
    # If that URL stops working, open https://data.gov.ie and search
    # “Monthly Exchequer Tax Receipts 1984 - Present”, copy the CSV link
)

def fetch_official_data():
    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    # Normalise columns
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"net receipts": "net_receipts_eur"})
    df = df[["year", "month", "net_receipts_eur"]]
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df
