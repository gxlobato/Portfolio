"""
FACT_ALERTA_ESTOQUE PIPELINE - SAÚDE ATUAL DO ESTOQUE POR SALA
Estratégia: DROP + CREATE + INSERT (sem histórico, apenas estado atual)
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
print("FACT_ALERTA_ESTOQUE - SAÚDE ATUAL DO ESTOQUE POR SALA")
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

cursor.execute("DROP TABLE IF EXISTS analytics.fact_alerta_estoque CASCADE")
cursor.execute("""
    CREATE TABLE analytics.fact_alerta_estoque (
        alerta_key       SERIAL        PRIMARY KEY,
        sala_key         INT           NOT NULL,
        medicamento_key  INT           NOT NULL,
        lote_key         INT,
        semana_referencia DATE         NOT NULL,
        saldo_atual      INT           NOT NULL,
        limite_inferior  NUMERIC(10,2),
        -- quantos dias de estoque restam com base na média das últimas 4 semanas
        dias_cobertura   NUMERIC(10,1),
        data_validade    DATE,
        dias_para_vencer INT,
        -- RUPTURA | CRÍTICO | VENC_PRÓXIMO | ATENÇÃO | OK
        nivel_alerta     VARCHAR(20)   NOT NULL,
        motivo_alerta    TEXT,
        createdtm        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
        changedtm        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
    )
""")
print("Table created!")

# ============================================================================
# INSERT - ALERTAS COM BASE EM fact_estoque_atual
# ============================================================================
print("\n[3] Inserting alerts...")

# Prioridade dos alertas (maior para menor severidade):
#   1. RUPTURA      -> saldo = 0
#   2. CRÍTICO      -> saldo <= limite_inferior
#   3. VENC_PRÓXIMO -> lote vence entre 1 e 30 dias (exclui já vencidos)
#   4. ATENÇÃO      -> saldo entre limite_inferior e 2x limite_inferior
#   5. OK           -> saldo > 2x limite_inferior

query_insert = """
INSERT INTO analytics.fact_alerta_estoque (
    sala_key, medicamento_key, lote_key,
    semana_referencia, saldo_atual, limite_inferior,
    dias_cobertura, data_validade, dias_para_vencer,
    nivel_alerta, motivo_alerta
)
WITH media_saidas AS (
    -- média semanal de saídas das últimas 4 semanas por sala e medicamento
    SELECT
        sala_key,
        medicamento_key,
        AVG(saidas) AS media_saidas_semanal
    FROM analytics.fact_estoque_semanal
    WHERE semana_referencia >= CURRENT_DATE - INTERVAL '28 days'
    GROUP BY sala_key, medicamento_key
)
SELECT
    fea.sala_key,
    fea.medicamento_key,
    fea.lote_key,
    fea.semana_referencia,
    fea.saldo_final                                         AS saldo_atual,
    fea.limite_inferior,

    CASE
        WHEN COALESCE(ms.media_saidas_semanal, 0) = 0 THEN NULL
        ELSE ROUND((fea.saldo_final::numeric / ms.media_saidas_semanal) * 7, 1)
    END                                                     AS dias_cobertura,

    dl.data_validade,
    (dl.data_validade - CURRENT_DATE)::int                  AS dias_para_vencer,

    CASE
        WHEN fea.saldo_final = 0
            THEN 'RUPTURA'
        WHEN fea.saldo_final <= fea.limite_inferior
            THEN 'CRÍTICO'
        WHEN dl.data_validade IS NOT NULL
             AND (dl.data_validade - CURRENT_DATE) BETWEEN 1 AND 30
            THEN 'VENCIMENTO PRÓXIMO'
        WHEN fea.saldo_final <= 2 * fea.limite_inferior
            THEN 'ATENÇÃO'
        ELSE 'OK'
    END                                                     AS nivel_alerta,

    CASE
        WHEN fea.saldo_final = 0
            THEN 'Sem estoque disponível'
        WHEN fea.saldo_final <= fea.limite_inferior
            THEN 'Saldo abaixo do limite mínimo (' || fea.limite_inferior::text || ' un.)'
        WHEN dl.data_validade IS NOT NULL
             AND (dl.data_validade - CURRENT_DATE) BETWEEN 1 AND 30
            THEN 'Lote vence em ' || (dl.data_validade - CURRENT_DATE)::text || ' dias'
        WHEN fea.saldo_final <= 2 * fea.limite_inferior
            THEN 'Saldo próximo ao limite mínimo'
        ELSE 'Estoque saudável'
    END                                                     AS motivo_alerta

FROM analytics.fact_estoque_atual fea
LEFT JOIN analytics.dim_lote dl
    ON dl.lote_key = fea.lote_key
LEFT JOIN media_saidas ms
    ON  ms.sala_key        = fea.sala_key
    AND ms.medicamento_key = fea.medicamento_key
"""

cursor.execute(query_insert)
rows_inserted = cursor.rowcount
print(f"Inserted: {rows_inserted} records")

# ============================================================================
# RESUMO POR NÍVEL DE ALERTA
# ============================================================================
print("\n[4] Summary by alert level...")
cursor.execute("""
    SELECT nivel_alerta, COUNT(*) AS qtd
    FROM analytics.fact_alerta_estoque
    GROUP BY nivel_alerta
    ORDER BY qtd DESC
""")
for nivel, qtd in cursor.fetchall():
    print(f"   {nivel:<15} {qtd}")

# ============================================================================
# CLEANUP
# ============================================================================
cursor.close()
conn.close()
print("\nDone!")

print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print(f"Total alertas: {rows_inserted}")
print("=" * 70)