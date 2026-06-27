"""
DIM_LOTE PIPELINE - DIRECT DIMENSION LOAD
================================================================================
Loads lot master data from raw.lotes into analytics.dim_lote.
SCD Type 0: new lots inserted, existing lots updated on change.
No additional indexes or constraints beyond primary key.
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
print("DIM_LOTE PIPELINE")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n[1] Connecting to database...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
engine = create_engine(DATABASE_URL)
print("Connected!")

# ============================================================================
# LOAD SOURCE DATA
# ============================================================================
print("\n[2] Loading source data from raw.lotes...")

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

if df.empty:
    print("No data found in raw.lotes. Exiting.")
    cursor.close()
    conn.close()
    exit()

print(f"Loaded {len(df)} rows from source.")

target_table_name = 'dim_lote'
target_schema = 'analytics'
full_target_table = f"{target_schema}.{target_table_name}"

inspector = inspect(engine)
table_exists = inspector.has_table(target_table_name, schema=target_schema)

if not table_exists:
    print(f"\n[3] Creating new table {full_target_table}...")
    cursor.execute(f"""
    CREATE TABLE {full_target_table} (
        lote_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        lote_id INT NOT NULL UNIQUE, -- UNIQUE é obrigatório para o ON CONFLICT funcionar
        data_fabricacao DATE,
        data_validade DATE,
        quantidade_inicial INT,
        createdtm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changedtm TIMESTAMP NULL
    )
    """)
    conn.commit() # Commita a criação da tabela antes de inserir

print(f"\n[4] Performing UPSERT (Insert/Update) into {full_target_table}...")

# Query de UPSERT: Insere se não existir, atualiza se houver conflito no lote_id
upsert_query = f"""
    INSERT INTO {full_target_table} (lote_id, data_fabricacao, data_validade, quantidade_inicial)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (lote_id) 
    DO UPDATE SET 
        data_fabricacao = EXCLUDED.data_fabricacao,
        data_validade = EXCLUDED.data_validade,
        quantidade_inicial = EXCLUDED.quantidade_inicial,
        changedtm = CURRENT_TIMESTAMP;
"""

# Converte o DataFrame do Pandas em uma lista de tuplas pura para o psycopg2
data_to_insert = [tuple(x) for x in df.to_numpy()]

# Executa em lote de forma ultra performática
cursor.executemany(upsert_query, data_to_insert)

# CRITICAL: Salva as alterações de fato no banco de dados
conn.commit()
print(f"Pipeline finished successfully! Affected rows: {cursor.rowcount}")

# Fechar cursores e conexões com segurança
cursor.close()
conn.close()