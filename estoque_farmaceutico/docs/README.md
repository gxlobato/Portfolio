# Estoque Farmacêutico — Previsibilidade de Demanda

Projeto de portfólio: pipeline de dados sintéticos de uma rede de distribuição
farmacêutica (10 centros de distribuição, 20 medicamentos, 200 clientes),
com modelo dimensional e integração com modelos de previsão de demanda.

## Stack
- **Neon (PostgreSQL)** — banco de dados (`DrugStoreDB`)
- **Python** (pandas, NumPy, Faker, statsmodels/Prophet/XGBoost) — geração
  de dados sintéticos e modelagem de forecast
- **Power BI** — camada de visualização (em construção)

## Arquitetura (camadas)

```
raw         → dados sintéticos brutos (fonte simulada)
analytics   → modelo dimensional (star schema)
forecast    → saídas do pipeline de previsão (fonte externa)
```

O schema `forecast` é tratado como uma "fonte externa" cujo `medicamento_key`
já é a mesma chave conformada de `analytics.dim_medicamento` — por isso as
fatos de previsão entram direto no star schema sem necessidade de remapeamento.

## Modelo dimensional (`analytics`)

| Tabela | Tipo | Grão |
|---|---|---|
| `dim_tempo` | Dimensão | 1 linha por semana |
| `dim_sala` | Dimensão | 1 linha por centro de distribuição |
| `dim_medicamento` | Dimensão | 1 linha por produto |
| `dim_cliente` | Dimensão | 1 linha por cliente (FK → dim_sala) |
| `fact_estoque_semanal` | Fato | sala × medicamento × semana (histórico realizado) |
| `fact_previsao_medicamento` | Fato | medicamento × semana futura (previsão) |
| `fact_recomendacao_estoque` | Fato | medicamento × data do snapshot (recomendação de compra) |

## Ordem de execução dos scripts (`/sql`)

1. `01_raw_schema_ddl.sql` — cria o schema `raw` e suas tabelas
2. `02_raw_data_load.sql` — popula `raw` com dados sintéticos (inclui
   bloco PL/pgSQL que simula 5 anos de movimentação semanal com
   sazonalidade, política de reposição e ruptura de estoque)
3. `03_analytics_schema_ddl.sql` — cria o schema `analytics` (star schema)
4. `04_analytics_data_load.sql` — popula as dimensões e a fato de
   estoque histórico via upsert idempotente
5. `05_forecast_integration_ddl.sql` — estende `dim_tempo` com semanas
   futuras e cria as fatos de previsão/recomendação
6. `06_forecast_integration_load.sql` — popula essas fatos a partir do
   schema `forecast` (gerado pelo pipeline de modelagem em Python)

## Padrões de engenharia adotados

- Chaves substitutas (`*_key`) via `SERIAL`/`BIGSERIAL`
- Upsert idempotente: `INSERT ... ON CONFLICT DO UPDATE ... WHERE IS DISTINCT FROM`
  (pode reexecutar os scripts de carga sem duplicar ou sobrescrever sem necessidade)
- Auditoria com `CreateDt`/`ChangedTM`
- Dimensões conformadas entre os schemas `analytics` e `forecast`
  (mesma chave substituta de medicamento reaproveitada)

## Métricas calculadas

- `valor_estoque_final` — saldo final × preço unitário (capital imobilizado)
- `dias_cobertura_estimados` — saldo final ÷ consumo médio diário da semana
- `ruptura_estoque` — flag de estoque zerado durante a semana

## Próximos passos

- Dashboard Power BI consumindo o star schema (histórico + previsão numa
  única linha do tempo)
- Documentação do pipeline de modelagem (Holt-Winters, Prophet, XGBoost)
  que alimenta o schema `forecast`
