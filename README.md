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

📄 Detalhes completos no [README do projeto](https://github.com/gxlobato/Portfolio/blob/main/JurisTrack/README.md).

### 🏥 [Rede de Farmácias — Estoque (DrugStoreDB)](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico)

Data warehouse para monitoramento de saúde de estoque em uma rede simulada
de farmácias. Inclui modelagem em star schema, pipelines Python, previsão
de demanda com Machine Learning e dashboard em Power BI.

**Tecnologias**: PostgreSQL (Neon), Python, pandas, psycopg2, scikit-learn,
GitHub Actions, Power BI/DAX.

📄 Detalhes completos no [README do projeto](https://github.com/gxlobato/Portfolio/blob/main/estoque_farmaceutico/README.md).

### 🔧 DQ (Data Quality)

Projeto em construção.

## Tecnologias gerais do portfólio

| Categoria            | Ferramentas       |
| -------------------- | ----------------- |
| Linguagem            | Python            |
| Banco de dados       | PostgreSQL (Neon) |
| Manipulação de dados | pandas            |
| Machine Learning     | scikit-learn      |
| Automação            | GitHub Actions    |
| Visualização         | Power BI          |
| Versionamento        | Git / GitHub      |

## Estrutura do repositório

```
Portfolio/
├── JurisTrack/             # Monitoramento de processos judiciais (CNJ Datajud)
├── estoque_farmaceutico/   # Data warehouse de estoque farmacêutico
├── DQ/                     # Projeto de Data Quality (em construção)
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

### 🔧 DQ (Data Quality)

Work in progress.

## General portfolio tech stack

| Category         | Tools             |
| ---------------- | ----------------- |
| Language         | Python            |
| Database         | PostgreSQL (Neon) |
| Data handling    | pandas            |
| Machine Learning | scikit-learn      |
| Automation       | GitHub Actions    |
| Visualization    | Power BI          |
| Version control  | Git / GitHub      |

## Repository structure

```
Portfolio/
├── JurisTrack/             # Judicial process monitoring (CNJ Datajud)
├── estoque_farmaceutico/   # Pharmacy stock data warehouse
├── DQ/                     # Data Quality project (work in progress)
└── .github/workflows/      # Pipeline automation
```
