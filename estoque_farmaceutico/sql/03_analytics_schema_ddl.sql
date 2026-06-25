-- ============================================================================
-- ESTOQUE FARMACÊUTICO — MODELO DIMENSIONAL (ANALYTICS)
-- Star schema: dim_tempo, dim_sala, dim_medicamento, dim_cliente,
-- fact_estoque_semanal (grão: sala x medicamento x semana)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- ----------------------------------------------------------------------------
-- analytics.dim_tempo
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.dim_tempo (
    tempo_key SERIAL PRIMARY KEY,
    semana_referencia DATE UNIQUE NOT NULL,
    ano SMALLINT NOT NULL,
    trimestre SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    mes_nome VARCHAR(20) NOT NULL,
    semana_numero SMALLINT NOT NULL,
    dia_inicio_semana DATE NOT NULL,
    dia_fim_semana DATE NOT NULL,
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- analytics.dim_sala
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.dim_sala (
    sala_key SERIAL PRIMARY KEY,
    sala_id SMALLINT UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    regiao VARCHAR(20) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL,
    capacidade_m3 NUMERIC(10,2) NOT NULL,
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- analytics.dim_medicamento
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.dim_medicamento (
    medicamento_key SERIAL PRIMARY KEY,
    medicamento_id SMALLINT UNIQUE NOT NULL,
    nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    fabricante VARCHAR(100) NOT NULL,
    principio_ativo VARCHAR(150) NOT NULL,
    preco_unitario NUMERIC(10,2) NOT NULL,
    validade_dias_padrao INTEGER NOT NULL,
    armazenamento_refrigerado BOOLEAN NOT NULL,
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- analytics.dim_cliente
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.dim_cliente (
    cliente_key SERIAL PRIMARY KEY,
    cliente_id INTEGER UNIQUE NOT NULL,
    nome VARCHAR(150) NOT NULL,
    tipo_cliente VARCHAR(30) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL,
    sala_key INTEGER NOT NULL REFERENCES analytics.dim_sala(sala_key),
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- analytics.fact_estoque_semanal (grão: sala x medicamento x semana)
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.fact_estoque_semanal (
    fact_id BIGSERIAL PRIMARY KEY,
    tempo_key INTEGER NOT NULL REFERENCES analytics.dim_tempo(tempo_key),
    sala_key INTEGER NOT NULL REFERENCES analytics.dim_sala(sala_key),
    medicamento_key INTEGER NOT NULL REFERENCES analytics.dim_medicamento(medicamento_key),
    saldo_inicial INTEGER NOT NULL,
    entradas INTEGER NOT NULL,
    saidas INTEGER NOT NULL,
    saldo_final INTEGER NOT NULL,
    ruptura_estoque BOOLEAN NOT NULL,
    valor_estoque_final NUMERIC(12,2),
    dias_cobertura_estimados NUMERIC(8,2),
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (tempo_key, sala_key, medicamento_key)
);

CREATE INDEX idx_fact_sala ON analytics.fact_estoque_semanal(sala_key);
CREATE INDEX idx_fact_medicamento ON analytics.fact_estoque_semanal(medicamento_key);
CREATE INDEX idx_fact_tempo ON analytics.fact_estoque_semanal(tempo_key);
