"""Limpieza y transformación de datos con pandas."""


import pandas as pd
from sqlalchemy import create_engine

from core.config import settings

DATABASE_URL = settings.DATABASE_URL


def transform() -> pd.DataFrame:
    engine = create_engine(DATABASE_URL)
    print("Leyendo raw.superstore ...")
    df = pd.read_sql("SELECT * FROM raw.superstore", engine)
    print(f"  Filas originales: {len(df)}")

    print("Transformando fechas ...")
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y", errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d/%m/%Y", errors="coerce")
    df.dropna(subset=["Order Date", "Ship Date"], inplace=True)

    print("Normalizando strings ...")
    str_cols = ["Customer Name", "Product Name", "City", "State", "Country"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)

    print("Detectando valores atípicos ...")
    neg_profit = df[df["Profit"] < 0]
    print(f"  Transacciones con utilidad negativa: {len(neg_profit)} ({len(neg_profit)/len(df)*100:.1f}%)")
    max_discount = df["Discount"].max()
    print(f"  Descuento máximo: {max_discount:.0%}")
    min_profit = df["Profit"].min()
    print(rf"  Utilidad mínima: \${min_profit:,.2f}")

    df.to_sql("superstore_clean", engine, schema="raw",
              if_exists="replace", index=False)
    print("  Datos limpios guardados en raw.superstore_clean")
    print(f"  Filas después de limpieza: {len(df)}")
    return df


if __name__ == "__main__":
    transform()
