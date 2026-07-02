"""
DIM_LOTE PIPELINE - EXTREME SPEED
================================================================================
Fastest possible load using pandas to_sql + single UPSERT
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

print("=" * 70)
print("DIM_LOTE PIPELINE (EXTREME SPEED)")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n[1] Connecting...")
engine = create_engine(DATABASE_URL)
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
print("Connected!")

# ============================================================================
# LOAD & PROCESS DATA
# ============================================================================
print("\n[2] Loading and processing data...")

query = """
    SELECT DISTINCT
        lote_id,
        data_fabricacao,
        data_validade,
        quantidade_inicial
    FROM raw.lotes
    WHERE lote_id IS NOT NULL
"""

df = pd.read_sql(query, engine)
print(f"Records: {len(df)}")

if len(df) == 0:
    print("No data. Exiting.")
    conn.close()
    exit(0)

# ============================================================================
# CREATE TABLE
# ============================================================================
print("\n[3] Creating table...")

cursor.execute("DROP TABLE IF EXISTS analytics.dim_lote CASCADE")
cursor.execute("""
    CREATE TABLE analytics.dim_lote (
        lote_key SERIAL PRIMARY KEY,
        lote_id INT NOT NULL UNIQUE,
        data_fabricacao DATE,
        data_validade DATE,
        quantidade_inicial INTEGER,
        createdt TIMESTAMP DEFAULT NOW(),
        changedtm TIMESTAMP DEFAULT NOW()
    )
""")
conn.commit()
print("Table created")

# ============================================================================
# BULK INSERT (MAIS RÁPIDO)
# ============================================================================
print("\n[4] Bulk inserting...")

# Usar to_sql do pandas (muito rápido)
df.to_sql('dim_lote', engine, schema='analytics', if_exists='append', index=False, method='multi')

# Atualizar timestamps
cursor.execute("""
    UPDATE analytics.dim_lote 
    SET createdt = NOW(), changedtm = NOW()
    WHERE createdt IS NULL
""")
conn.commit()

print(f"Inserted: {len(df)} records")

conn.close()
print("\nDone!")

print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)
