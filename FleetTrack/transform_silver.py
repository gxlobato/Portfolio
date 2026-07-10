"""
Transformação Silver - Posição de Veículos (Olho Vivo)
Camada Silver = dado limpo, tipado, deduplicado, em formato tabular.

Lê todos os JSONs brutos da Bronze, "explode" a estrutura aninhada
(linha -> veículos) em uma linha por veículo/timestamp, tipa e deduplica.

Antes de rodar:
    pip install pandas pyarrow
"""

import json
import os
import glob
import pandas as pd
from datetime import datetime

BRONZE_PATH = "bronze/posicao_veiculos"
SILVER_PATH = "silver/posicao_veiculos"


def listar_arquivos_bronze() -> list[str]:
    """Lista todos os JSONs já ingeridos na Bronze."""
    padrao = os.path.join(BRONZE_PATH, "data=*", "*.json")
    return sorted(glob.glob(padrao))


def ler_arquivo_bronze(caminho: str) -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def explodir_para_linhas(payload: dict) -> list[dict]:
    """
    Extrai metadados do payload: timestamp de ingestão e hora de referência da API.
    Transforma a estrutura aninhada (linha -> veículos) em uma
    lista de registros planos (uma linha por veículo).
    """
    registros = []
    ingestion_ts = payload.get("ingestion_timestamp_utc")
    dados = payload.get("data") or {}
    hora_referencia = dados.get("hr")

    # Percorre cada linha de ônibus e extrai seus atributos (código, letreiro, sentido, quantidade de veículos).
    for linha in dados.get("l", []):
        codigo_linha = linha.get("cl")
        letreiro = linha.get("c")
        sentido = linha.get("sl")
        qtd_veiculos_linha = linha.get("qv")

        # Para cada veículo dentro da linha, cria um registro plano combinando dados da linha com dados do veículo.
        for veiculo in linha.get("vs", []):
            registros.append({
                "ingestion_timestamp_utc": ingestion_ts,
                "hora_referencia_api": hora_referencia,
                "codigo_linha": codigo_linha,
                "letreiro_linha": letreiro,
                "sentido": sentido,
                "qtd_veiculos_linha": qtd_veiculos_linha,
                "prefixo_veiculo": veiculo.get("p"),
                "acessivel": veiculo.get("a"),
                "timestamp_captura": veiculo.get("ta"),
                "latitude": veiculo.get("py"),
                "longitude": veiculo.get("px"),
            })

    return registros

# Lista arquivos da Bronze e verifica se existem.
def construir_dataframe() -> pd.DataFrame:
    arquivos = listar_arquivos_bronze()

    if not arquivos:
        raise FileNotFoundError(
            "Nenhum arquivo encontrado na Bronze. Rode a ingestão primeiro."
        )

    print(f"Arquivos Bronze encontrados: {len(arquivos)}")

    todos_registros = []
    arquivos_com_erro = 0

    # Processa cada arquivo: lê, explode em registros e adiciona à lista. 
    for caminho in arquivos:
        try:
            payload = ler_arquivo_bronze(caminho)
            registros = explodir_para_linhas(payload)
            todos_registros.extend(registros)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Aviso: falha ao processar {caminho} ({e}). Pulando arquivo.")
            arquivos_com_erro += 1

    # Se der erro de JSON ou chave faltando, pula o arquivo.
    if arquivos_com_erro:
        print(f"Total de arquivos com erro (ignorados): {arquivos_com_erro}")

    df = pd.DataFrame(todos_registros)
    return df

# Cria cópia para não modificar original.
def tipar_e_limpar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica tipagem correta e remove registros inválidos."""
    df = df.copy()

    #Converte colunas para tipos corretos
    df["timestamp_captura"] = pd.to_datetime(df["timestamp_captura"], errors="coerce", utc=True)
    df["ingestion_timestamp_utc"] = pd.to_datetime(df["ingestion_timestamp_utc"], errors="coerce", utc=True)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["codigo_linha"] = pd.to_numeric(df["codigo_linha"], errors="coerce").astype("Int64")
    df["acessivel"] = df["acessivel"].astype("boolean")

    linhas_antes = len(df)

    # Regra de qualidade: sem timestamp de captura ou coordenadas, o registro é inútil
    df = df.dropna(subset=["timestamp_captura", "latitude", "longitude"])

    # Remove registros sem dados essenciais e retorna DataFrame limpo.
    linhas_removidas = linhas_antes - len(df)
    if linhas_removidas:
        print(f"Registros removidos por dado inválido (nulo em campo crítico): {linhas_removidas}")

    return df

# Remove duplicatas baseado no par veículo+timestamp.
def deduplicar(df: pd.DataFrame) -> pd.DataFrame:
    """Mesmo veículo pode aparecer repetido se ingestões rodarem muito próximas."""
    linhas_antes = len(df)
    df = df.drop_duplicates(subset=["prefixo_veiculo", "timestamp_captura"])
    linhas_removidas = linhas_antes - len(df)
    if linhas_removidas:
        print(f"Duplicatas removidas: {linhas_removidas}")
    return df

# Cria coluna de partição baseada na data de captura.
def salvar_silver(df: pd.DataFrame) -> None:
    df = df.copy()
    df["data_particao"] = df["timestamp_captura"].dt.strftime("%Y-%m-%d")

    # Salva dados particionados por dia em formato Parquet.
    for data_particao, grupo in df.groupby("data_particao"):
        pasta = os.path.join(SILVER_PATH, f"data={data_particao}")
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, "posicao_veiculos.parquet")
        grupo.drop(columns=["data_particao"]).to_parquet(caminho, index=False)
        print(f"Salvo: {caminho} ({len(grupo)} registros)")

# Orquestra todo o processo: carrega, limpa, deduplica e salva.
def main():
    df = construir_dataframe()
    print(f"Total de registros brutos (antes de limpar): {len(df)}")

    df = tipar_e_limpar(df)
    df = deduplicar(df)

    print(f"Total de registros finais na Silver: {len(df)}")
    salvar_silver(df)

# Executa o script quando rodado diretamente.
if __name__ == "__main__":
    main()