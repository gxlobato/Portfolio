-- ============================================================================
-- ESTOQUE FARMACÊUTICO — CARGA DO MODELO DIMENSIONAL (ANALYTICS)
-- Padrão: upsert idempotente via ON CONFLICT ... DO UPDATE ... WHERE IS DISTINCT FROM
-- Executar após 03_analytics_schema_ddl.sql, com a camada raw já populada.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- dim_sala
-- ----------------------------------------------------------------------------
INSERT INTO analytics.dim_sala (sala_id, nome, regiao, cidade, uf, capacidade_m3)
SELECT sala_id, nome, regiao, cidade, uf, capacidade_m3
FROM raw.salas_estoque
ON CONFLICT (sala_id) DO UPDATE SET
    nome = EXCLUDED.nome,
    regiao = EXCLUDED.regiao,
    cidade = EXCLUDED.cidade,
    uf = EXCLUDED.uf,
    capacidade_m3 = EXCLUDED.capacidade_m3,
    ChangedTM = now()
WHERE (analytics.dim_sala.nome, analytics.dim_sala.regiao, analytics.dim_sala.cidade, analytics.dim_sala.uf, analytics.dim_sala.capacidade_m3)
      IS DISTINCT FROM (EXCLUDED.nome, EXCLUDED.regiao, EXCLUDED.cidade, EXCLUDED.uf, EXCLUDED.capacidade_m3);

-- ----------------------------------------------------------------------------
-- dim_medicamento
-- ----------------------------------------------------------------------------
INSERT INTO analytics.dim_medicamento (medicamento_id, nome, categoria, fabricante, principio_ativo, preco_unitario, validade_dias_padrao, armazenamento_refrigerado)
SELECT medicamento_id, nome, categoria, fabricante, principio_ativo, preco_unitario, validade_dias_padrao, armazenamento_refrigerado
FROM raw.medicamentos
ON CONFLICT (medicamento_id) DO UPDATE SET
    nome = EXCLUDED.nome,
    categoria = EXCLUDED.categoria,
    fabricante = EXCLUDED.fabricante,
    principio_ativo = EXCLUDED.principio_ativo,
    preco_unitario = EXCLUDED.preco_unitario,
    validade_dias_padrao = EXCLUDED.validade_dias_padrao,
    armazenamento_refrigerado = EXCLUDED.armazenamento_refrigerado,
    ChangedTM = now()
WHERE (analytics.dim_medicamento.nome, analytics.dim_medicamento.categoria, analytics.dim_medicamento.fabricante, analytics.dim_medicamento.principio_ativo, analytics.dim_medicamento.preco_unitario, analytics.dim_medicamento.validade_dias_padrao, analytics.dim_medicamento.armazenamento_refrigerado)
      IS DISTINCT FROM (EXCLUDED.nome, EXCLUDED.categoria, EXCLUDED.fabricante, EXCLUDED.principio_ativo, EXCLUDED.preco_unitario, EXCLUDED.validade_dias_padrao, EXCLUDED.armazenamento_refrigerado);

-- ----------------------------------------------------------------------------
-- dim_cliente (depende de dim_sala já carregada)
-- ----------------------------------------------------------------------------
INSERT INTO analytics.dim_cliente (cliente_id, nome, tipo_cliente, cidade, uf, sala_key)
SELECT c.cliente_id, c.nome, c.tipo_cliente, c.cidade, c.uf, ds.sala_key
FROM raw.clientes c
JOIN analytics.dim_sala ds ON ds.sala_id = c.sala_id_principal
ON CONFLICT (cliente_id) DO UPDATE SET
    nome = EXCLUDED.nome,
    tipo_cliente = EXCLUDED.tipo_cliente,
    cidade = EXCLUDED.cidade,
    uf = EXCLUDED.uf,
    sala_key = EXCLUDED.sala_key,
    ChangedTM = now()
WHERE (analytics.dim_cliente.nome, analytics.dim_cliente.tipo_cliente, analytics.dim_cliente.cidade, analytics.dim_cliente.uf, analytics.dim_cliente.sala_key)
      IS DISTINCT FROM (EXCLUDED.nome, EXCLUDED.tipo_cliente, EXCLUDED.cidade, EXCLUDED.uf, EXCLUDED.sala_key);

-- ----------------------------------------------------------------------------
-- dim_tempo (derivada das semanas existentes na movimentação)
-- ----------------------------------------------------------------------------
INSERT INTO analytics.dim_tempo (semana_referencia, ano, trimestre, mes, mes_nome, semana_numero, dia_inicio_semana, dia_fim_semana)
SELECT DISTINCT
    semana_referencia,
    EXTRACT(YEAR FROM semana_referencia)::smallint,
    EXTRACT(QUARTER FROM semana_referencia)::smallint,
    EXTRACT(MONTH FROM semana_referencia)::smallint,
    to_char(semana_referencia, 'TMMonth'),
    EXTRACT(WEEK FROM semana_referencia)::smallint,
    semana_referencia,
    semana_referencia + 6
FROM raw.estoque_movimentacao_semanal
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
-- fact_estoque_semanal (depende de todas as dimensões já carregadas)
-- Métricas derivadas: valor financeiro do estoque e dias de cobertura estimados
-- ----------------------------------------------------------------------------
INSERT INTO analytics.fact_estoque_semanal (tempo_key, sala_key, medicamento_key, saldo_inicial, entradas, saidas, saldo_final, ruptura_estoque, valor_estoque_final, dias_cobertura_estimados)
SELECT
    dt.tempo_key,
    ds.sala_key,
    dm.medicamento_key,
    e.saldo_inicial,
    e.entradas,
    e.saidas,
    e.saldo_final,
    e.ruptura_estoque,
    round((e.saldo_final * dm.preco_unitario)::numeric, 2),
    CASE WHEN e.saidas > 0 THEN round((e.saldo_final::numeric / (e.saidas / 7.0)), 2) ELSE NULL END
FROM raw.estoque_movimentacao_semanal e
JOIN analytics.dim_tempo dt ON dt.semana_referencia = e.semana_referencia
JOIN analytics.dim_sala ds ON ds.sala_id = e.sala_id
JOIN analytics.dim_medicamento dm ON dm.medicamento_id = e.medicamento_id
ON CONFLICT (tempo_key, sala_key, medicamento_key) DO UPDATE SET
    saldo_inicial = EXCLUDED.saldo_inicial,
    entradas = EXCLUDED.entradas,
    saidas = EXCLUDED.saidas,
    saldo_final = EXCLUDED.saldo_final,
    ruptura_estoque = EXCLUDED.ruptura_estoque,
    valor_estoque_final = EXCLUDED.valor_estoque_final,
    dias_cobertura_estimados = EXCLUDED.dias_cobertura_estimados,
    ChangedTM = now()
WHERE (analytics.fact_estoque_semanal.saldo_inicial, analytics.fact_estoque_semanal.entradas, analytics.fact_estoque_semanal.saidas, analytics.fact_estoque_semanal.saldo_final, analytics.fact_estoque_semanal.ruptura_estoque, analytics.fact_estoque_semanal.valor_estoque_final, analytics.fact_estoque_semanal.dias_cobertura_estimados)
      IS DISTINCT FROM (EXCLUDED.saldo_inicial, EXCLUDED.entradas, EXCLUDED.saidas, EXCLUDED.saldo_final, EXCLUDED.ruptura_estoque, EXCLUDED.valor_estoque_final, EXCLUDED.dias_cobertura_estimados);
