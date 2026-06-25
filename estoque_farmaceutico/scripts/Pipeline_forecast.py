"""
================================================================================
PIPELINE DE PREVISÃO DE ESTOQUE - VERSÃO PORTUGUÊS
================================================================================
Autor: Sistema de Previsão
Data: 2026
Descrição: Pipeline completo para previsão de estoque por medicamento
           com salvamento no PostgreSQL e geração de recomendações.
================================================================================
"""

# ============================================================================
# 1. IMPORTAÇÕES
# ============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import warnings
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')

print("=" * 70)
print("🚀 INICIANDO PIPELINE DE PREVISÃO DE ESTOQUE")
print("=" * 70)

# ============================================================================
# 2. CONFIGURAÇÃO
# ============================================================================

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')  # Valor padrão se não existir
}

# Configurações do modelo
CONFIG = {
    'semanas_previsao': 12,           # Quantas semanas prever
    'semanas_historico': 52,          # Quantas semanas usar para treino
    'modelo': 'random_forest',        # random_forest ou media_simples
    'salvar_csv': True,               # Salvar backup em CSV
    'salvar_graficos': True,          # Salvar gráficos
    'pasta_resultados': 'resultados'  # Pasta para salvar os arquivos
}

# Criar pasta de resultados
os.makedirs(CONFIG['pasta_resultados'], exist_ok=True)

print("\n📋 CONFIGURAÇÕES CARREGADAS:")
for key, value in CONFIG.items():
    print(f"   • {key}: {value}")

# ============================================================================
# 3. FUNÇÕES DE BANCO DE DADOS
# ============================================================================

