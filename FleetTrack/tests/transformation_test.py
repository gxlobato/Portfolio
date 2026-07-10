"""
Testes unitários - lógica de transformação Silver.

Como rodar:
    pytest tests/test_transformacoes.py -v

Esses testes validam a LÓGICA de transformação usando dado fake
(não dependem da API real nem de arquivos em disco).
"""

import pandas as pd
import sys
import os

# Garante que os módulos do projeto sejam encontrados ao rodar via pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transform_silver import explodir_para_linhas, tipar_e_limpar, deduplicar


def payload_bronze_exemplo():
    """Simula um arquivo Bronze real, com 1 linha e 2 veículos."""
    return {
        "ingestion_timestamp_utc": "2026-07-10T12:00:00+00:00",
        "source": "olhovivo_sptrans",
        "data": {
            "hr": "12:00",
            "l": [
                {
                    "cl": 33736,
                    "c": "8000-10",
                    "sl": 1,
                    "qv": 2,
                    "vs": [
                        {"p": "12345", "a": True, "ta": "2026-07-10T12:00:05-03:00", "px": -46.6, "py": -23.5},
                        {"p": "67890", "a": False, "ta": "2026-07-10T12:00:10-03:00", "px": -46.7, "py": -23.6},
                    ],
                }
            ],
        },
    }


def test_explodir_para_linhas_gera_um_registro_por_veiculo():
    payload = payload_bronze_exemplo()
    registros = explodir_para_linhas(payload)

    assert len(registros) == 2
    assert registros[0]["prefixo_veiculo"] == "12345"
    assert registros[0]["codigo_linha"] == 33736
    assert registros[1]["prefixo_veiculo"] == "67890"


def test_explodir_para_linhas_com_payload_vazio_nao_quebra():
    payload = {"ingestion_timestamp_utc": "2026-07-10T12:00:00+00:00", "data": {"hr": "12:00", "l": []}}
    registros = explodir_para_linhas(payload)

    assert registros == []


def test_tipar_e_limpar_remove_registro_sem_coordenada():
    df = pd.DataFrame([
        {
            "ingestion_timestamp_utc": "2026-07-10T12:00:00+00:00",
            "hora_referencia_api": "12:00",
            "codigo_linha": 33736,
            "letreiro_linha": "8000-10",
            "sentido": 1,
            "qtd_veiculos_linha": 2,
            "prefixo_veiculo": "12345",
            "acessivel": True,
            "timestamp_captura": "2026-07-10T12:00:05-03:00",
            "latitude": -23.5,
            "longitude": -46.6,
        },
        {
            "ingestion_timestamp_utc": "2026-07-10T12:00:00+00:00",
            "hora_referencia_api": "12:00",
            "codigo_linha": 33736,
            "letreiro_linha": "8000-10",
            "sentido": 1,
            "qtd_veiculos_linha": 2,
            "prefixo_veiculo": "67890",
            "acessivel": False,
            "timestamp_captura": "2026-07-10T12:00:10-03:00",
            "latitude": None,  # dado inválido -> deve ser removido
            "longitude": -46.7,
        },
    ])

    df_limpo = tipar_e_limpar(df)

    assert len(df_limpo) == 1
    assert df_limpo.iloc[0]["prefixo_veiculo"] == "12345"


def test_deduplicar_remove_mesma_captura_repetida():
    df = pd.DataFrame([
        {"prefixo_veiculo": "12345", "timestamp_captura": pd.Timestamp("2026-07-10T12:00:05", tz="UTC")},
        {"prefixo_veiculo": "12345", "timestamp_captura": pd.Timestamp("2026-07-10T12:00:05", tz="UTC")},  # duplicata
        {"prefixo_veiculo": "67890", "timestamp_captura": pd.Timestamp("2026-07-10T12:00:10", tz="UTC")},
    ])

    df_dedup = deduplicar(df)

    assert len(df_dedup) == 2