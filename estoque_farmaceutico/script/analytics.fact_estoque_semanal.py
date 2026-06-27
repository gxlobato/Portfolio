"""
FACT_ESTOQUE_SEMANAL PIPELINE - FACT TABLE LOAD WITH SURROGATE KEYS
================================================================================
Loads weekly stock movement and balances into analytics.fact_estoque_semanal.
Performs LEFT JOINs to resolve business keys into analytics surrogate keys.
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

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
print("FACT_ESTOQUE_SEMANAL PIPELINE")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n Connecting to database...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
engine = create_engine(DATABASE_URL)
print("Connected!")

# ============================================================================
# LOAD SOURCE DATA WITH SURROGATE KEY JOINS
# ============================================================================
print("\n Loading source data and joining with Dimensions...")

# Query realizando os JOINs necessários para capturar as chaves substitutas (_key)
query = """
    SELECT DISTINCT
        s.sala_key,
        m.medicamento_key,
        raw.semana_referencia,
        raw.ano,
        raw.semana_numero,
        raw.saldo_inicial,
        raw.entradas,
        raw.saidas,
        raw.saldo_final,
        raw.ruptura_estoque
    FROM raw.estoque_movimentacao_semanal raw
    LEFT JOIN analytics.dim_sala s 
        ON raw.sala_id = s.sala_id
    LEFT JOIN analytics.dim_medicamento m 
        ON raw.medicamento_id = m.medicamento_id
    WHERE raw.sala_id IS NOT NULL 
      AND raw.medicamento_id IS NOT NULL
"""
df = pd.read_sql(query, engine)

if df.empty:
    print("No data found in source. Exiting.")
    cursor.close()
    conn.close()
    exit()

print(f"Loaded {len(df)} rows linked to dimensions.")

target_table_name = 'fact_estoque_semanal'
target_schema = 'analytics'
full_target_table = f"{target_schema}.{target_table_name}"

# Verifica se a tabela Fato existe
inspector = inspect(engine)
table_exists = inspector.has_table(target_table_name, schema=target_schema)

if not table_exists:
    print(f"\n Creating new Fact table {full_target_table}...")
    cursor.execute(f"""
    CREATE TABLE {full_target_table} (
        fact_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sala_key INT NOT NULL,
        medicamento_key INT NOT NULL,
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
        -- Chave única composta para garantir a granularidade e permitir o UPSERT
        CONSTRAINT uq_fact_estoque_semanal UNIQUE (sala_key, medicamento_key, semana_referencia)
    )
    """)
    conn.commit()

print(f"\n Performing UPSERT (Insert/Update) into {full_target_table}...")

# Query de UPSERT baseada na restrição de chave única composta
upsert_query = f"""
    INSERT INTO {full_target_table} (
        sala_key, medicamento_key, semana_referencia, ano, semana_numero,
        saldo_inicial, entradas, saidas, saldo_final, ruptura_estoque
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (sala_key, medicamento_key, semana_referencia) 
    DO UPDATE SET 
        ano = EXCLUDED.ano,
        semana_numero = EXCLUDED.semana_numero,
        saldo_inicial = EXCLUDED.saldo_inicial,
        entradas = EXCLUDED.entradas,
        saidas = EXCLUDED.saidas,
        saldo_final = EXCLUDED.saldo_final,
        ruptura_estoque = EXCLUDED.ruptura_estoque,
        changedtm = CURRENT_TIMESTAMP;
"""

# Converte DataFrame para tuplas
data_to_insert = [tuple(x) for x in df.to_numpy()]

# Carga massiva
cursor.executemany(upsert_query, data_to_insert)
conn.commit()

print(f"Pipeline finished successfully! Affected rows: {cursor.rowcount}")

# Fechar conexões
cursor.close()
conn.close()
