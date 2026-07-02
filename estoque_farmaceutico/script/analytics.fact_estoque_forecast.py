"""
FACT_ESTOQUE_FORECAST PIPELINE - EXTREME SPEED
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
print("FACT_ESTOQUE_FORECAST (EXTREME)")
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
# LOAD FORECAST DATA
# ============================================================================
print("\n[2] Loading forecast data...")

query = """
    SELECT 
        prev.id,
        prev.sala_key,
        prev.medicamento_key,
        prev.data_previsao,
        prev.previsao_saidas,
        prev.limite_inferior,
        prev.limite_superior,
        rec.recomendacao
    FROM forecast.previsoes_xgb prev
    JOIN forecast.recomendacoes_estoque rec 
        ON prev.sala_key = rec.sala_key 
        AND prev.medicamento_key = rec.medicamento_key 
        AND prev.data_previsao >= rec.data_calculo
"""

df = pd.read_sql(query, engine)
print(f"Records: {len(df)}")

if len(df) == 0:
    print("No data. Exiting.")
    conn.close()
    exit(0)

# ============================================================================
# UPDATE DIM_TEMPO WITH FORECAST DATES
# ============================================================================
print("\n[3] Updating dim_tempo...")

# Build date attributes in SQL and insert directly
cursor.execute("""
    INSERT INTO analytics.dim_tempo 
    (semana_referencia, ano, trimestre, mes, mes_nome, semana_numero, 
     dia_inicio_semana, dia_fim_semana)
    SELECT DISTINCT
        data_previsao,
        EXTRACT(YEAR FROM data_previsao)::INT,
        EXTRACT(QUARTER FROM data_previsao)::INT,
        EXTRACT(MONTH FROM data_previsao)::INT,
        TO_CHAR(data_previsao, 'Month'),
        EXTRACT(WEEK FROM data_previsao)::INT,
        (data_previsao - EXTRACT(DOW FROM data_previsao)::INT)::DATE,
        (data_previsao - EXTRACT(DOW FROM data_previsao)::INT + 6)::DATE
    FROM forecast.previsoes_xgb
    ON CONFLICT (semana_referencia) DO NOTHING
""")
conn.commit()
print("dim_tempo updated")

# ============================================================================
# CREATE TABLE
# ============================================================================
print("\n[4] Creating table...")

cursor.execute("DROP TABLE IF EXISTS analytics.fact_estoque_forecast CASCADE")

cursor.execute("""
    CREATE TABLE analytics.fact_estoque_forecast (
        fact_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        id INT NOT NULL,
        sala_key INT NOT NULL,
        medicamento_key INT NOT NULL,
        tempo_key INT NOT NULL,
        data_previsao DATE NOT NULL,
        previsao_saidas NUMERIC(10, 2),
        limite_inferior NUMERIC(10, 2),
        limite_superior NUMERIC(10, 2),
        recomendacao TEXT,
        createdtm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changedtm TIMESTAMP NULL
    )
""")
conn.commit()
print("Table created")

# ============================================================================
# LOAD FACT TABLE DIRECTLY VIA SQL
# ============================================================================
print("\n[5] Loading fact table...")

cursor.execute("""
    INSERT INTO analytics.fact_estoque_forecast 
    (id, sala_key, medicamento_key, tempo_key, data_previsao, 
     previsao_saidas, limite_inferior, limite_superior, recomendacao)
    SELECT 
        prev.id,
        prev.sala_key,
        prev.medicamento_key,
        t.tempo_key,
        prev.data_previsao,
        prev.previsao_saidas,
        prev.limite_inferior,
        prev.limite_superior,
        rec.recomendacao
    FROM forecast.previsoes_xgb prev
    JOIN forecast.recomendacoes_estoque rec 
        ON prev.sala_key = rec.sala_key 
        AND prev.medicamento_key = rec.medicamento_key 
        AND prev.data_previsao >= rec.data_calculo
    JOIN analytics.dim_tempo t 
        ON prev.data_previsao = t.semana_referencia
""")

conn.commit()
cursor.close()
conn.close()

print("\nDone!")
print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)
