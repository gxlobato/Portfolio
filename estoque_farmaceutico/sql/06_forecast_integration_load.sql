-- ============================================================================
-- ESTOQUE FARMACÊUTICO — CARGA DAS FATOS DE PREVISÃO/RECOMENDAÇÃO
-- Executar após 05_forecast_integration_ddl.sql, com o schema forecast
-- já populado pelo pipeline de modelagem (Holt-Winters/Prophet/XGBoost etc.)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- fact_previsao_medicamento
-- O medicamento_key do schema forecast já é a mesma chave conformada de
-- analytics.dim_medicamento — não é necessário remapear.
-- ----------------------------------------------------------------------------
INSERT INTO analytics.fact_previsao_medicamento (tempo_key, medicamento_key, previsao_saidas, limite_inferior, limite_superior, data_criacao_modelo)
SELECT dt.tempo_key, p.medicamento_key, p.previsao_saidas, p.limite_inferior, p.limite_superior, p.data_criacao
FROM forecast.previsoes_medicamentos p
JOIN analytics.dim_tempo dt ON dt.semana_referencia = p.data_previsao
ON CONFLICT (tempo_key, medicamento_key) DO UPDATE SET
    previsao_saidas = EXCLUDED.previsao_saidas,
    limite_inferior = EXCLUDED.limite_inferior,
    limite_superior = EXCLUDED.limite_superior,
    data_criacao_modelo = EXCLUDED.data_criacao_modelo,
    ChangedTM = now()
WHERE (analytics.fact_previsao_medicamento.previsao_saidas, analytics.fact_previsao_medicamento.limite_inferior, analytics.fact_previsao_medicamento.limite_superior, analytics.fact_previsao_medicamento.data_criacao_modelo)
      IS DISTINCT FROM (EXCLUDED.previsao_saidas, EXCLUDED.limite_inferior, EXCLUDED.limite_superior, EXCLUDED.data_criacao_modelo);

-- ----------------------------------------------------------------------------
-- fact_recomendacao_estoque
-- ----------------------------------------------------------------------------
INSERT INTO analytics.fact_recomendacao_estoque (medicamento_key, data_recomendacao, estoque_atual, venda_media_semanal, semanas_estoque, quantidade_recomendada, nivel_urgencia, prioridade, observacao, data_criacao_modelo)
SELECT r.medicamento_key, r.data_recomendacao, r.estoque_atual, r.venda_media_semanal, r.semanas_estoque, r.quantidade_recomendada, r.nivel_urgencia, r.prioridade, r.observacao, r.data_criacao
FROM forecast.recomendacoes_estoque r
ON CONFLICT (medicamento_key, data_recomendacao) DO UPDATE SET
    estoque_atual = EXCLUDED.estoque_atual,
    venda_media_semanal = EXCLUDED.venda_media_semanal,
    semanas_estoque = EXCLUDED.semanas_estoque,
    quantidade_recomendada = EXCLUDED.quantidade_recomendada,
    nivel_urgencia = EXCLUDED.nivel_urgencia,
    prioridade = EXCLUDED.prioridade,
    observacao = EXCLUDED.observacao,
    data_criacao_modelo = EXCLUDED.data_criacao_modelo,
    ChangedTM = now()
WHERE (analytics.fact_recomendacao_estoque.estoque_atual, analytics.fact_recomendacao_estoque.venda_media_semanal, analytics.fact_recomendacao_estoque.semanas_estoque, analytics.fact_recomendacao_estoque.quantidade_recomendada, analytics.fact_recomendacao_estoque.nivel_urgencia, analytics.fact_recomendacao_estoque.prioridade, analytics.fact_recomendacao_estoque.observacao, analytics.fact_recomendacao_estoque.data_criacao_modelo)
      IS DISTINCT FROM (EXCLUDED.estoque_atual, EXCLUDED.venda_media_semanal, EXCLUDED.semanas_estoque, EXCLUDED.quantidade_recomendada, EXCLUDED.nivel_urgencia, EXCLUDED.prioridade, EXCLUDED.observacao, EXCLUDED.data_criacao_modelo);
