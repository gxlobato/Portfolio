"""
Atualiza raw.estoque_movimentacao_semanal com as semanas faltantes até hoje.

Lógica:
1. Descobre a última semana_referencia já registrada por (sala_id, medicamento_id).
2. Gera as semanas faltantes (intervalo semanal, mesmo dia da semana já usado na tabela).
3. Para cada semana nova: saldo_inicial = saldo_final da semana anterior; entradas/saidas
   sintéticas com leve sazonalidade; saldo_final = saldo_inicial + entradas - saidas (>= 0).
4. lote_id segue FEFO: pega o lote do mesmo sala/medicamento com menor data_validade
   que ainda não venceu na semana de referência.
5. valor_venda_unitario vem de medicamentos.preco_unitario (+ pequena variação).

Pré-requisitos: pip install psycopg2-binary
"""

import logging
import os
import random
from datetime import timedelta

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

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

random.seed(42)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def buscar_estado_atual(conn):
    """Retorna, por (sala_id, medicamento_id), a última semana e o saldo_final dela."""
    sql = """
        SELECT DISTINCT ON (sala_id, medicamento_id)
            sala_id, medicamento_id, semana_referencia, saldo_final
        FROM raw.estoque_movimentacao_semanal
        ORDER BY sala_id, medicamento_id, semana_referencia DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return {(r[0], r[1]): {"ultima_semana": r[2], "saldo_final": r[3]} for r in rows}


def buscar_lotes(conn):
    """Lotes disponíveis por (sala_id, medicamento_id), ordenados por data_validade (FEFO)."""
    sql = """
        SELECT lote_id, sala_id, medicamento_id, data_validade
        FROM raw.lotes
        ORDER BY sala_id, medicamento_id, data_validade ASC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    lotes = {}
    for lote_id, sala_id, medicamento_id, validade in rows:
        lotes.setdefault((sala_id, medicamento_id), []).append((lote_id, validade))
    return lotes


def escolher_lote_fefo(lotes_combo, semana_referencia):
    """Primeiro lote (já ordenado por validade) que ainda não venceu na semana."""
    for lote_id, validade in lotes_combo:
        if validade >= semana_referencia:
            return lote_id
    # fallback: se todos vencidos, usa o de validade mais distante mesmo assim
    return lotes_combo[-1][0] if lotes_combo else None


def buscar_precos(conn):
    sql = "SELECT medicamento_id, preco_unitario FROM raw.medicamentos;"
    with conn.cursor() as cur:
        cur.execute(sql)
        return dict(cur.fetchall())


def gerar_semanas_faltantes(ultima_semana, hoje):
    """Lista de novas datas semanais (intervalo de 7 dias) entre a última registrada e hoje."""
    semanas = []
    proxima = ultima_semana + timedelta(days=7)
    while proxima <= hoje:
        semanas.append(proxima)
        proxima += timedelta(days=7)
    return semanas


def simular_movimentacao(saldo_inicial, semana_referencia):
    """Gera entradas/saidas sintéticas com leve sazonalidade (inverno/verão hemisfério sul)."""
    mes = semana_referencia.month
    fator_sazonal = 1.25 if mes in (5, 6, 7, 8) else 0.9  # mais demanda no inverno (gripes etc.)

    demanda_base = random.randint(15, 60)
    saidas = max(0, int(demanda_base * fator_sazonal + random.uniform(-5, 5)))
    saidas = min(saidas, saldo_inicial + random.randint(0, 30))  # evita saída maluca sem reposição

    entradas = random.randint(0, 40) if random.random() > 0.3 else 0  # nem toda semana tem entrada

    saldo_final = saldo_inicial + entradas - saidas
    if saldo_final < 0:
        # ajusta saidas para não estourar estoque negativo
        saidas = saldo_inicial + entradas
        saldo_final = 0

    ruptura = saldo_final == 0
    return entradas, saidas, saldo_final, ruptura


def montar_linhas(conn):
    estado = buscar_estado_atual(conn)
    lotes_por_combo = buscar_lotes(conn)
    precos = buscar_precos(conn)

    hoje = __import__("datetime").date.today()
    linhas = []

    for (sala_id, medicamento_id), info in estado.items():
        semanas_novas = gerar_semanas_faltantes(info["ultima_semana"], hoje)
        if not semanas_novas:
            continue

        saldo_corrente = info["saldo_final"]
        lotes_combo = lotes_por_combo.get((sala_id, medicamento_id), [])
        preco_base = precos.get(medicamento_id)

        for semana in semanas_novas:
            entradas, saidas, saldo_final, ruptura = simular_movimentacao(saldo_corrente, semana)
            lote_id = escolher_lote_fefo(lotes_combo, semana)
            if lote_id is None:
                log.warning(
                    "Sem lote disponível para sala=%s medicamento=%s — pulando semana %s",
                    sala_id, medicamento_id, semana,
                )
                continue

            valor_unitario = None
            if preco_base is not None:
                variacao = random.uniform(-0.05, 0.05)
                valor_unitario = round(float(preco_base) * (1 + variacao), 2)

            linhas.append((
                sala_id,
                medicamento_id,
                semana,
                semana.isocalendar().year,
                semana.isocalendar().week,
                saldo_corrente,
                entradas,
                saidas,
                saldo_final,
                ruptura,
                lote_id,
                valor_unitario,
            ))

            saldo_corrente = saldo_final

    return linhas


def inserir_linhas(conn, linhas):
    if not linhas:
        log.info("Nada para inserir — a tabela já está atualizada até hoje.")
        return

    sql = """
        INSERT INTO raw.estoque_movimentacao_semanal (
            sala_id, medicamento_id, semana_referencia, ano, semana_numero,
            saldo_inicial, entradas, saidas, saldo_final, ruptura_estoque,
            lote_id, valor_venda_unitario
        ) VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, linhas, page_size=500)
    conn.commit()
    log.info("Inseridas %d novas linhas.", len(linhas))


def main():
    conn = get_connection()
    try:
        linhas = montar_linhas(conn)
        inserir_linhas(conn, linhas)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