def conectar_banco():
    """Conecta ao PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

def carregar_dados(conn):
    """Carrega os dados do banco"""
    print("\n📊 CARREGANDO DADOS...")
    
    query = """
        SELECT 
            medicamento_id,
            semana_referencia,
            saidas,
            entradas,
            saldo_inicial,
            saldo_final
        FROM raw.estoque_movimentacao_semanal
        WHERE ano >= 2021
        ORDER BY semana_referencia, medicamento_id
    """
    
    try:
        df = pd.read_sql(query, conn)
        print(f"✅ Dados carregados: {len(df)} registros")
        print(f"   • Remédios: {df['medicamento_id'].nunique()}")
        print(f"   • Período: {df['semana_referencia'].min()} a {df['semana_referencia'].max()}")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return None

# ============================================================================
# 4. FUNÇÕES DE ANÁLISE E PREVISÃO
# ============================================================================

def analisar_medicamento(df, medicamento_id):
    """Analisa um medicamento específico"""
    
    # Filtrar dados
    df_med = df[df['medicamento_id'] == medicamento_id]
    
    if len(df_med) < 4:
        return None
    
    # Vendas por semana
    vendas = df_med.groupby('semana_referencia')['saidas'].sum()
    
    # Estatísticas
    stats = {
        'medicamento_id': medicamento_id,
        'total': vendas.sum(),
        'media': vendas.mean(),
        'desvio': vendas.std(),
        'variacao': (vendas.std() / vendas.mean() * 100) if vendas.mean() > 0 else 0,
        'minimo': vendas.min(),
        'maximo': vendas.max(),
        'semanas': len(vendas),
        'vendas': vendas
    }
    
    return stats

def fazer_previsao(vendas, semanas=12):
    """Faz previsão simples usando Random Forest"""
    
    if len(vendas) < 10:
        # Dados insuficientes - usar média simples
        media = vendas.mean()
        return [media] * semanas
    
    # Preparar dados para o modelo
    dados = pd.DataFrame({'vendas': vendas})
    
    # Criar lags
    for lag in range(1, 5):
        dados[f'lag_{lag}'] = vendas.shift(lag)
    
    dados = dados.dropna()
    
    if len(dados) < 4:
        media = vendas.mean()
        return [media] * semanas
    
    # Treinar modelo
    X = dados.drop('vendas', axis=1)
    y = dados['vendas']
    
    modelo = RandomForestRegressor(n_estimators=50, random_state=42)
    modelo.fit(X, y)
    
    # Fazer previsões
    previsoes = []
    ultimos_dados = dados.iloc[-1:].copy()
    
    for _ in range(semanas):
        pred = modelo.predict(ultimos_dados)[0]
        previsoes.append(max(0, pred))
        
        # Atualizar dados
        novo_dado = ultimos_dados.copy()
        for lag in range(4, 1, -1):
            novo_dado[f'lag_{lag}'] = novo_dado[f'lag_{lag-1}'].values
        novo_dado['lag_1'] = pred
        ultimos_dados = novo_dado
    
    return previsoes

def calcular_recomendacao(med_stats, previsoes, estoque_atual=None):
    """Calcula recomendação de compra"""
    
    media_semanal = med_stats['media']
    
    # Estoque atual (usar último valor ou estimar)
    if estoque_atual is None:
        estoque_atual = media_semanal * 4  # 4 semanas de estoque
    
    # Total previsto para 4 semanas
    total_previsto_4s = sum(previsoes[:4]) if len(previsoes) >= 4 else sum(previsoes)
    
    # Semanas de estoque
    semanas_estoque = estoque_atual / media_semanal if media_semanal > 0 else 0
    
    # Nível de urgência
    if semanas_estoque < 2:
        nivel = 'CRÍTICO'
        prioridade = 1
        obs = f'Estoque para {semanas_estoque:.1f} semanas. Compre URGENTE!'
    elif semanas_estoque < 3:
        nivel = 'ALTO'
        prioridade = 2
        obs = f'Estoque para {semanas_estoque:.1f} semanas. Compre em breve.'
    elif semanas_estoque < 5:
        nivel = 'MÉDIO'
        prioridade = 3
        obs = f'Estoque confortável por {semanas_estoque:.1f} semanas.'
    else:
        nivel = 'BAIXO'
        prioridade = 4
        obs = f'Estoque abundante para {semanas_estoque:.1f} semanas.'
    
    # Quantidade recomendada
    if semanas_estoque < 4:
        quantidade = max(0, total_previsto_4s * 1.5 - estoque_atual)
    else:
        quantidade = 0
    
    return {
        'medicamento_id': med_stats['medicamento_id'],
        'data_recomendacao': datetime.now().date(),
        'estoque_atual': round(estoque_atual, 2),
        'venda_media_semanal': round(media_semanal, 2),
        'semanas_estoque': round(semanas_estoque, 2),
        'quantidade_recomendada': round(quantidade, 2),
        'nivel_urgencia': nivel,
        'prioridade': prioridade,
        'observacao': obs
    }

# ============================================================================
# 5. FUNÇÕES DE SALVAMENTO
# ============================================================================

def salvar_previsoes_postgres(conn, previsoes_df):
    """Salva previsões no PostgreSQL"""
    print("\n💾 SALVANDO PREVISÕES NO POSTGRES...")
    
    cursor = conn.cursor()
    inseridos = 0
    
    for _, row in previsoes_df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO forecast.previsoes_medicamentos 
                (medicamento_id, semana_numero, data_previsao, 
                 previsao_saidas, limite_inferior, limite_superior)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (medicamento_id, data_previsao) 
                DO UPDATE SET 
                    previsao_saidas = EXCLUDED.previsao_saidas,
                    limite_inferior = EXCLUDED.limite_inferior,
                    limite_superior = EXCLUDED.limite_superior,
                    data_criacao = CURRENT_TIMESTAMP
            """, (
                int(row['medicamento_id']),
                int(row['semana_numero']),
                row['data_previsao'],
                float(row['previsao_saidas']),
                float(row['limite_inferior']),
                float(row['limite_superior'])
            ))
            inseridos += 1
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir previsão {row['medicamento_id']}: {e}")
    
    conn.commit()
    print(f"✅ {inseridos} previsões salvas")

