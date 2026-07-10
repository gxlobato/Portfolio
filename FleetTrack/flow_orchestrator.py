"""
Orquestração do pipeline Olho Vivo (Bronze -> Silver -> Gold) usando Prefect.

Antes de rodar:
    pip install prefect

Como rodar uma vez, manualmente:
    python orquestracao_flow.py

Como agendar (roda sozinho em intervalos, com Prefect cuidando do scheduling):
    Descomente a chamada .serve() no final do arquivo.
"""

from prefect import flow, task, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner

from ingest_bronze import main as rodar_ingestao_bronze
from transform_silver_incremental import main as rodar_silver_incremental
from load_gold import main as rodar_gold

# Tarefas do Prefect (cada uma é uma etapa do pipeline)
@task(retries=2, retry_delay_seconds=30, name="Ingestão Bronze")
def task_ingest_bronze():
    """
    Busca dado bruto da API Olho Vivo.
    Retry automático: se a API falhar (instabilidade pontual), tenta de novo
    até 2 vezes, esperando 30s entre tentativas, antes de desistir.
    """
    logger = get_run_logger()
    logger.info("Iniciando ingestão Bronze.")
    rodar_ingestao_bronze()
    logger.info("Ingestão Bronze concluída.")


@task(name="Transformação Silver (incremental)")
def task_transform_silver():
    """Processa apenas arquivos Bronze novos, faz append na Silver."""
    logger = get_run_logger()
    logger.info("Iniciando transformação Silver.")
    rodar_silver_incremental()
    logger.info("Transformação Silver concluída.")


@task(name="Agregação Gold")
def task_gerar_gold():
    """Recalcula as tabelas agregadas da Gold a partir da Silver atualizada."""
    logger = get_run_logger()
    logger.info("Iniciando agregação Gold.")
    rodar_gold()
    logger.info("Agregação Gold concluída.")

# Orquestração do pipeline completo
@flow(name="Pipeline Olho Vivo - Bronze a Gold", task_runner=ConcurrentTaskRunner())
def pipeline_olho_vivo():
    """
    Orquestra o pipeline completo. As tarefas rodam em sequência porque
    cada uma depende do resultado da anterior (dependência implícita:
    Silver só roda se Bronze retornar sem erro; Gold só roda se Silver retornar).
    """
    resultado_bronze = task_ingest_bronze()
    resultado_silver = task_transform_silver(wait_for=[resultado_bronze])
    task_gerar_gold(wait_for=[resultado_silver])

# Ponto de entrada do script
if __name__ == "__main__":
    # Execução única (manual)
    #pipeline_olho_vivo()

    # Para rodar agendado sozinho (ex: a cada 5 min), comente a linha acima
    # e descomente as linhas abaixo:
    #
     pipeline_olho_vivo.serve(
         name="olho-vivo-agendado",
         interval=300,  # segundos
     )