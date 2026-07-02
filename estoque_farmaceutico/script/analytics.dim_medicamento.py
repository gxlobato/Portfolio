"""
DIM_MEDICAMENTO PIPELINE - DIRECT DIMENSION LOAD
================================================================================
Loads medicine master data from raw.medicamentos into analytics.dim_medicamento.
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
print("DIM_MEDICAMENTO PIPELINE")
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
print("\n Loading source data from raw.medicamentos...")

# Query corrigida (sem a vírgula antes do primeiro campo)
query = """
    SELECT DISTINCT
        medicamento_id,
        nome,
        categoria,
        fabricante,
        principio_ativo,
        preco_unitario,
        validade_dias_padrao,
        armazenamento_refrigerado
    FROM raw.medicamentos
    WHERE medicamento_id IS NOT NULL
"""
df = pd.read_sql(query, engine)

if df.empty:
    print("No data found in raw.medicamentos. Exiting.")
    cursor.close()
    conn.close()
    exit()

print(f"Loaded {len(df)} rows from source.")

target_table_name = 'dim_medicamento'
target_schema = 'analytics'
full_target_table = f"{target_schema}.{target_table_name}"

# Verifica se a tabela já existe no schema do analytics
inspector = inspect(engine)
table_exists = inspector.has_table(target_table_name, schema=target_schema)

if not table_exists:
    print(f"\n Creating new table {full_target_table}...")
    cursor.execute(f"""
    CREATE TABLE {full_target_table} (
        medicamento_key INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        medicamento_id INT NOT NULL UNIQUE, -- Obrigatório para o ON CONFLICT
        nome VARCHAR(255),
        categoria VARCHAR(100),
        fabricante VARCHAR(150),
        principio_ativo VARCHAR(255),
        preco_unitario NUMERIC(10, 2),
        validade_dias_padrao INT,
        armazenamento_refrigerado BOOLEAN,
        createdtm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changedtm TIMESTAMP NULL
    )
    """)
    conn.commit() # Salva a criação da tabela antes do insert

print(f"\n Performing UPSERT (Insert/Update) into {full_target_table}...")

# Query de UPSERT mapeando todos os campos da query source
upsert_query = f"""
    INSERT INTO {full_target_table} (
        medicamento_id, nome, categoria, fabricante, 
        principio_ativo, preco_unitario, validade_dias_padrao, armazenamento_refrigerado
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (medicamento_id) 
    DO UPDATE SET 
        nome = EXCLUDED.nome,
        categoria = EXCLUDED.categoria,
        fabricante = EXCLUDED.fabricante,
        principio_ativo = EXCLUDED.principio_ativo,
        preco_unitario = EXCLUDED.preco_unitario,
        validade_dias_padrao = EXCLUDED.validade_dias_padrao,
        armazenamento_refrigerado = EXCLUDED.armazenamento_refrigerado,
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
