"""
FACT_ESTOQUE_SEMANAL PIPELINE - EXTREME SPEED
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

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
print("FACT_ESTOQUE_SEMANAL (EXTREME)")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n[1] Connecting...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
engine = create_engine(DATABASE_URL)
print("Connected!")

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n[2] Loading data...")

query = """
    SELECT 
        s.sala_key,
        m.medicamento_key,
        dl.lote_key,
        raw.semana_referencia,
        raw.ano,
        raw.semana_numero,
        raw.saldo_inicial,
        raw.entradas,
        raw.saidas,
        raw.saldo_final,
        raw.ruptura_estoque
    FROM raw.estoque_movimentacao_semanal raw
    LEFT JOIN analytics.dim_sala s ON raw.sala_id = s.sala_id
    LEFT JOIN analytics.dim_medicamento m ON raw.medicamento_id = m.medicamento_id
    LEFT JOIN raw.lotes l ON raw.medicamento_id = l.medicamento_id and raw.sala_id = l.sala_id
    LEFT JOIN analytics.dim_lote dl ON l.lote_id = dl.lote_id
    WHERE raw.sala_id IS NOT NULL 
      AND raw.medicamento_id IS NOT NULL
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

cursor.execute("DROP TABLE IF EXISTS analytics.fact_estoque_semanal CASCADE")
cursor.execute("""
    CREATE TABLE analytics.fact_estoque_semanal (
        fact_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sala_key INT NOT NULL,
        medicamento_key INT NOT NULL,
        lote_key INT NOT NULL,               
        semana_referencia DATE NOT NULL,
        ano INT,
        semana_numero INT,
        saldo_inicial INT,
        entradas INT,
        saidas INT,
        saldo_final INT,
        ruptura_estoque BOOLEAN,
        createdtm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changedtm TIMESTAMP NULL,
        CONSTRAINT uq_fact_estoque_semanal UNIQUE (sala_key, medicamento_key, semana_referencia)
    )
""")
conn.commit()
print("Table created")

# ============================================================================
# BULK INSERT
# ============================================================================
print("\n[4] Bulk inserting...")

# Usar to_sql para insert rápido
df.to_sql('fact_estoque_semanal', engine, schema='analytics', 
          if_exists='append', index=False, method='multi')

print(f"Inserted: {len(df)} records")

conn.close()
print("\nDone!")

print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)