def salvar_recomendacoes_postgres(conn, recomendacoes_df):
    """Salva recomendações no PostgreSQL"""
    print("\n💾 SALVANDO RECOMENDAÇÕES NO POSTGRES...")
    
    cursor = conn.cursor()
    inseridos = 0
    
    for _, row in recomendacoes_df.iterrows():
        try:
            # Garantir que temos a coluna medicamento_id
            med_id = row.get('medicamento_id') or row.get('medicamento_key')
            
            cursor.execute("""
                INSERT INTO forecast.recomendacoes_estoque 
                (medicamento_id, data_recomendacao, estoque_atual, 
                 venda_media_semanal, semanas_estoque, quantidade_recomendada,
                 nivel_urgencia, prioridade, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (medicamento_id, data_recomendacao) 
                DO UPDATE SET 
                    estoque_atual = EXCLUDED.estoque_atual,
                    venda_media_semanal = EXCLUDED.venda_media_semanal,
                    semanas_estoque = EXCLUDED.semanas_estoque,
                    quantidade_recomendada = EXCLUDED.quantidade_recomendada,
                    nivel_urgencia = EXCLUDED.nivel_urgencia,
                    prioridade = EXCLUDED.prioridade,
                    observacao = EXCLUDED.observacao,
                    data_criacao = CURRENT_TIMESTAMP
            """, (
                int(med_id),
                row['data_recomendacao'],
                float(row['estoque_atual']),
                float(row['venda_media_semanal']),
                float(row['semanas_estoque']),
                float(row['quantidade_recomendada']),
                str(row['nivel_urgencia']),
                int(row['prioridade']),
                str(row['observacao'])
            ))
            inseridos += 1
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir recomendação {row.get('medicamento_id', 'N/A')}: {e}")
    
    conn.commit()
    print(f"✅ {inseridos} recomendações salvas")

def salvar_csv(df, nome, pasta='resultados'):
    """Salva DataFrame em CSV"""
    caminho = os.path.join(pasta, f"{nome}.csv")
    df.to_csv(caminho, index=False, encoding='utf-8-sig')
    print(f"✅ {caminho} salvo")

def salvar_grafico(vendas, previsoes, medicamento_id, pasta='resultados'):
    """Salva gráfico de previsão"""
    plt.figure(figsize=(12, 5))
    
    # Histórico
    plt.plot(vendas.index, vendas, 'bo-', label='Histórico', linewidth=2)
    
    # Previsões
    datas_futuras = [vendas.index[-1] + timedelta(weeks=i+1) for i in range(len(previsoes))]
    plt.plot(datas_futuras, previsoes, 'r*-', label='Previsão', linewidth=2)
    
    plt.title(f'💊 Previsão - Medicamento {medicamento_id}')
    plt.xlabel('Data')
    plt.ylabel('Quantidade')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axvline(x=vendas.index[-1], color='gray', linestyle='--', alpha=0.5)
    
    caminho = os.path.join(pasta, f'medicamento_{medicamento_id}.png')
    plt.savefig(caminho, dpi=150, bbox_inches='tight')
    plt.close()

# ============================================================================
# 6. FUNÇÃO PRINCIPAL - EXECUTA O PIPELINE
# ============================================================================

