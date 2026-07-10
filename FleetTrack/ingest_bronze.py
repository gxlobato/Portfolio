"""
Ingestão Bronze - API Olho Vivo (SPTrans)
Camada Bronze = dado bruto, sem transformação, só ingestão.

Antes de rodar:
1. Crie um arquivo .env nesta mesma pasta com o conteúdo:
   SPTRANS_TOKEN=seu_token_aqui
2. Instale a dependência: pip install python-dotenv
"""

import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # carrega variáveis do arquivo .env

TOKEN = os.getenv("SPTRANS_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BRONZE_PATH = os.getenv("BRONZE_PATH")

# Faz autenticação na API
def autenticar(session: requests.Session, token: str) -> bool:
    """Autentica na API. Retorna True se sucesso."""
    resp = session.post(f"{BASE_URL}/Login/Autenticar", params={"token": token})
    resp.raise_for_status()
    return resp.json() is True

# Busca dados de posição dos veículos
def buscar_posicoes(session: requests.Session) -> dict:
    """Busca a posição de todos os veículos em tempo real."""
    resp = session.get(f"{BASE_URL}/Posicao")
    resp.raise_for_status()
    return resp.json()

# Prepara estrutura de pastas
def salvar_bronze(dados: dict) -> str:
    """Salva o JSON bruto particionado por data e timestamp de ingestão."""
    # Obtém data/hora atual em UTC
    agora = datetime.now(timezone.utc)
    # Cria nome da pasta no formato data=YYYY-MM-DD
    pasta = os.path.join(BRONZE_PATH, f"data={agora.strftime('%Y-%m-%d')}")
    # Cria a pasta se não existir
    os.makedirs(pasta, exist_ok=True)

    # Define o nome do arquivo
    nome_arquivo = f"posicao_{agora.strftime('%H%M%S')}.json"
    caminho = os.path.join(pasta, nome_arquivo)

    # Cria o payload enriquecido
    payload = {
        # timestamp da ingestão em formato ISO
        "ingestion_timestamp_utc": agora.isoformat(),
        # identificação da fonte de dados
        "source": "olhovivo_sptrans",
        # os dados originais da API (mantidos intactos)
        "data": dados,
    }

    # Abre arquivo para escrita com encoding UTF-8
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return caminho

# Valida se token existe
def main():
    if not TOKEN:
        raise ValueError(
            "TOKEN não encontrado. Verifique se o arquivo .env existe "
            "e contém a linha SPTRANS_TOKEN=seu_token_aqui"
        )

    session = requests.Session()

    if not autenticar(session, TOKEN):
        raise RuntimeError("Falha na autenticação. Verifique se o token está correto/ativo.")

    print("Autenticado com sucesso.")

    # Chama API para obter posições dos veículos
    dados = buscar_posicoes(session)

    # Verifica se dados existem e contêm campo "l" (linhas)
    if not dados or "l" not in dados:
        # Se vazio/inválido, exibe aviso e encerra
        print("Aviso: API retornou dado vazio/inválido nesta chamada. Nada foi salvo.")
        return
    
    # Salva os dados
    caminho = salvar_bronze(dados)

    print(f"Ingestão concluída: {caminho}")
    print(f"Total de linhas capturadas: {len(dados.get('l', []))}")

# Executa o script quando rodado diretamente
if __name__ == "__main__":
    main()