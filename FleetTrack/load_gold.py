"""
Agregação Gold - Posição de Veículos (Olho Vivo)
Camada Gold = dado agregado, pronto para consumo (dashboard, BI, análise).

Gera duas tabelas:
1. veiculos_ativos_por_linha_hora: visão operacional
2. intervalo_atualizacao_por_veiculo: proxy de qualidade/frequência dos dados

Antes de rodar:
    pip install pandas pyarrow
"""

import glob
import os
import pandas as pd

SILVER_PATH = "silver/posicao_veiculos"
GOLD_PATH = "gold"


def carregar_silver() -> pd.DataFrame:
    arquivos = glob.glob(os.path.join(SILVER_PATH, "data=*", "posicao_veiculos.parquet"))

    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo encontrado na Silver. Rode a transformação primeiro.")

    df = pd.concat([pd.read_parquet(a) for a in arquivos], ignore_index=True)
    print(f"Registros carregados da Silver: {len(df)}")
    return df


def gerar_veiculos_ativos_por_linha_hora(df: pd.DataFrame) -> pd.DataFrame:
    """Quantos veículos distintos estiveram ativos, por linha, em cada hora."""
    df = df.copy()
    df["data_hora"] = df["timestamp_captura"].dt.floor("h")

    agregado = (
        df.groupby(["codigo_linha", "letreiro_linha", "data_hora"])["prefixo_veiculo"]
        .nunique()
        .reset_index(name="qtd_veiculos_ativos")
        .sort_values(["data_hora", "codigo_linha"])
    )

    return agregado


def gerar_intervalo_atualizacao_por_veiculo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada veículo, calcula o intervalo médio entre capturas consecutivas.
    Serve como proxy de frequência/qualidade dos dados (não é headway real de linha).
    """
    df = df.copy().sort_values(["prefixo_veiculo", "timestamp_captura"])

    df["intervalo_anterior"] = (
        df.groupby("prefixo_veiculo")["timestamp_captura"].diff().dt.total_seconds()
    )

    agregado = (
        df.groupby(["prefixo_veiculo", "codigo_linha"])["intervalo_anterior"]
        .agg(intervalo_medio_segundos="mean", qtd_intervalos_calculados="count")
        .reset_index()
    )
    # qtd_intervalos_calculados = qtd_capturas - 1 (não conta a primeira captura, sem par anterior)
    agregado["qtd_capturas_total"] = agregado["qtd_intervalos_calculados"] + 1
    agregado = agregado.sort_values("intervalo_medio_segundos")

    return agregado


def salvar_gold(df: pd.DataFrame, nome: str) -> None:
    os.makedirs(GOLD_PATH, exist_ok=True)
    caminho = os.path.join(GOLD_PATH, f"{nome}.parquet")
    df.to_parquet(caminho, index=False)
    print(f"Salvo: {caminho} ({len(df)} registros)")


def main():
    df = carregar_silver()

    veiculos_ativos = gerar_veiculos_ativos_por_linha_hora(df)
    salvar_gold(veiculos_ativos, "veiculos_ativos_por_linha_hora")

    intervalo_atualizacao = gerar_intervalo_atualizacao_por_veiculo(df)
    salvar_gold(intervalo_atualizacao, "intervalo_atualizacao_por_veiculo")

    print("\nAmostra - veículos ativos por linha/hora:")
    print(veiculos_ativos.head())

    print("\nAmostra - intervalo de atualização por veículo:")
    print(intervalo_atualizacao.head())


if __name__ == "__main__":
    main()