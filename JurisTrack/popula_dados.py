import os
import re
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime

# ---------- CONFIGURAÇÕES ----------
DATAJUD_API_KEY = os.environ["DATAJUD_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]


def buscar_processos_cadastrados():
    """
    Busca todos os processos já cadastrados em cadastro.processos
    (inseridos manualmente via identifica_tribunal.py).
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, numero_processo, tribunal_alias FROM cadastro.processos"
            )
            return cur.fetchall()
    finally:
        conn.close()


def consultar_datajud(numero_processo: str, tribunal_alias: str):
    """
    Consulta a Datajud pelo número do processo, usando o tribunal
    já identificado e salvo no cadastro (evita redecodificar aqui).
    """
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal_alias}/_search"
    headers = {
        "Authorization": f"APIKey {DATAJUD_API_KEY}",
        "Content-Type": "application/json",
    }
    query = {"query": {"match": {"numeroProcesso": numero_processo}}}

    resposta = requests.post(url, headers=headers, json=query)
    resposta.raise_for_status()
    hits = resposta.json().get("hits", {}).get("hits", [])

    if not hits:
        return None
    return hits[0]["_source"]


def salvar_status(processo_id: int, payload: dict):
    """
    Salva o payload bruto retornado pela Datajud em cadastro.status_processos.
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cadastro.status_processos (processo_id, data_consulta, payload_bruto)
                    VALUES (%s, %s, %s)
                    """,
                    (processo_id, datetime.now(), psycopg2.extras.Json(payload)),
                )
    finally:
        conn.close()


if __name__ == "__main__":
    processos = buscar_processos_cadastrados()

    if not processos:
        print("Nenhum processo cadastrado em cadastro.processos. "
              "Cadastre processos com identifica_tribunal.py antes de rodar este script.")
    else:
        print(f"{len(processos)} processo(s) cadastrado(s) encontrados. Consultando a Datajud...\n")

        for processo_id, numero_processo, tribunal_alias in processos:
            print(f"Consultando processo {numero_processo} ({tribunal_alias})...")
            payload = consultar_datajud(numero_processo, tribunal_alias)

            if payload is None:
                print("  -> Não encontrado na Datajud (pode não estar indexado ainda). Pulando.\n")
                continue

            salvar_status(processo_id, payload)
            print("  -> Status salvo em cadastro.status_processos.\n")

        print("Concluído.")