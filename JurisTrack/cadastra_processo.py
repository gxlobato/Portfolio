import os
import re
import psycopg2

# ---------- CONFIGURACOES ----------
NEON_CONNECTION_STRING = os.environ["DATABASE_URL"]

# Mapeamento do digito J (segmento da Justica)
SEGMENTOS = {
    "3": "stj",
    "4": "trf",   # Justica Federal
    "5": "trt",   # Justica do Trabalho
    "8": "tj",    # Justica Estadual
}

# TR (01 a 06) -> TRF
TRF = {f"{i:02d}": f"trf{i}" for i in range(1, 7)}

# TR (01 a 24) -> TRT
TRT = {f"{i:02d}": f"trt{i}" for i in range(1, 25)}

# TR -> TJ (conforme Resolucao 65/2008, Anexo dos TJs)
TJ = {
    "01": "tjac", "02": "tjal", "03": "tjap", "04": "tjam", "05": "tjba",
    "06": "tjce", "07": "tjdft", "08": "tjes", "09": "tjgo", "10": "tjma",
    "11": "tjmt", "12": "tjms", "13": "tjmg", "14": "tjpa", "15": "tjpb",
    "16": "tjpr", "17": "tjpe", "18": "tjpi", "19": "tjrj", "20": "tjrn",
    "21": "tjrs", "22": "tjro", "23": "tjrr", "24": "tjsc", "25": "tjse",
    "26": "tjsp", "27": "tjto",
}


def identificar_tribunal(numero_processo: str):
    """Extrai o alias do tribunal a partir do numero CNJ do processo."""
    digitos = re.sub(r"\D", "", numero_processo)  # remove pontos e tracos

    if len(digitos) != 20:
        raise ValueError(f"Numero invalido: esperava 20 digitos, recebido {len(digitos)}")

    j = digitos[13]        # segmento
    tr = digitos[14:16]    # tribunal

    if j == "3":
        return "stj"
    elif j == "4":
        return TRF.get(tr)
    elif j == "5":
        return TRT.get(tr)
    elif j == "8":
        return TJ.get(tr)
    else:
        return None  # segmento nao mapeado (eleitoral/militar)


def cadastrar_cliente_e_processo(nome_cliente: str, numero_processo: str, tribunal_alias: str):
    """
    Cadastra o cliente (se ainda nao existir) e associa o processo a ele.
    Nao faz nada com o cliente se ele ja existir; apenas reaproveita o id.
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    try:
        with conn:
            with conn.cursor() as cur:
                # verifica se o cliente ja existe
                cur.execute("SELECT id FROM clientes WHERE nome = %s", (nome_cliente,))
                linha = cur.fetchone()

                if linha:
                    cliente_id = linha[0]
                    print(f"Cliente '{nome_cliente}' ja cadastrado (id {cliente_id}).")
                else:
                    cur.execute(
                        "INSERT INTO clientes (nome) VALUES (%s) RETURNING id",
                        (nome_cliente,),
                    )
                    cliente_id = cur.fetchone()[0]
                    print(f"Cliente '{nome_cliente}' cadastrado (id {cliente_id}).")

                # cadastra o processo, associado ao cliente
                cur.execute(
                    """
                    INSERT INTO processos (cliente_id, numero_processo, tribunal_alias)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (numero_processo) DO NOTHING
                    """,
                    (cliente_id, numero_processo, tribunal_alias),
                )

                if cur.rowcount == 0:
                    print(f"Processo {numero_processo} ja estava cadastrado. Nenhuma alteracao realizada.")
                else:
                    print(f"Processo {numero_processo} cadastrado para '{nome_cliente}' ({tribunal_alias}).")
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Sistema de Cadastro de Processos ===\n")
    
    numero = input("Informe o numero do processo: ").strip()
    nome_cliente = input("Informe o nome do cliente: ").strip()

    numero_limpo = re.sub(r"\D", "", numero)
    alias = identificar_tribunal(numero_limpo)

    if not alias:
        print("\nNao foi possivel identificar o tribunal automaticamente. Cadastro nao realizado.")
    else:
        print(f"\nTribunal identificado: {alias}")
        cadastrar_cliente_e_processo(nome_cliente, numero_limpo, alias)
        print("\nOperacao finalizada.")