"""
Transformação Silver INCREMENTAL - Posição de Veículos (Olho Vivo)

Diferença pra versão anterior: só processa arquivos Bronze NOVOS
(que ainda não foram transformados), usando um checkpoint em disco.
Faz append nos Parquets existentes em vez de sobrescrever tudo.

Reaproveita as funções de limpeza/tipagem do transform_silver_olhovivo.py.

Antes de rodar:
    pip install pandas pyarrow
"""

import json
import os
import glob
import pandas as pd

from transform_silver import (
    ler_arquivo_bronze,
    explodir_para_linhas,
    tipar_e_limpar,
)

BRONZE_PATH = "bronze/posicao_veiculos"
SILVER_PATH = "silver/posicao_veiculos"
CHECKPOINT_PATH = "silver/.checkpoint_arquivos_processados.txt"


def carregar_checkpoint() -> set[str]:
    """Retorna o conjunto de arquivos Bronze já processados anteriormente."""
    if not os.path.exists(CHECKPOINT_PATH):
        return set()
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        return set(linha.strip() for linha in f if linha.strip())


def salvar_checkpoint(arquivos_processados: set[str]) -> None:
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(arquivos_processados)))


def listar_arquivos_novos(ja_processados: set[str]) -> list[str]:
    padrao = os.path.join(BRONZE_PATH, "data=*", "*.json")
    todos = set(glob.glob(padrao))
    novos = sorted(todos - ja_processados)
    return novos


def construir_dataframe_incremental(arquivos_novos: list[str]) -> pd.DataFrame:
    todos_registros = []
    arquivos_com_erro = 0

    for caminho in arquivos_novos:
        try:
            payload = ler_arquivo_bronze(caminho)
            registros = explodir_para_linhas(payload)
            todos_registros.extend(registros)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Aviso: falha ao processar {caminho} ({e}). Pulando arquivo.")
            arquivos_com_erro += 1

    if arquivos_com_erro:
        print(f"Total de arquivos com erro (ignorados): {arquivos_com_erro}")

    return pd.DataFrame(todos_registros)


def mesclar_com_existente(df_novo: pd.DataFrame, data_particao: str) -> pd.DataFrame:
    """Se já existir Parquet dessa partição, junta com o dado novo antes de deduplicar."""
    caminho_existente = os.path.join(SILVER_PATH, f"data={data_particao}", "posicao_veiculos.parquet")

    if os.path.exists(caminho_existente):
        df_existente = pd.read_parquet(caminho_existente)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    linhas_antes = len(df_final)
    df_final = df_final.drop_duplicates(subset=["prefixo_veiculo", "timestamp_captura"])
    duplicatas = linhas_antes - len(df_final)
    if duplicatas:
        print(f"  Duplicatas removidas na mesclagem (partição {data_particao}): {duplicatas}")

    return df_final


def salvar_silver_incremental(df: pd.DataFrame) -> None:
    df = df.copy()
    df["data_particao"] = df["timestamp_captura"].dt.strftime("%Y-%m-%d")

    for data_particao, grupo_novo in df.groupby("data_particao"):
        grupo_novo = grupo_novo.drop(columns=["data_particao"])
        grupo_final = mesclar_com_existente(grupo_novo, data_particao)

        pasta = os.path.join(SILVER_PATH, f"data={data_particao}")
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, "posicao_veiculos.parquet")
        grupo_final.to_parquet(caminho, index=False)
        print(f"Atualizado: {caminho} (total agora: {len(grupo_final)} registros)")


def main():
    ja_processados = carregar_checkpoint()
    arquivos_novos = listar_arquivos_novos(ja_processados)

    if not arquivos_novos:
        print("Nenhum arquivo novo desde a última execução. Nada a fazer.")
        return

    print(f"Arquivos novos encontrados: {len(arquivos_novos)}")

    df = construir_dataframe_incremental(arquivos_novos)

    if df.empty:
        print("Arquivos novos não continham registros válidos.")
    else:
        df = tipar_e_limpar(df)
        if df.empty:
            print("Nenhum registro sobrou após limpeza.")
        else:
            salvar_silver_incremental(df)

    # Marca como processados mesmo se vieram vazios/inválidos, pra não tentar de novo
    ja_processados.update(arquivos_novos)
    salvar_checkpoint(ja_processados)
    print(f"Checkpoint atualizado. Total de arquivos já processados: {len(ja_processados)}")


if __name__ == "__main__":
    main()