def executar_pipeline():
    """Executa o pipeline completo"""
    
    print("\n" + "=" * 70)
    print("🚀 EXECUTANDO PIPELINE")
    print("=" * 70)
    
    # 1. Conectar ao banco
    conn = conectar_banco()
    if conn is None:
        print("❌ Falha na conexão. Pipeline interrompido.")
        return
    
    # 2. Carregar dados
    df = carregar_dados(conn)
    if df is None:
        conn.close()
        return
    
    # 3. Analisar cada medicamento
    print("\n📊 ANALISANDO MEDICAMENTOS...")
    
    medicamentos = df['medicamento_id'].unique()
    print(f"Total de medicamentos: {len(medicamentos)}")
    
    resultados = {}
    previsoes_todas = []
    recomendacoes_todas = []
    
    for i, med in enumerate(medicamentos):
        if (i + 1) % 10 == 0:
            print(f"   • Processando {i+1}/{len(medicamentos)}...")
        
        # Analisar
        stats = analisar_medicamento(df, med)
        if stats is None:
            continue
        
        # Prever
        previsoes = fazer_previsao(stats['vendas'], CONFIG['semanas_previsao'])
        
        # Salvar resultados
        resultados[med] = {
            'stats': stats,
            'previsoes': previsoes
        }
        
        # Preparar dados para salvar
        ultima_data = stats['vendas'].index[-1]
        for semana, pred in enumerate(previsoes, 1):
            data_pred = ultima_data + timedelta(weeks=semana)
            erro_estimado = stats['desvio'] * 0.5
            previsoes_todas.append({
                'medicamento_id': med,
                'semana_numero': semana,
                'data_previsao': data_pred,
                'previsao_saidas': round(pred, 2),
                'limite_inferior': round(max(0, pred - erro_estimado), 2),
                'limite_superior': round(pred + erro_estimado, 2)
            })
        
        # Calcular recomendação
        rec = calcular_recomendacao(stats, previsoes)
        recomendacoes_todas.append(rec)
        
        # Salvar gráfico (opcional)
        if CONFIG['salvar_graficos']:
            salvar_grafico(stats['vendas'], previsoes, med, CONFIG['pasta_resultados'])
    
    print(f"✅ Análise concluída: {len(resultados)} medicamentos")
    
    # 4. Criar DataFrames
    df_previsoes = pd.DataFrame(previsoes_todas)
    df_recomendacoes = pd.DataFrame(recomendacoes_todas)
    
    print(f"\n📊 Resumo:")
    print(f"   • Previsões: {len(df_previsoes)} registros")
    print(f"   • Recomendações: {len(df_recomendacoes)} registros")
    
    # 5. Salvar no PostgreSQL
    salvar_previsoes_postgres(conn, df_previsoes)
    salvar_recomendacoes_postgres(conn, df_recomendacoes)
    
    # 6. Salvar CSV (backup)
    if CONFIG['salvar_csv']:
        print("\n💾 SALVANDO BACKUPS CSV...")
        salvar_csv(df_previsoes, 'previsoes_medicamentos', CONFIG['pasta_resultados'])
        salvar_csv(df_recomendacoes, 'recomendacoes_estoque', CONFIG['pasta_resultados'])
    
    # 7. Fechar conexão
    conn.close()
    print("\n🔒 Conexão fechada")
    
    # 8. Relatório final
    print("\n" + "=" * 70)
    print("📊 RELATÓRIO FINAL")
    print("=" * 70)
    
    # Resumo das recomendações
    if len(df_recomendacoes) > 0:
        urgencia_counts = df_recomendacoes['nivel_urgencia'].value_counts()
        print("\n📋 DISTRIBUIÇÃO POR URGÊNCIA:")
        for nivel, count in urgencia_counts.items():
            print(f"   • {nivel}: {count} medicamentos")
        
        # Críticos
        criticos = df_recomendacoes[df_recomendacoes['nivel_urgencia'].isin(['CRÍTICO', 'ALTO'])]
        if len(criticos) > 0:
            print(f"\n⚠️ {len(criticos)} MEDICAMENTOS PRECISAM DE ATENÇÃO:")
            for _, row in criticos.head(5).iterrows():
                print(f"   • Medicamento {int(row['medicamento_id'])}: {row['semanas_estoque']:.1f} semanas de estoque")
    
    print("\n" + "=" * 70)
    print("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    
    return df_previsoes, df_recomendacoes

# ============================================================================
# 7. EXECUTAR
# ============================================================================

if __name__ == "__main__":
    previsoes, recomendacoes = executar_pipeline()