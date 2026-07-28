"""Extracción del CSV Superstore hacia PostgreSQL usando pandas + SQLAlchemy."""


import pandas as pd
from sqlalchemy import create_engine, text

from core.config import settings

DATABASE_URL = settings.DATABASE_URL
CSV_PATH = settings.CSV_PATH
CHUNK_SIZE = 1000


def extract(csv_path: str = CSV_PATH) -> pd.DataFrame:
    print(f"Extrayendo datos desde {csv_path} ...")
    df = pd.read_csv(csv_path, encoding="latin-1")
    print(f"  Filas leídas: {len(df)}")
    print(f"  Columnas: {list(df.columns)}")
    return df


def load_to_raw(df: pd.DataFrame, engine) -> None:
    print("Cargando a raw.superstore ...")
    df.to_sql("superstore", engine, schema="raw",
              if_exists="replace", index=False, chunksize=CHUNK_SIZE)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM raw.superstore"))
        count = result.scalar()
    print(f"  Filas cargadas: {count}")
    print("  Estado: OK")


def main():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.commit()
    df = extract()
    load_to_raw(df, engine)


if __name__ == "__main__":
    main()
