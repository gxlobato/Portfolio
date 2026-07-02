"""
FACT_ESTOQUE_ATUAL PIPELINE - ÚLTIMO MOVIMENTO POR SALA
"""

import os
import psycopg2
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432'),
    'sslmode': 'require'
}

print("=" * 70)
print("FACT_ESTOQUE_ATUAL - ÚLTIMO MOVIMENTO POR SALA")
print("=" * 70)

# ============================================================================
# CONNECTION
# ============================================================================
print("\n[1] Connecting...")
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cursor = conn.cursor()
print("Connected!")

# ============================================================================
# CREATE TABLE
# ============================================================================
print("\n[2] Creating table...")

cursor.execute("DROP TABLE IF EXISTS analytics.fact_estoque_atual CASCADE")
cursor.execute("""
    CREATE TABLE analytics.fact_estoque_atual (
        fact_key         INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sala_key         INT           NOT NULL,
        medicamento_key  INT           NOT NULL,
        lote_key         INT           NOT NULL,
        semana_referencia DATE         NOT NULL,
        saldo_inicial    INT,
        entradas         INT,
        saidas           INT,
        saldo_final      INT,
        limite_inferior  NUMERIC(10, 2),
        createdtm        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
        changedtm        TIMESTAMP     NULL
    )
""")
print("Table created!")

# ============================================================================
# INSERT - ÚLTIMO MOVIMENTO POR SALA + MEDICAMENTO
# ============================================================================
print("\n[3] Loading and inserting data...")

# A CTE basic identifica a semana mais recente por sala+medicamento.
# O join com raw.lotes usa ems.lote_id = l.lote_id (1 para 1),
# evitando duplicatas que ocorriam ao cruzar por sala_id+medicamento_id.
# O WHERE do limite_inferior foi removido: medicamentos sem limite cadastrado
# devem aparecer com limite NULL em vez de serem silenciosamente excluídos.

query_insert = """
INSERT INTO analytics.fact_estoque_atual (
    sala_key,
    medicamento_key,
    lote_key,
    semana_referencia,
    saldo_inicial,
    entradas,
    saidas,
    saldo_final,
    limite_inferior
)
WITH basic AS (
    SELECT
        sala_id,
        medicamento_id,
        MAX(semana_referencia) AS semana_referencia
    FROM raw.estoque_movimentacao_semanal
    GROUP BY sala_id, medicamento_id
)
SELECT
    s.sala_key,
    m.medicamento_key,
    dl.lote_key,
    ems.semana_referencia,
    ems.saldo_inicial,
    ems.entradas,
    ems.saidas,
    ems.saldo_final,
    lms.limite_inferior
FROM raw.estoque_movimentacao_semanal ems
INNER JOIN basic b
    ON  ems.sala_id          = b.sala_id
    AND ems.medicamento_id   = b.medicamento_id
    AND ems.semana_referencia = b.semana_referencia
INNER JOIN raw.lotes l
    ON  l.lote_id = ems.lote_id
INNER JOIN analytics.dim_sala s
    ON  s.sala_id = ems.sala_id
INNER JOIN analytics.dim_medicamento m
    ON  m.medicamento_id = ems.medicamento_id
INNER JOIN analytics.dim_lote dl
    ON  dl.lote_id = l.lote_id
LEFT JOIN forecast.limites_mensais_simples lms
    ON  lms.medicamento_key = m.medicamento_key
    AND lms.sala_key        = s.sala_key
    AND DATE_TRUNC('month', lms.mes_referencia) = DATE_TRUNC('month', b.semana_referencia)
"""

cursor.execute(query_insert)
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
print(f"Total registros: {rows_inserted}")
print("=" * 70)