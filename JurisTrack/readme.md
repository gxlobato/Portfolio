# JurisTrack

Sistema de monitoramento de processos judiciais para escritórios de advocacia. O projeto simula a infraestrutura de dados de um escritório real: cadastro de clientes e processos em banco relacional, atualização automática diária via API pública do CNJ, e visualização em dashboard.

## 🎯 Objetivo

Automatizar o acompanhamento de processos judiciais, eliminando a consulta manual repetitiva ao site dos tribunais. O fluxo completo é:

```
Cadastro de processos (PostgreSQL)
        ↓
Pipeline diário (Python) → API Datajud (CNJ)
        ↓
Tabelas atualizadas (status, movimentações, detalhes)
        ↓
Dashboard Power BI
```

## 🏗️ Arquitetura

**Banco de dados:** PostgreSQL (hospedado na Neon)
- `processos` — cadastro base dos processos monitorados
- `clientes` — dados dos clientes, com verificação de duplicidade no cadastro
- `status_processos` — status atual de cada processo

**Pipeline:** scripts Python executados diariamente, responsáveis por:
- Consultar a API Datajud (CNJ) para cada processo cadastrado
- Decodificar automaticamente o tribunal a partir do próprio número do processo (padrão CNJ `NNNNNNN-DD.AAAA.J.TR.OOOO`), sem exigir esse dado do usuário
- Classificar a área do processo por heurística de palavras-chave sobre `classe.nome`
- Persistir os dados no PostgreSQL com `psycopg2`, usando `ON CONFLICT DO NOTHING` para idempotência

**Dashboard:** Power BI, consumindo diretamente as tabelas do PostgreSQL, com:
- KPIs: quantidade de Processos, Data de atualização mais Recente
- Tabela central de movimentações
- Filtros por cliente

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Banco de dados | PostgreSQL (Neon) |
| Linguagem do pipeline | Python |
| Integração com banco | psycopg2 |
| Fonte de dados | API Pública Datajud (CNJ) |
| Visualização | Power BI (DAX) |
| Execução local | PowerShell |

## 🧠 Decisões técnicas

- **Decodificação automática de tribunal:** o número do processo já contém a informação do tribunal (dígitos 14–16). Aproveitar esse padrão evita erro humano e input manual, tornando o cadastro mais simples.
- **Classificação de área por heurística:** a tabela oficial de classes (TPU) do CNJ exige login e muda com frequência. Optei por um dicionário de palavras-chave sobre `classe.nome`, uma solução mais simples e suficiente para o objetivo do dashboard, mesmo sabendo que é menos precisa que a fonte oficial.
- **Idempotência no pipeline:** como o pipeline roda diariamente e pode ser reexecutado (inclusive em modo de simulação retroativa com um parâmetro de data), todas as inserções usam `ON CONFLICT DO NOTHING` e constraints de unicidade para evitar duplicação de dados.
- **Variáveis de ambiente para credenciais:** nenhuma credencial de banco fica hardcoded nos scripts; tudo é lido via `DATABASE_URL`.
- **Separação de camadas:** o pipeline Python cuida só da coleta e persistência dos dados; toda a modelagem de métricas e relações fica no Power BI (DAX), mantendo cada parte do projeto com uma responsabilidade clara.

## 📊 Dashboard

O dashboard final entrega uma visão única de todos os processos monitorados, com indicadores de atividade e permitindo o acompanhamento por cliente.

## 📁 Estrutura do repositório

```
juristrack/
├── cadastra_processo.py   # cadastra cliente + processo, decodificando o tribunal automaticamente
├── popula_dados.py          # consulta a Datajud para cada processo cadastrado e salva o retorno bruto
├── status_diario.py         # extrai os dados relevantes do retorno bruto para a tabela principal de processos
├── .env.example              # modelo das variáveis de ambiente necessárias (sem valores reais)
└── README.md
├── PowerBI/
     ├────JurisTrack.pbix        #arquivo do power bi desktop
```
> ⚠️ Nenhum script contém credenciais no código. Todas as chaves e strings de conexão são lidas de variáveis de ambiente (`DATABASE_URL`, `DATAJUD_API_KEY`), conforme boa prática de segurança.

## 🚀 Como executar

```powershell
# 1. Configurar variáveis de ambiente (PowerShell)
$env:DATABASE_URL = "postgresql://usuario:senha@host/Advocacia?sslmode=require"
$env:DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

# 2. Instalar dependências
pip install psycopg2 requests

# 3. Rodar os scripts conforme a necessidade
python popula_dados.py          # carga inicial de dados de teste
python identifica_tribunal.py   # consulta pontual de um processo
python status_diario.py         # atualização diária de status
```

**Importante:** o arquivo `.env` (ou qualquer arquivo com credenciais reais) deve estar no `.gitignore` e nunca ser commitado.

## 📌 Status do projeto

Projeto em desenvolvimento ativo, construído como parte do meu portfólio para demonstrar a construção de um pipeline de dados de ponta a ponta: banco relacional, integração com API externa, tratamento de dados e visualização.

## 📄 Documentação API Pública

https://datajud-wiki.cnj.jus.br/api-publica/

---

Desenvolvido por Gabriela Lobato.
