"""
DIM_SALA PIPELINE - DIRECT DIMENSION LOAD
================================================================================
Loads stock room master data from raw.salas_estoque into analytics.dim_sala.
SCD Type 0/1: new records inserted, existing updated on change via UPSERT.
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
print("DIM_SALA PIPELINE")
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
# LOAD SOURCE DATA
# ============================================================================
print("\n Loading source data from raw.salas_estoque...")

query = """
    SELECT DISTINCT
        sala_id,
        nome,
        regiao,
        cidade,
        uf,
        capacidade_m3
    FROM raw.salas_estoque
    WHERE sala_id IS NOT NULL
"""
df = pd.read_sql(query, engine)

if df.empty:
    print("No data found in raw.salas_estoque. Exiting.")
    cursor.close()
    conn.close()
    exit()

print(f"Loaded {len(df)} rows from source.")

target_table_name = 'dim_sala'
target_schema = 'analytics'
full_target_table = f"{target_schema}.{target_table_name}"

# Verifica se a tabela já existe no schema do analytics
inspector = inspect(engine)
table_exists = inspector.has_table(target_table_name, schema=target_schema)

if not table_exists:
    print(f"\n Creating new table {full_target_table}...")
    cursor.execute(f"""
    CREATE TABLE {full_target_table} (
        sala_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sala_id INT NOT NULL UNIQUE, -- Obrigatório para o ON CONFLICT
        nome VARCHAR(150),
        regiao VARCHAR(100),
        cidade VARCHAR(150),
        uf VARCHAR(2), -- Padrão para sigla de estado (ex: SP, RJ)
        capacidade_m3 NUMERIC(12, 4), -- Ideal para volumes com casas decimais
        createdtm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changedtm TIMESTAMP NULL
    )
    """)
    conn.commit() # Salva a criação da tabela antes do insert

print(f"\n Performing UPSERT (Insert/Update) into {full_target_table}...")

# Query de UPSERT mapeando todos os campos da tabela de salas
upsert_query = f"""
    INSERT INTO {full_target_table} (
        sala_id, nome, regiao, cidade, uf, capacidade_m3
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (sala_id) 
    DO UPDATE SET 
        nome = EXCLUDED.nome,
        regiao = EXCLUDED.regiao,
        cidade = EXCLUDED.cidade,
        uf = EXCLUDED.uf,
        capacidade_m3 = EXCLUDED.capacidade_m3,
        changedtm = CURRENT_TIMESTAMP;
"""

# Converte o DataFrame para uma lista de tuplas compatível com o psycopg2
data_to_insert = [tuple(x) for x in df.to_numpy()]

# Executa a carga massiva com alta performance
cursor.executemany(upsert_query, data_to_insert)

# CRITICAL: Confirma as alterações no banco de dados
conn.commit()
print(f"Pipeline finished successfully! Affected rows: {cursor.rowcount}")

# Fechar conexões com segurança
cursor.close()
conn.close()
