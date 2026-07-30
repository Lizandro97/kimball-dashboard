from pathlib import Path
import pandas as pd

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "super-store.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="latin-1")
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d/%m/%Y")
    return df
