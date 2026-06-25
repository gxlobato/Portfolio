"""
================================================================================
STOCK FORECAST PIPELINE - ENGLISH VERSION
================================================================================
Author: Forecasting System
Date: 2026
Description: Complete pipeline for medication stock forecasting
             with PostgreSQL storage and recommendation generation.
================================================================================
"""

# ============================================================================
# 1. IMPORTS
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
print("🚀 STARTING STOCK FORECAST PIPELINE")
print("=" * 70)

# ============================================================================
# 2. CONFIGURATION
# ============================================================================

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')  # Valor padrão se não existir
}

# Model configuration
CONFIG = {
    'forecast_weeks': 12,             # How many weeks to forecast
    'history_weeks': 52,              # How many weeks to use for training
    'model': 'random_forest',         # random_forest or simple_average
    'save_csv': True,                 # Save CSV backups
    'save_charts': True,              # Save charts
    'results_folder': 'results'       # Folder to save files
}

# Create results folder
os.makedirs(CONFIG['results_folder'], exist_ok=True)

print("\n📋 CONFIGURATIONS LOADED:")
for key, value in CONFIG.items():
    print(f"   • {key}: {value}")

# ============================================================================
# 3. DATABASE FUNCTIONS
# ============================================================================

def connect_database():
    """Connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def load_data(conn):
    """Load data from database"""
    print("\n📊 LOADING DATA...")
    
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
        print(f"✅ Data loaded: {len(df)} records")
        print(f"   • Medications: {df['medicamento_id'].nunique()}")
        print(f"   • Period: {df['semana_referencia'].min()} to {df['semana_referencia'].max()}")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

# ============================================================================
# 4. ANALYSIS AND FORECAST FUNCTIONS
# ============================================================================

def analyze_medication(df, medication_id):
    """Analyze a specific medication"""
    
    # Filter data
    df_med = df[df['medicamento_id'] == medication_id]
    
    if len(df_med) < 4:
        return None
    
    # Weekly sales
    sales = df_med.groupby('semana_referencia')['saidas'].sum()
    
    # Statistics
    stats = {
        'medication_id': medication_id,
        'total': sales.sum(),
        'mean': sales.mean(),
        'std': sales.std(),
        'variation': (sales.std() / sales.mean() * 100) if sales.mean() > 0 else 0,
        'min': sales.min(),
        'max': sales.max(),
        'weeks': len(sales),
        'sales': sales
    }
    
    return stats

def forecast_sales(sales, weeks=12):
    """Make forecast using Random Forest"""
    
    if len(sales) < 10:
        # Insufficient data - use simple average
        mean = sales.mean()
        return [mean] * weeks
    
    # Prepare data for model
    data = pd.DataFrame({'sales': sales})
    
    # Create lags
    for lag in range(1, 5):
        data[f'lag_{lag}'] = sales.shift(lag)
    
    data = data.dropna()
    
    if len(data) < 4:
        mean = sales.mean()
        return [mean] * weeks
    
    # Train model
    X = data.drop('sales', axis=1)
    y = data['sales']
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # Make forecasts
    forecasts = []
    last_data = data.iloc[-1:].copy()
    
    for _ in range(weeks):
        pred = model.predict(last_data)[0]
        forecasts.append(max(0, pred))
        
        # Update data
        new_data = last_data.copy()
        for lag in range(4, 1, -1):
            new_data[f'lag_{lag}'] = new_data[f'lag_{lag-1}'].values
        new_data['lag_1'] = pred
        last_data = new_data
    
    return forecasts

def calculate_recommendation(med_stats, forecasts, current_stock=None):
    """Calculate purchase recommendation"""
    
    weekly_avg = med_stats['mean']
    
    # Current stock (use last value or estimate)
    if current_stock is None:
        current_stock = weekly_avg * 4  # 4 weeks of stock
    
    # Total forecast for 4 weeks
    total_forecast_4w = sum(forecasts[:4]) if len(forecasts) >= 4 else sum(forecasts)
    
    # Weeks of stock
    stock_weeks = current_stock / weekly_avg if weekly_avg > 0 else 0
    
    # Urgency level
    if stock_weeks < 2:
        level = 'CRITICAL'
        priority = 1
        obs = f'Stock for {stock_weeks:.1f} weeks. Buy URGENTLY!'
    elif stock_weeks < 3:
        level = 'HIGH'
        priority = 2
        obs = f'Stock for {stock_weeks:.1f} weeks. Buy soon.'
    elif stock_weeks < 5:
        level = 'MEDIUM'
        priority = 3
        obs = f'Comfortable stock for {stock_weeks:.1f} weeks.'
    else:
        level = 'LOW'
        priority = 4
        obs = f'Abundant stock for {stock_weeks:.1f} weeks.'
    
    # Recommended quantity
    if stock_weeks < 4:
        quantity = max(0, total_forecast_4w * 1.5 - current_stock)
    else:
        quantity = 0
    
    return {
        'medication_id': med_stats['medication_id'],
        'recommendation_date': datetime.now().date(),
        'current_stock': round(current_stock, 2),
        'weekly_avg_sales': round(weekly_avg, 2),
        'stock_weeks': round(stock_weeks, 2),
        'recommended_quantity': round(quantity, 2),
        'urgency_level': level,
        'priority': priority,
        'observation': obs
    }

# ============================================================================
# 5. SAVE FUNCTIONS
# ============================================================================

def save_forecasts_postgres(conn, forecasts_df):
    """Save forecasts to PostgreSQL"""
    print("\n💾 SAVING FORECASTS TO POSTGRES...")
    
    cursor = conn.cursor()
    inserted = 0
    
    for _, row in forecasts_df.iterrows():
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
            inserted += 1
        except Exception as e:
            print(f"   ⚠️ Error inserting forecast {row['medicamento_id']}: {e}")
    
    conn.commit()
    print(f"✅ {inserted} forecasts saved")

def save_recommendations_postgres(conn, recommendations_df):
    """Save recommendations to PostgreSQL"""
    print("\n💾 SAVING RECOMMENDATIONS TO POSTGRES...")
    
    cursor = conn.cursor()
    inserted = 0
    
    for _, row in recommendations_df.iterrows():
        try:
            # Ensure we have medication_id column
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
            inserted += 1
        except Exception as e:
            print(f"   ⚠️ Error inserting recommendation {row.get('medicamento_id', 'N/A')}: {e}")
    
    conn.commit()
    print(f"✅ {inserted} recommendations saved")

def save_csv(df, name, folder='results'):
    """Save DataFrame to CSV"""
    path = os.path.join(folder, f"{name}.csv")
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"✅ {path} saved")

def save_chart(sales, forecasts, medication_id, folder='results'):
    """Save forecast chart"""
    plt.figure(figsize=(12, 5))
    
    # History
    plt.plot(sales.index, sales, 'bo-', label='History', linewidth=2)
    
    # Forecasts
    future_dates = [sales.index[-1] + timedelta(weeks=i+1) for i in range(len(forecasts))]
    plt.plot(future_dates, forecasts, 'r*-', label='Forecast', linewidth=2)
    
    plt.title(f'💊 Forecast - Medication {medication_id}')
    plt.xlabel('Date')
    plt.ylabel('Quantity')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axvline(x=sales.index[-1], color='gray', linestyle='--', alpha=0.5)
    
    path = os.path.join(folder, f'medication_{medication_id}.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()

# ============================================================================
# 6. MAIN FUNCTION - RUN THE PIPELINE
# ============================================================================

def run_pipeline():
    """Execute the complete pipeline"""
    
    print("\n" + "=" * 70)
    print("🚀 RUNNING PIPELINE")
    print("=" * 70)
    
    # 1. Connect to database
    conn = connect_database()
    if conn is None:
        print("❌ Connection failed. Pipeline interrupted.")
        return
    
    # 2. Load data
    df = load_data(conn)
    if df is None:
        conn.close()
        return
    
    # 3. Analyze each medication
    print("\n📊 ANALYZING MEDICATIONS...")
    
    medications = df['medicamento_id'].unique()
    print(f"Total medications: {len(medications)}")
    
    results = {}
    all_forecasts = []
    all_recommendations = []
    
    for i, med in enumerate(medications):
        if (i + 1) % 10 == 0:
            print(f"   • Processing {i+1}/{len(medications)}...")
        
        # Analyze
        stats = analyze_medication(df, med)
        if stats is None:
            continue
        
        # Forecast
        forecasts = forecast_sales(stats['sales'], CONFIG['forecast_weeks'])
        
        # Save results
        results[med] = {
            'stats': stats,
            'forecasts': forecasts
        }
        
        # Prepare data for saving
        last_date = stats['sales'].index[-1]
        for week, pred in enumerate(forecasts, 1):
            pred_date = last_date + timedelta(weeks=week)
            error_estimate = stats['std'] * 0.5
            all_forecasts.append({
                'medicamento_id': med,
                'semana_numero': week,
                'data_previsao': pred_date,
                'previsao_saidas': round(pred, 2),
                'limite_inferior': round(max(0, pred - error_estimate), 2),
                'limite_superior': round(pred + error_estimate, 2)
            })
        
        # Calculate recommendation
        rec = calculate_recommendation(stats, forecasts)
        all_recommendations.append(rec)
        
        # Save chart (optional)
        if CONFIG['save_charts']:
            save_chart(stats['sales'], forecasts, med, CONFIG['results_folder'])
    
    print(f"✅ Analysis completed: {len(results)} medications")
    
    # 4. Create DataFrames
    df_forecasts = pd.DataFrame(all_forecasts)
    df_recommendations = pd.DataFrame(all_recommendations)
    
    print(f"\n📊 Summary:")
    print(f"   • Forecasts: {len(df_forecasts)} records")
    print(f"   • Recommendations: {len(df_recommendations)} records")
    
    # 5. Save to PostgreSQL
    save_forecasts_postgres(conn, df_forecasts)
    save_recommendations_postgres(conn, df_recommendations)
    
    # 6. Save CSV (backup)
    if CONFIG['save_csv']:
        print("\n💾 SAVING CSV BACKUPS...")
        save_csv(df_forecasts, 'forecasts_medications', CONFIG['results_folder'])
        save_csv(df_recommendations, 'stock_recommendations', CONFIG['results_folder'])
    
    # 7. Close connection
    conn.close()
    print("\n🔒 Connection closed")
    
    # 8. Final report
    print("\n" + "=" * 70)
    print("📊 FINAL REPORT")
    print("=" * 70)
    
    # Summary of recommendations
    if len(df_recommendations) > 0:
        urgency_counts = df_recommendations['nivel_urgencia'].value_counts()
        print("\n📋 URGENCY DISTRIBUTION:")
        for level, count in urgency_counts.items():
            print(f"   • {level}: {count} medications")
        
        # Critical items
        critical = df_recommendations[df_recommendations['nivel_urgencia'].isin(['CRITICAL', 'HIGH'])]
        if len(critical) > 0:
            print(f"\n⚠️ {len(critical)} MEDICATIONS NEED ATTENTION:")
            for _, row in critical.head(5).iterrows():
                print(f"   • Medication {int(row['medicamento_id'])}: {row['semanas_estoque']:.1f} weeks of stock")
    
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    return df_forecasts, df_recommendations

# ============================================================================
# 7. EXECUTE
# ============================================================================

if __name__ == "__main__":
    forecasts, recommendations = run_pipeline()