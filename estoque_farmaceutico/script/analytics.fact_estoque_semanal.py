"""
FACT_ESTOQUE_SEMANAL PIPELINE - EXTREME SPEED V2
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

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
print("FACT_ESTOQUE_SEMANAL (EXTREME V2)")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n[1] Connecting...")
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True  # Speed up
cursor = conn.cursor()
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
print("Connected!")

# ============================================================================
# CREATE TABLE
# ============================================================================
print("\n[2] Creating table...")

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
        changedtm TIMESTAMP NULL
    )
""")
conn.commit()
print("Table created")

# ============================================================================
# OPTIMIZED LOAD - DIRECT INSERT FROM CTE
# ============================================================================
print("\n[3] Loading and inserting data (single pass)...")

# QUERY OTIMIZADA - JOIN direto no INSERT com CTE
query_optimized = """
WITH joined_data AS (
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
        raw.ruptura_estoque,
        ROW_NUMBER() OVER (PARTITION BY s.sala_key, m.medicamento_key, raw.semana_referencia ORDER BY raw.semana_referencia) as rn
    FROM raw.estoque_movimentacao_semanal raw
    INNER JOIN analytics.dim_sala s ON raw.sala_id = s.sala_id
    INNER JOIN analytics.dim_medicamento m ON raw.medicamento_id = m.medicamento_id
    INNER JOIN raw.lotes l ON raw.medicamento_id = l.medicamento_id AND raw.sala_id = l.sala_id
    INNER JOIN analytics.dim_lote dl ON l.lote_id = dl.lote_id
    WHERE raw.sala_id IS NOT NULL 
      AND raw.medicamento_id IS NOT NULL
)
INSERT INTO analytics.fact_estoque_semanal (
    sala_key, medicamento_key, lote_key, semana_referencia, 
    ano, semana_numero, saldo_inicial, entradas, saidas, 
    saldo_final, ruptura_estoque
)
SELECT 
    sala_key, medicamento_key, lote_key, semana_referencia,
    ano, semana_numero, saldo_inicial, entradas, saidas,
    saldo_final, ruptura_estoque
FROM joined_data
WHERE rn = 1  -- Remove duplicatas
"""

cursor.execute(query_optimized)
rows_inserted = cursor.rowcount
print(f"Inserted: {rows_inserted} records")

# ============================================================================
# CLEANUP
# ============================================================================
cursor.close()
conn.close()
print("\nDone!")

print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)