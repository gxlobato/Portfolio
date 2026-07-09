import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import json
import re

# ---------- CONFIGURACOES ----------
# Credencial lida de variavel de ambiente (nunca hardcoded)
NEON_CONNECTION_STRING = os.environ["DATABASE_URL"]

def extrair_ultimo_movimento(movimentos):
    """
    Extrai o ultimo movimento da lista de movimentos
    """
    if not movimentos or len(movimentos) == 0:
        return None, None, None, None
    
    # Ordena por dataHora (mais recente primeiro)
    movimentos_ordenados = sorted(movimentos, key=lambda m: m.get('dataHora', ''), reverse=True)
    ultimo = movimentos_ordenados[0]
    
    nome = ultimo.get('nome')
    codigo = ultimo.get('codigo')
    data_hora = ultimo.get('dataHora')
    orgao = ultimo.get('orgaoJulgador', {}).get('nome') if 'orgaoJulgador' in ultimo else None
    
    return nome, codigo, data_hora, orgao

def extrair_primeiro_assunto(assuntos_list):
    """
    Extrai apenas o primeiro assunto do processo
    Retorna um dicionario com os dados do primeiro assunto
    """
    if not assuntos_list or len(assuntos_list) == 0:
        return {
            'assunto_1_nome': None,
            'assunto_1_codigo': None
        }
    
    primeiro_assunto = assuntos_list[0]
    return {
        'assunto_1_nome': primeiro_assunto.get('nome'),
        'assunto_1_codigo': primeiro_assunto.get('codigo'),
    }

def converter_data_ajuizamento(data_str):
    """
    Converte data no formato YYYYMMDDHHMMSS para DATE
    """
    if not data_str or len(data_str) < 8:
        return None
    
    try:
        # Pega os primeiros 8 caracteres (YYYYMMDD)
        return datetime.strptime(data_str[:8], '%Y%m%d').date()
    except:
        return None

def migrar_status_para_processos():
    """
    Migra os dados da tabela status_processos para a tabela processos
    """
    conn = None
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        
        with conn:
            with conn.cursor() as cur:
                # Busca os registros mais recentes de cada processo
                cur.execute("""
                    WITH ultimos_status AS (
                        SELECT DISTINCT ON (sp.processo_id) 
                            sp.processo_id,
                            sp.data_consulta,
                            sp.payload_bruto
                        FROM cadastro.status_processos sp
                        WHERE sp.payload_bruto IS NOT NULL
                        ORDER BY sp.processo_id, sp.data_consulta DESC
                    )
                    SELECT 
                        us.processo_id,
                        us.data_consulta,
                        us.payload_bruto,
                        p.numero_processo
                    FROM ultimos_status us
                    INNER JOIN cadastro.processos p ON us.processo_id = p.id
                """)
                
                registros = cur.fetchall()
                total_registros = len(registros)
                print(f"Total de registros a processar: {total_registros}")
                
                for idx, registro in enumerate(registros, 1):
                    try:
                        (processo_id, data_consulta, payload_bruto, numero_processo) = registro
                        
                        # Extrai dados do JSON
                        dados = payload_bruto if isinstance(payload_bruto, dict) else json.loads(payload_bruto)
                        
                        # Extrai informacoes basicas
                        classe = dados.get('classe', {})
                        formato = dados.get('formato', {})
                        sistema = dados.get('sistema', {})
                        orgao_julgador = dados.get('orgaoJulgador', {})
                        
                        # Extrai apenas o primeiro assunto
                        assuntos = extrair_primeiro_assunto(dados.get('assuntos', []))
                        
                        # Converte data de ajuizamento
                        data_ajuizamento = converter_data_ajuizamento(dados.get('dataAjuizamento'))
                        
                        # Atualiza o processo com os dados extraidos
                        cur.execute("""
                            UPDATE cadastro.processos SET
                                data_ajuizamento = %s,
                                grau = %s,
                                nivel_sigilo = %s,
                                classe_nome = %s,
                                classe_codigo = %s,
                                formato_nome = %s,
                                formato_codigo = %s,
                                sistema_nome = %s,
                                sistema_codigo = %s,
                                tribunal = %s,
                                orgao_julgador_nome = %s,
                                orgao_julgador_codigo = %s,
                                orgao_julgador_municipio_ibge = %s,
                                assunto_1_nome = %s,
                                assunto_1_codigo = %s,
                                ultima_atualizacao = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            data_ajuizamento,
                            dados.get('grau'),
                            dados.get('nivelSigilo'),
                            classe.get('nome'),
                            classe.get('codigo'),
                            formato.get('nome'),
                            formato.get('codigo'),
                            sistema.get('nome'),
                            sistema.get('codigo'),
                            dados.get('tribunal'),
                            orgao_julgador.get('nome'),
                            orgao_julgador.get('codigo'),
                            orgao_julgador.get('codigoMunicipioIBGE'),
                            assuntos['assunto_1_nome'],
                            assuntos['assunto_1_codigo'],
                            processo_id
                        ))
                        
                        if idx % 100 == 0 or idx == total_registros:
                            print(f"Processados {idx}/{total_registros} registros")
                        
                    except json.JSONDecodeError as e:
                        print(f"Erro ao decodificar JSON do processo ID {processo_id}: {e}")
                        continue
                    except Exception as e:
                        print(f"Erro ao atualizar processo ID {processo_id}: {e}")
                        continue
                        
        print(f"Migracao concluida! {total_registros} registros processados.")
        
    except Exception as e:
        print(f"Erro na migracao: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Iniciando migracao de dados...")
    
    # Executa a migracao
    migrar_status_para_processos()
    
    print("\nMigracao concluida com sucesso!")