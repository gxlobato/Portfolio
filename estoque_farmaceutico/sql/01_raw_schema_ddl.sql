-- ============================================================================
-- ESTOQUE FARMACÊUTICO — CAMADA RAW
-- Schema com os dados sintéticos brutos: salas de estoque, medicamentos,
-- clientes, lotes e movimentação semanal de estoque.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS raw;

-- ----------------------------------------------------------------------------
-- raw.salas_estoque — Centros de distribuição / salas de estoque
-- ----------------------------------------------------------------------------
CREATE TABLE raw.salas_estoque (
    sala_id SMALLINT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    regiao VARCHAR(20) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL,
    capacidade_m3 NUMERIC(10,2) NOT NULL,
    CreateDt TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- raw.medicamentos — Catálogo de medicamentos
-- ----------------------------------------------------------------------------
CREATE TABLE raw.medicamentos (
    medicamento_id SMALLINT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    fabricante VARCHAR(100) NOT NULL,
    principio_ativo VARCHAR(150) NOT NULL,
    preco_unitario NUMERIC(10,2) NOT NULL,
    validade_dias_padrao INTEGER NOT NULL,
    armazenamento_refrigerado BOOLEAN NOT NULL DEFAULT FALSE,
    CreateDt TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- raw.clientes — Farmácias, hospitais, clínicas e UPAs atendidos
-- ----------------------------------------------------------------------------
CREATE TABLE raw.clientes (
    cliente_id INTEGER PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    tipo_cliente VARCHAR(30) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL,
    sala_id_principal SMALLINT NOT NULL REFERENCES raw.salas_estoque(sala_id),
    CreateDt TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- raw.lotes — Lotes de medicamentos (fabricação/validade) por sala
-- ----------------------------------------------------------------------------
CREATE TABLE raw.lotes (
    lote_id INTEGER PRIMARY KEY,
    medicamento_id SMALLINT NOT NULL REFERENCES raw.medicamentos(medicamento_id),
    sala_id SMALLINT NOT NULL REFERENCES raw.salas_estoque(sala_id),
    data_fabricacao DATE NOT NULL,
    data_validade DATE NOT NULL,
    quantidade_inicial INTEGER NOT NULL,
    CreateDt TIMESTAMP NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- raw.estoque_movimentacao_semanal — Série semanal de estoque (grão:
-- sala x medicamento x semana)
-- ----------------------------------------------------------------------------
CREATE TABLE raw.estoque_movimentacao_semanal (
    id BIGINT PRIMARY KEY,
    sala_id SMALLINT NOT NULL REFERENCES raw.salas_estoque(sala_id),
    medicamento_id SMALLINT NOT NULL REFERENCES raw.medicamentos(medicamento_id),
    semana_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    semana_numero SMALLINT NOT NULL,
    saldo_inicial INTEGER NOT NULL,
    entradas INTEGER NOT NULL,
    saidas INTEGER NOT NULL,
    saldo_final INTEGER NOT NULL,
    ruptura_estoque BOOLEAN NOT NULL DEFAULT FALSE,
    CreateDt TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_mov_sala_med ON raw.estoque_movimentacao_semanal(sala_id, medicamento_id);
CREATE INDEX idx_mov_semana ON raw.estoque_movimentacao_semanal(semana_referencia);
