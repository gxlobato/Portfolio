# Portfolio

🇧🇷 [Português](#-português) | 🇺🇸 [English](#-english)

---

## 🇧🇷 Português

Portfólio de projetos de **engenharia de dados e analytics**, com pipelines
completos de ponta a ponta: geração/ingestão de dados, modelagem dimensional
(star schema) em PostgreSQL (Neon), e modelos de previsão (machine learning)
integrados ao mesmo banco.

### Projetos

#### 📦 [`estoque_farmaceutico/`](./estoque_farmaceutico) — Previsibilidade de estoque

Simulação de uma rede de distribuição farmacêutica (10 centros de distribuição,
20 medicamentos, 200 clientes), com:

- **Camada `raw`**: dados sintéticos brutos (salas de estoque, medicamentos,
  clientes, lotes e 5 anos de movimentação semanal de estoque com sazonalidade
  realista — antialérgicos na primavera, respiratórios no inverno, etc.)
- **Camada `analytics`**: modelo dimensional (star schema) com dimensões
  conformadas (`dim_tempo`, `dim_sala`, `dim_medicamento`, `dim_cliente`) e
  fatos de histórico realizado, previsão de demanda e recomendação de compra
- **Pipeline de previsão** (Python + Random Forest): consome o histórico,
  gera previsões de 12 semanas por medicamento e recomendações de reposição
  classificadas por urgência (`CRÍTICO`, `ALTO`, `MÉDIO`, `BAIXO`)

**Stack**: Neon (PostgreSQL), Python (pandas, scikit-learn, psycopg2,
matplotlib), Power BI (em construção)

```
estoque_farmaceutico/
├── sql/
│   ├── 01_raw_schema_ddl.sql           # DDL da camada raw
│   ├── 02_raw_data_load.sql            # Carga sintética (clientes + simulação de estoque)
│   ├── 03_analytics_schema_ddl.sql     # DDL do star schema
│   ├── 04_analytics_data_load.sql      # Upsert das dimensões + fato histórica
│   ├── 05_forecast_integration_ddl.sql # DDL das fatos de previsão/recomendação
│   └── 06_forecast_integration_load.sql# Carga das fatos a partir do schema forecast
├── scripts/
│   ├── Pipeline_forecast.py            # Pipeline de previsão (PT)
│   └── Pipeline_forecast_ing.py        # Pipeline de previsão (EN)
└── docs/
    └── README.md                       # Documentação detalhada do projeto
```

### Padrões de engenharia usados neste portfólio

- **Chaves substitutas** (`*_key`) via `SERIAL`/`BIGSERIAL` nas dimensões e fatos
- **Upsert idempotente**: `INSERT ... ON CONFLICT DO UPDATE ... WHERE IS DISTINCT FROM`
  — scripts de carga podem ser reexecutados sem duplicar ou sobrescrever sem necessidade
- **Auditoria** com colunas `CreateDt`/`ChangedTM`
- **Dimensões conformadas** entre camadas/schemas diferentes (ex.: o
  `medicamento_key` é o mesmo entre `analytics` e `forecast`)
- **Credenciais via variáveis de ambiente** nos scripts Python (nunca hardcoded)

### Próximos passos

- Dashboard Power BI consumindo o star schema (linha do tempo única: histórico + previsão)
- Adicionar projeto de marketing analytics (funil multicanal) a este repositório
- Consolidar os pipelines de previsão (PT/EN) e adicionar `requirements.txt`

---

## 🇺🇸 English

A portfolio of **data engineering and analytics** projects, featuring
complete end-to-end pipelines: data generation/ingestion, dimensional
modeling (star schema) in PostgreSQL (Neon), and forecasting models
(machine learning) integrated into the same database.

### Projects

#### 📦 [`estoque_farmaceutico/`](./estoque_farmaceutico) — Stock Forecasting (Pharma)

Simulation of a pharmaceutical distribution network (10 distribution centers,
20 medications, 200 clients), featuring:

- **`raw` layer**: synthetic source data (stock rooms, medications, clients,
  batches/lots, and 5 years of weekly stock movement with realistic
  seasonality — antihistamines peaking in spring, respiratory drugs in
  winter, etc.)
- **`analytics` layer**: dimensional model (star schema) with conformed
  dimensions (`dim_tempo`, `dim_sala`, `dim_medicamento`, `dim_cliente`) and
  fact tables for realized history, demand forecast, and purchase
  recommendations
- **Forecasting pipeline** (Python + Random Forest): consumes historical
  data, generates 12-week-ahead forecasts per medication, and replenishment
  recommendations ranked by urgency (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)

**Stack**: Neon (PostgreSQL), Python (pandas, scikit-learn, psycopg2,
matplotlib), Power BI (in progress)

```
estoque_farmaceutico/
├── sql/
│   ├── 01_raw_schema_ddl.sql           # DDL for the raw layer
│   ├── 02_raw_data_load.sql            # Synthetic data load (clients + stock simulation)
│   ├── 03_analytics_schema_ddl.sql     # Star schema DDL
│   ├── 04_analytics_data_load.sql      # Upsert for dimensions + historical fact
│   ├── 05_forecast_integration_ddl.sql # DDL for forecast/recommendation facts
│   └── 06_forecast_integration_load.sql# Loads facts from the forecast schema
├── scripts/
│   ├── Pipeline_forecast.py            # Forecasting pipeline (PT)
│   └── Pipeline_forecast_ing.py        # Forecasting pipeline (EN)
└── docs/
    └── README.md                       # Detailed project documentation
```

### Engineering patterns used in this portfolio

- **Surrogate keys** (`*_key`) via `SERIAL`/`BIGSERIAL` on dimensions and facts
- **Idempotent upsert**: `INSERT ... ON CONFLICT DO UPDATE ... WHERE IS DISTINCT FROM`
  — load scripts can be re-run safely without duplicating or unnecessary overwrites
- **Audit columns**: `CreateDt`/`ChangedTM`
- **Conformed dimensions** across layers/schemas (e.g. `medicamento_key` is
  shared between `analytics` and `forecast`)
- **Environment-variable credentials** in Python scripts (never hardcoded)

### Roadmap

- Power BI dashboard consuming the star schema (single timeline: history + forecast)
- Add the marketing analytics project (multichannel funnel) to this repository
- Consolidate the PT/EN forecasting pipelines and add a `requirements.txt`
