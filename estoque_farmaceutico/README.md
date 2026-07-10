# 🏥 Rede de Farmácias — Data Warehouse de Estoque (DrugStoreDB)

> 🇧🇷 Português | [🇺🇸 English below](#-pharmacy-chain--stock-data-warehouse-drugstoredb)

## Sobre o projeto

Pipeline de dados de ponta a ponta para monitoramento de saúde de estoque em uma
rede simulada de farmácias: geração de dados sintéticos, modelagem dimensional
(star schema), pipelines de ETL em Python, previsão de demanda com Machine
Learning e dashboard em Power BI.

O objetivo é demonstrar, na prática, as etapas de um projeto real de Engenharia
de Dados / Analytics: da ingestão de dados brutos até a entrega de indicadores
de negócio (KPIs) para tomada de decisão.

## Problema de negócio

Redes de farmácias precisam evitar dois problemas opostos:
- **Ruptura de estoque**: faltar medicamento na prateleira.
- **Perda por vencimento**: excesso de estoque que vence antes de ser vendido.

O projeto constrói um sistema de alertas (`fact_alerta_estoque`) que classifica
cada combinação sala/medicamento em níveis de risco: `RUPTURA`, `CRÍTICO`,
`VENC_PRÓXIMO`, `ATENÇÃO` ou `OK`.

## Arquitetura

```
raw/ (CSV)  →  Python (pandas + psycopg2)  →  PostgreSQL (Neon)  →  Power BI
                                                  ├── raw schema
                                                  └── analytics schema (star schema)
```

### Camada raw
Tabelas de origem: `salas_estoque`, `medicamentos`, `lotes`,
`estoque_movimentacao_semanal`, `clientes`.

### Camada analytics (star schema)
- **Dimensões**: `dim_sala`, `dim_medicamento`, `dim_lote`, `dim_tempo`,
  `dim_cliente`.
- **Fatos**:
  - `fact_estoque_semanal` — histórico de 5 anos de movimentação.
  - `fact_estoque_atual` — snapshot atual (truncate-and-reload).
  - `fact_alerta_estoque` — níveis de alerta de estoque.
  - `fact_estoque_forecast` — previsão de demanda (Machine Learning).

## Tecnologias usadas

| Camada | Tecnologia | Uso no projeto |
|---|---|---|
| Banco de dados | **PostgreSQL (Neon)** | Data warehouse serverless, com branching para testar mudanças de schema sem afetar produção |
| Linguagem | **Python** | Scripts de ETL e pipeline de forecast |
| Manipulação de dados | **pandas** | Transformação e limpeza dos dados antes da carga |
| Conexão com banco | **psycopg2** | Execução de comandos SQL a partir do Python |
| Machine Learning | **scikit-learn (RandomForestRegressor)** | Previsão de demanda futura por medicamento |
| Segurança de credenciais | **python-dotenv** | Variáveis de ambiente (usuário/senha do banco fora do código) |
| Automação | **GitHub Actions** | Execução automática e agendada dos pipelines |
| Visualização | **Power BI + DAX** | Dashboard de KPIs, curva ABC, vencimentos e previsão vs. real |

## Como os pipelines funcionam

Cada script segue o mesmo padrão:
1. Conecta ao banco com `psycopg2` (autocommit).
2. Recria a tabela de destino (`DROP TABLE IF EXISTS ... CASCADE` + `CREATE TABLE`)
   ou faz upsert com `ON CONFLICT DO UPDATE`.
3. Grava colunas de auditoria (`CreateDt`, `ChangedTM`).

Scripts principais (`estoque_farmaceutico/script/`):
- `analytics.dim_*.py` — carga das dimensões.
- `analytics.fact_estoque_atual.py` — snapshot atual de estoque.
- `analytics.fact_alerta_estoque.py` — cálculo dos níveis de alerta.
- `analytics.fact_estoque_semanal.py` — histórico semanal.
- `pipeline_forecast.py` — previsão de demanda com RandomForest, grava em
  `fact_estoque_forecast`.
- `atualizar_estoque_semanal.py` — atualização incremental semanal.

## Automação (GitHub Actions)

Os pipelines rodam automaticamente via workflows em `.github/workflows/`,
usando secrets do repositório (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_PORT`) — nenhuma credencial fica exposta no código.

## 📊 Dashboard Power BI

O dashboard consome o modelo estrela hospedado no PostgreSQL (Neon) e está
organizado em três páginas:

- **Alertas**: classifica o estoque por nível de risco (RUPTURA, CRÍTICO,
  VENC_PRÓXIMO, ATENÇÃO, OK), com curva ABC de medicamentos.
- **Tendências**: histórico de movimentação de estoque, giro e cobertura,
  com indicadores de sazonalidade.
- **Previsão**: projeção de saídas e recomendação de reposição, calculada
  por um modelo de Machine Learning (Random Forest) treinado sobre o
  histórico semanal de estoque.

As medidas DAX incluem giro de estoque, cobertura de estoque, taxa de
ruptura, sinalizadores de vencimento e curva ABC.

## Demonstração

<p align="center">
  <img
    src="https://raw.githubusercontent.com/gxlobato/Portfolio/main/estoque_farmaceutico/Dashboard/demo.gif"
    alt="Demonstração do Dashboard"
    width="100%">
</p>

## Estrutura de pastas

```
estoque_farmaceutico/
├── raw/           # CSVs de origem (dados sintéticos)
├── script/        # Pipelines Python (ETL, dimensões, fatos, forecast)
└── requirements.txt
```

## Como rodar localmente

```bash
pip install -r estoque_farmaceutico/requirements.txt
# configure um arquivo .env com DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
python estoque_farmaceutico/script/analytics.dim_sala.py
```

---

# 🇺🇸 Pharmacy Chain — Stock Data Warehouse (DrugStoreDB)

## About the project

An end-to-end data pipeline for stock health monitoring in a simulated
pharmacy chain: synthetic data generation, dimensional modeling (star schema),
Python ETL pipelines, Machine Learning demand forecasting, and a Power BI
dashboard.

The goal is to showcase practical Data Engineering / Analytics skills: from
raw data ingestion to delivering business KPIs for decision-making.

## Business problem

Pharmacy chains need to avoid two opposite problems:
- **Stockouts**: running out of a medicine.
- **Expiration loss**: excess stock expiring before it's sold.

The project builds an alert system (`fact_alerta_estoque`) that classifies
each room/medicine combination into risk levels: `RUPTURA` (stockout),
`CRÍTICO` (critical), `VENC_PRÓXIMO` (near expiration), `ATENÇÃO` (attention)
or `OK`.

## Architecture

```
raw/ (CSV)  →  Python (pandas + psycopg2)  →  PostgreSQL (Neon)  →  Power BI
                                                  ├── raw schema
                                                  └── analytics schema (star schema)
```

### Raw layer
Source tables: `salas_estoque` (stock rooms), `medicamentos` (medicines),
`lotes` (batches), `estoque_movimentacao_semanal` (weekly movement),
`clientes` (clients).

### Analytics layer (star schema)
- **Dimensions**: `dim_sala`, `dim_medicamento`, `dim_lote`, `dim_tempo`,
  `dim_cliente`.
- **Facts**:
  - `fact_estoque_semanal` — 5-year weekly movement history.
  - `fact_estoque_atual` — current snapshot (truncate-and-reload).
  - `fact_alerta_estoque` — stock alert levels.
  - `fact_estoque_forecast` — demand forecast (Machine Learning).

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Database | **PostgreSQL (Neon)** | Serverless data warehouse, with branching to test schema changes without touching production |
| Language | **Python** | ETL scripts and forecast pipeline |
| Data handling | **pandas** | Transformation and cleaning before loading |
| DB connection | **psycopg2** | Running SQL commands from Python |
| Machine Learning | **scikit-learn (RandomForestRegressor)** | Forecasting future demand per medicine |
| Credential security | **python-dotenv** | Environment variables (DB credentials kept out of code) |
| Automation | **GitHub Actions** | Scheduled, automated pipeline runs |
| Visualization | **Power BI + DAX** | KPI dashboard, ABC analysis, expiration tracking, forecast vs. actuals |

## How the pipelines work

Each script follows the same pattern:
1. Connect to the database with `psycopg2` (autocommit).
2. Recreate the target table (`DROP TABLE IF EXISTS ... CASCADE` + `CREATE TABLE`)
   or upsert with `ON CONFLICT DO UPDATE`.
3. Write audit columns (`CreateDt`, `ChangedTM`).

Main scripts (`estoque_farmaceutico/script/`):
- `analytics.dim_*.py` — dimension loads.
- `analytics.fact_estoque_atual.py` — current stock snapshot.
- `analytics.fact_alerta_estoque.py` — alert level calculation.
- `analytics.fact_estoque_semanal.py` — weekly history.
- `pipeline_forecast.py` — RandomForest demand forecast, writes to
  `fact_estoque_forecast`.
- `atualizar_estoque_semanal.py` — weekly incremental update.

## Automation (GitHub Actions)

Pipelines run automatically via workflows in `.github/workflows/`, using
repository secrets (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_PORT`) — no credentials exposed in code.

## 📊 Power BI Dashboard

The dashboard consumes the star-schema model hosted on PostgreSQL (Neon)
and is organized into three pages:

- **Alerts**: classifies inventory by risk level (STOCKOUT, CRITICAL,
  NEAR_EXPIRY, ATTENTION, OK), including an ABC medication curve.
- **Trends**: historical stock movement, turnover, and coverage, with
  seasonality indicators.
- **Forecast**: projected demand and restock recommendations, calculated
  by a Machine Learning model (Random Forest) trained on weekly stock
  history.

DAX measures include inventory turnover, stock coverage, stockout rate,
expiration flags, and ABC curve analysis.

## Demonstration

<p align="center">
  <img
    src="https://raw.githubusercontent.com/gxlobato/Portfolio/main/estoque_farmaceutico/Dashboard/demo.gif"
    alt="Dashboard Demonstration"
    width="100%">
</p>

## Folder structure

```
estoque_farmaceutico/
├── raw/           # Source CSVs (synthetic data)
├── script/        # Python pipelines (ETL, dimensions, facts, forecast)
└── requirements.txt
```

## Running locally

```bash
pip install -r estoque_farmaceutico/requirements.txt
# create a .env file with DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
python estoque_farmaceutico/script/analytics.dim_sala.py
```
