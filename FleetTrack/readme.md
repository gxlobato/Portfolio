# FleetTrack

Pipeline de dados em tempo real da frota de ônibus de São Paulo, construído com arquitetura **Medallion (Bronze → Silver → Gold)**, consumindo a API pública Olho Vivo da SPTrans.

## 🎯 Objetivo

Demonstrar a construção de um pipeline de dados de ponta a ponta com foco em **engenharia de dados**: não é só extrair e agregar dados, é garantir que o processo seja confiável, rastreável e reprocessável. O fluxo completo é:

```
API Olho Vivo (SPTrans)
        ↓
   Bronze (dado bruto, JSON, particionado por data)
        ↓
   Silver (limpo, tipado, deduplicado, incremental)
        ↓
   Gold (agregações prontas para consumo)
```

## 🏗️ Arquitetura

**Bronze:** ingestão via API, salva como JSON particionado por data de captura, com metadado de ingestão (timestamp, fonte) para rastreabilidade.

**Silver:** processamento **incremental** (checkpoint de arquivos já processados), responsável por:
- "Explodir" a estrutura aninhada da API (linha → veículos) em formato tabular
- Tipagem correta (coordenadas como float, timestamps como datetime)
- Remoção de registros inválidos (sem coordenada ou timestamp de captura)
- Deduplicação por veículo + timestamp de captura

**Gold:** agregações prontas para análise:
- `veiculos_ativos_por_linha_hora` — visão operacional
- `intervalo_atualizacao_por_veiculo` — proxy de frequência/qualidade dos dados

**Orquestração:** Prefect, com retry automático em caso de instabilidade da API e dependência explícita entre as etapas (Silver só roda se Bronze for bem-sucedida; Gold só roda se Silver for bem-sucedida).

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Ingestão | Python + `requests` |
| Autenticação | `.env` + `python-dotenv` |
| Transformação | `pandas` |
| Armazenamento | Parquet (`pyarrow`) |
| Orquestração | Prefect |
| Testes | `pytest` |
| Fonte de dados | API Pública Olho Vivo (SPTrans) |

## 🧠 Decisões técnicas

- **Processamento incremental na Silver:** reexecutar o pipeline não reprocessa o histórico inteiro — um checkpoint em disco guarda quais arquivos Bronze já foram transformados, e novos dados são mesclados (append + deduplicação) aos Parquets existentes.
- **Tratamento de falha silenciosa da API:** a API Olho Vivo pode responder com corpo `null` ou `false` sem retornar um erro HTTP. O pipeline valida o conteúdo antes de persistir, evitando salvar dado corrompido na Bronze.
- **Retry automático na orquestração:** a tarefa de ingestão tem retry configurado no Prefect (2 tentativas, com espera entre elas), para absorver instabilidades pontuais da API sem falhar o pipeline inteiro.
- **Dependência explícita entre etapas:** o Prefect só executa a Silver se a Bronze for bem-sucedida, e só executa a Gold se a Silver for bem-sucedida — falha não propaga silenciosamente.
- **Credenciais seguras:** o token de API nunca fica hardcoded; é lido via `.env` (fora do controle de versão).
- **Testes unitários da lógica de transformação:** as funções de limpeza, deduplicação e parsing são testadas com `pytest`, de forma independente da API real.

## 📁 Estrutura do repositório

```
FleetTrack/
├── bronze/                          # dado bruto (gerado em runtime, fora do git)
├── silver/                          # dado limpo (gerado em runtime, fora do git)
├── gold/                            # dado agregado (gerado em runtime, fora do git)
├── tests/
│   └── transformation_test.py       # testes unitários da lógica de transformação
├── ingest_bronze.py        # ingestão da API -> Bronze
├── transform_silver.py     # funções de transformação (reaproveitadas)
├── transform_silver_incremental.py  # Silver incremental com checkpoint
├── load_gold.py                 # agregações -> Gold
├── flow_orchestrator.py             # orquestração do pipeline com Prefect
├── requirements.txt
├── .env.example                     # modelo das variáveis de ambiente necessárias (sem valores reais)
└── README.md
```
> ⚠️ Nenhum script contém credenciais no código. O token é lido da variável de ambiente `SPTRANS_TOKEN`, conforme boa prática de segurança.

## 🚀 Como executar

```powershell
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Gerar token gratuito em https://www.sptrans.com.br/desenvolvedores/ (menu "Meus Aplicativos")
#    e criar um arquivo .env na raiz do projeto:
#    SPTRANS_TOKEN=seu_token_aqui

# 3. Rodar o pipeline completo (Bronze -> Silver -> Gold)
flow_orchestrator.py 

# 4. (Opcional) Subir a interface visual do Prefect
prefect server start
# acesse http://127.0.0.1:4200
```

**Importante:** o arquivo `.env` (ou qualquer arquivo com credenciais reais) deve estar no `.gitignore` e nunca ser commitado.

## ✅ Testes

O projeto tem testes unitários (`pytest`) para a lógica de transformação da camada Silver, independentes da API real — usam dado fake que simula o formato de um arquivo Bronze.

```powershell
pytest tests/ -v
```

**O que é validado:**
- `test_explodir_para_linhas_gera_um_registro_por_veiculo` — confirma que a estrutura aninhada da API (linha → veículos) é corretamente transformada em um registro por veículo
- `test_explodir_para_linhas_com_payload_vazio_nao_quebra` — garante que o pipeline não quebra se a API retornar uma lista de linhas vazia
- `test_tipar_e_limpar_remove_registro_sem_coordenada` — valida a regra de qualidade que descarta registros sem latitude/longitude, evitando dado inútil na Silver
- `test_deduplicar_remove_mesma_captura_repetida` — confirma que duas capturas idênticas do mesmo veículo (mesmo timestamp) não geram registro duplicado

## 📌 Status do projeto

Projeto em desenvolvimento ativo, construído como parte do meu portfólio para demonstrar a construção de um pipeline de dados de ponta a ponta com arquitetura Medallion: ingestão resiliente, processamento incremental, orquestração e testes automatizados.

## 📄 Documentação da API

https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/

---

Desenvolvido por Gabriela Lobato.