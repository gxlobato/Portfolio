> 🇧🇷 Português | [🇺🇸 English below](#-portfolio---gabi-lobato-1)

# 📊 Portfolio — Gabriela Lobato

Portfólio de projetos de **Engenharia de Dados e Analytics**, com pipelines
de ponta a ponta: ingestão, modelagem dimensional, automação e visualização.

## Projetos

### ⚖️ [JurisTrack — Monitoramento de Processos Judiciais](https://github.com/gxlobato/Portfolio/blob/main/JurisTrack)

Sistema de monitoramento de processos judiciais para escritórios de advocacia.
Clientes e processos são cadastrados em um banco relacional; um pipeline em
Python consulta diariamente a API pública Datajud (CNJ) para atualizar o
status de cada processo, com identificação automática do tribunal a partir
do próprio número do processo (padrão CNJ). Os dados atualizados são
consumidos por um dashboard em Power BI.

**Tecnologias**: PostgreSQL (Neon), Python, psycopg2, requests, API Datajud (CNJ), Power BI/DAX.

📄 Detalhes completos no [README do projeto](https://github.com/gxlobato/Portfolio/blob/main/JurisTrack/readme.md).

### 🏥 [Rede de Farmácias — Estoque (DrugStoreDB)](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico)

Data warehouse para monitoramento de saúde de estoque em uma rede simulada
de farmácias. Inclui modelagem em star schema, pipelines Python, previsão
de demanda com Machine Learning e dashboard em Power BI.

**Tecnologias**: PostgreSQL (Neon), Python, pandas, psycopg2, scikit-learn,
GitHub Actions, Power BI/DAX.

📄 Detalhes completos no [README do projeto](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico/README.md).

### 🚌 [FleetTrack — Pipeline de Frota de Ônibus em Tempo Real](https://github.com/gxlobato/Portfolio/blob/main/olho-vivo-medallion)

Pipeline de dados em tempo real da frota de ônibus de São Paulo, construído
com arquitetura Medallion (Bronze → Silver → Gold), consumindo a API pública
Olho Vivo da SPTrans. Ingestão resiliente a falhas da API, processamento
incremental com checkpoint, orquestração com retry automático via Prefect,
e testes unitários da lógica de transformação.

**Tecnologias**: Python, requests, python-dotenv, pandas, pyarrow (Parquet),
Prefect, pytest, API Pública Olho Vivo (SPTrans).

📄 Detalhes completos no [README do projeto](https://github.com/gxlobato/Portfolio/blob/main/olho-vivo-medallion/README.md).

## Tecnologias gerais do portfólio

| Categoria            | Ferramentas       |
| -------------------- | ----------------- |
| Linguagem            | Python             |
| Banco de dados       | PostgreSQL (Neon)  |
| Manipulação de dados | pandas             |
| Armazenamento        | Parquet            |
| Machine Learning     | scikit-learn       |
| Orquestração         | Prefect            |
| Automação            | GitHub Actions     |
| Testes               | pytest             |
| Visualização         | Power BI           |
| Versionamento        | Git / GitHub       |

## Estrutura do repositório

```
Portfolio/
├── JurisTrack/             # Monitoramento de processos judiciais (CNJ Datajud)
├── estoque_farmaceutico/   # Data warehouse de estoque farmacêutico
├── FleetTrack/    # Pipeline de frota de ônibus em tempo real (Medallion)
└── .github/workflows/      # Automação dos pipelines
```

---

# 🇺🇸 Portfolio — Gabriela Lobato

Portfolio of **Data Engineering and Analytics** projects, featuring
end-to-end pipelines: ingestion, dimensional modeling, automation and
visualization.

## Projects

### ⚖️ [JurisTrack — Judicial Process Monitoring](https://github.com/gxlobato/Portfolio/blob/main/JurisTrack)

A judicial process monitoring system for law firms. Clients and legal
processes are registered in a relational database; a daily Python pipeline
queries the public Datajud API (Brazil's National Council of Justice, CNJ)
to update each process's status, automatically identifying the relevant
court from the process number itself (CNJ standard format). Updated data
is consumed by a Power BI dashboard.

**Tech stack**: PostgreSQL (Neon), Python, psycopg2, requests, Datajud API (CNJ), Power BI/DAX.

📄 Full details in the [project README](https://github.com/gxlobato/Portfolio/blob/main/JurisTrack/README.md).

### 🏥 [Pharmacy Chain — Stock (DrugStoreDB)](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico)

A data warehouse for stock health monitoring in a simulated pharmacy chain.
Includes star schema modeling, Python pipelines, ML-based demand
forecasting, and a Power BI dashboard.

**Tech stack**: PostgreSQL (Neon), Python, pandas, psycopg2, scikit-learn,
GitHub Actions, Power BI/DAX.

📄 Full details in the [project README](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico/README.md).

### 🚌 [olho-vivo-medallion — Real-Time Bus Fleet Pipeline](https://github.com/gxlobato/Portfolio/blob/main/olho-vivo-medallion)

A real-time data pipeline for São Paulo's bus fleet, built with the
Medallion architecture (Bronze → Silver → Gold), consuming SPTrans' public
Olho Vivo API. Features fault-tolerant ingestion, incremental processing
with checkpointing, orchestration with automatic retries via Prefect, and
unit tests covering the transformation logic.

**Tech stack**: Python, requests, python-dotenv, pandas, pyarrow (Parquet),
Prefect, pytest, Olho Vivo Public API (SPTrans).

📄 Full details in the [project README](https://github.com/gxlobato/Portfolio/blob/main/olho-vivo-medallion/README.md).

## General portfolio tech stack

| Category         | Tools             |
| ----------------- | ----------------- |
| Language          | Python             |
| Database          | PostgreSQL (Neon)  |
| Data handling     | pandas             |
| Storage           | Parquet            |
| Machine Learning  | scikit-learn       |
| Orchestration     | Prefect            |
| Automation        | GitHub Actions     |
| Testing           | pytest             |
| Visualization     | Power BI           |
| Version control   | Git / GitHub       |

## Repository structure

```
Portfolio/
├── JurisTrack/             # Judicial process monitoring (CNJ Datajud)
├── estoque_farmaceutico/   # Pharmacy stock data warehouse
├── olho-vivo-medallion/    # Real-time bus fleet pipeline (Medallion)
├── DQ/                     # Data Quality project (work in progress)
└── .github/workflows/      # Pipeline automation
```
