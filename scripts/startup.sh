#!/bin/bash
set -e

echo "=== Superstore BI Dashboard ==="
echo "Waiting for PostgreSQL ..."

python -c "
import os, time, psycopg2

url = os.environ['DATABASE_URL']
for i in range(30):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print('PostgreSQL OK')
        break
    except Exception:
        time.sleep(1)
else:
    print('Could not connect to PostgreSQL')
    exit(1)
"

echo "Checking if data already loaded ..."
python -c "
import os, psycopg2
url = os.environ['DATABASE_URL']
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM f_sales\")
count = cur.fetchone()[0]
cur.close()
conn.close()
print(f'  f_sales has {count} rows')
exit(0 if count > 0 else 1)
" && echo "Data exists, skipping ETL." || {
  echo "Running ETL pipeline ..."
  python -m etl.run
}

echo "Starting server ..."
exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000