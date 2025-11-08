def fetch_official_data():
    import io
    import requests
    import pandas as pd

    CSV_URL = "https://databank.finance.gov.ie/FinDataBank.aspx?rep=OpenDataSourceCSV"

    # Fetch CSV (disable SSL verification to avoid Render issue)
    r = requests.get(CSV_URL, timeout=30, verify=False)
    r.raise_for_status()

    # Read the CSV
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [str(c).strip() for c in df.columns]

    # Debug: print first few rows to logs
    print("Columns:", df.columns[:10])
    print(df.head())

    # Try to detect year columns (they look like numbers)
    year_cols = [c for c in df.columns if c.isdigit()]

    if not year_cols:
        raise ValueError("Could not find any numeric year columns in dataset.")

    # Melt wide data into long format
    df_long = df.melt(
        id_vars=[col for col in df.columns if col not in year_cols],
        value_vars=year_cols,
        var_name="year",
        value_name="net_receipts_eur",
    )

    # Try to find a month column
    possible_months = ["month", "Month", "MONTH", "January", "Feb", "Mar"]
    month_col = next((c for c in df.columns if any(m in c for m in possible_months)), None)
    if month_col:
        df_long.rename(columns={month_col: "month"}, inplace=True)
    else:
        df_long["month"] = None  # placeholder

    # Clean up
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long = df_long.dropna(subset=["year", "net_receipts_eur"])
    df_long = df_long.sort_values(["year"]).reset_index(drop=True)

    return df_long
