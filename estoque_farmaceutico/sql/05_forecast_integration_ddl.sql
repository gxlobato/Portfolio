-- ============================================================================
-- ESTOQUE FARMACÊUTICO — INTEGRAÇÃO COM SCHEMA FORECAST
-- Cria fatos no schema analytics que reutilizam as dimensões conformadas
-- (dim_tempo, dim_medicamento) para conectar histórico realizado com
-- previsões geradas externamente (schema forecast).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Extensão de dim_tempo com as semanas futuras presentes nas previsões
-- (forecast.previsoes_medicamentos.data_previsao)
-- ----------------------------------------------------------------------------
INSERT INTO analytics.dim_tempo (semana_referencia, ano, trimestre, mes, mes_nome, semana_numero, dia_inicio_semana, dia_fim_semana)
SELECT DISTINCT
    data_previsao,
    EXTRACT(YEAR FROM data_previsao)::smallint,
    EXTRACT(QUARTER FROM data_previsao)::smallint,
    EXTRACT(MONTH FROM data_previsao)::smallint,
    to_char(data_previsao, 'TMMonth'),
    EXTRACT(WEEK FROM data_previsao)::smallint,
    data_previsao,
    data_previsao + 6
FROM forecast.previsoes_medicamentos
ON CONFLICT (semana_referencia) DO UPDATE SET
    ano = EXCLUDED.ano,
    trimestre = EXCLUDED.trimestre,
    mes = EXCLUDED.mes,
    mes_nome = EXCLUDED.mes_nome,
    semana_numero = EXCLUDED.semana_numero,
    dia_inicio_semana = EXCLUDED.dia_inicio_semana,
    dia_fim_semana = EXCLUDED.dia_fim_semana,
    ChangedTM = now()
WHERE (analytics.dim_tempo.ano, analytics.dim_tempo.trimestre, analytics.dim_tempo.mes, analytics.dim_tempo.mes_nome, analytics.dim_tempo.semana_numero, analytics.dim_tempo.dia_inicio_semana, analytics.dim_tempo.dia_fim_semana)
      IS DISTINCT FROM (EXCLUDED.ano, EXCLUDED.trimestre, EXCLUDED.mes, EXCLUDED.mes_nome, EXCLUDED.semana_numero, EXCLUDED.dia_inicio_semana, EXCLUDED.dia_fim_semana);

-- ----------------------------------------------------------------------------
-- analytics.fact_previsao_medicamento (grão: medicamento x semana futura)
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.fact_previsao_medicamento (
    fact_id BIGSERIAL PRIMARY KEY,
    tempo_key INTEGER NOT NULL REFERENCES analytics.dim_tempo(tempo_key),
    medicamento_key INTEGER NOT NULL REFERENCES analytics.dim_medicamento(medicamento_key),
    previsao_saidas NUMERIC(12,2),
    limite_inferior NUMERIC(12,2),
    limite_superior NUMERIC(12,2),
    data_criacao_modelo TIMESTAMP,
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (tempo_key, medicamento_key)
);

CREATE INDEX idx_fact_previsao_medicamento ON analytics.fact_previsao_medicamento(medicamento_key);

-- ----------------------------------------------------------------------------
-- analytics.fact_recomendacao_estoque (grão: medicamento x data do snapshot)
-- ----------------------------------------------------------------------------
CREATE TABLE analytics.fact_recomendacao_estoque (
    fact_id BIGSERIAL PRIMARY KEY,
    medicamento_key INTEGER NOT NULL REFERENCES analytics.dim_medicamento(medicamento_key),
    data_recomendacao DATE NOT NULL,
    estoque_atual NUMERIC(12,2),
    venda_media_semanal NUMERIC(12,2),
    semanas_estoque NUMERIC(8,2),
    quantidade_recomendada NUMERIC(12,2),
    nivel_urgencia VARCHAR(20),
    prioridade INTEGER,
    observacao TEXT,
    data_criacao_modelo TIMESTAMP,
    CreateDt TIMESTAMP NOT NULL DEFAULT now(),
    ChangedTM TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (medicamento_key, data_recomendacao)
);
