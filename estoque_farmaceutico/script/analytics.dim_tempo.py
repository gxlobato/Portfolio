"""
DIM_TEMPO PIPELINE - EXTREME SPEED
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
print("DIM_TEMPO PIPELINE (EXTREME)")
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
# LOAD AND BUILD
# ============================================================================
print("\n[2] Building dimension...")

# Load dates and build attributes in one query
query = """
    SELECT DISTINCT
        semana_referencia,
        EXTRACT(YEAR FROM semana_referencia)::INT as ano,
        EXTRACT(QUARTER FROM semana_referencia)::INT as trimestre,
        EXTRACT(MONTH FROM semana_referencia)::INT as mes,
        TO_CHAR(semana_referencia, 'Month') as mes_nome,
        EXTRACT(WEEK FROM semana_referencia)::INT as semana_numero,
        (semana_referencia - EXTRACT(DOW FROM semana_referencia)::INT)::DATE as dia_inicio_semana,
        (semana_referencia - EXTRACT(DOW FROM semana_referencia)::INT + 6)::DATE as dia_fim_semana
    FROM raw.estoque_movimentacao_semanal
    WHERE semana_referencia IS NOT NULL
    ORDER BY semana_referencia
"""

df = pd.read_sql(query, engine)
print(f"Dates: {len(df)}")

if len(df) == 0:
    print("No data. Exiting.")
    conn.close()
    exit(0)

# ============================================================================
# CREATE TABLE
# ============================================================================
print("\n[3] Creating table...")

cursor.execute("DROP TABLE IF EXISTS analytics.dim_tempo CASCADE")
cursor.execute("""
    CREATE TABLE analytics.dim_tempo (
        tempo_key SERIAL PRIMARY KEY,
        semana_referencia DATE UNIQUE NOT NULL,
        ano SMALLINT NOT NULL,
        trimestre SMALLINT NOT NULL,
        mes SMALLINT NOT NULL,
        mes_nome VARCHAR(20) NOT NULL,
        semana_numero SMALLINT NOT NULL,
        dia_inicio_semana DATE NOT NULL,
        dia_fim_semana DATE NOT NULL,
        CreateDt TIMESTAMP NOT NULL DEFAULT NOW(),
        ChangedTM TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
conn.commit()
print("Table created")

# ============================================================================
# BULK INSERT
# ============================================================================
print("\n[4] Inserting...")

df.to_sql('dim_tempo', engine, schema='analytics', if_exists='append', index=False, method='multi')
print(f"Inserted: {len(df)} records")

conn.close()
print("\nDone!")

print("\n" + "=" * 70)
print("DIM_TEMPO PIPELINE COMPLETED")
print("=" * 70)
