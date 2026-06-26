"""
LOAD FORECAST DATA TO ANALYTICS SCHEMA
================================================================================
PURPOSE:
- Populate analytics.fact_estoque_forecast with XGBoost predictions
- Update dim_tempo with any new forecast dates
- Provide clean, denormalized data for dashboards and reporting

TECHNICAL DECISIONS:
- Full refresh (DROP & CREATE) for fact table: 
  Since forecasts are regenerated daily and incremental load is handled 
  in the raw layer, a full refresh ensures consistency without complex merge logic.
  
- Incremental UPSERT for dim_tempo:
  Uses ON CONFLICT DO NOTHING to add only new dates without duplicates.
  dim_tempo is a slowly changing dimension (SCD Type 0) - dates never change.
  
- Denormalized fact table:
  Joins forecasts with recommendations to create a single source of truth
  for dashboards, avoiding repeated joins in BI tools.
  
- Date dimension alignment:
  Ensures every forecast date has a corresponding dim_tempo record,
  maintaining referential integrity for star schema.
================================================================================
"""

import os
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

print("=" * 70)
print("LOAD FORECAST TO ANALYTICS SCHEMA")
print("=" * 70)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================
print("\nConnecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    engine = create_engine(DATABASE_URL)
    print("Connected!")
except Exception as e:
    print(f"Error connecting: {e}")
    exit(1)

# ============================================================================
# 1. LOAD FORECAST DATA
# ============================================================================
print("\nLoading forecast data from raw schema...")

query = """
    select 
        prev.id,
        prev.sala_key,
        prev.medicamento_key,
        prev.data_previsao,
        prev.previsao_saidas,
        prev.limite_inferior,
        prev.limite_superior,
        rec.recomendacao
    from forecast.previsoes_xgb prev
    join forecast.recomendacoes_estoque rec 
        on prev.sala_key = rec.sala_key 
        and prev.medicamento_key = rec.medicamento_key 
        and prev.data_previsao >= rec.data_calculo
    order by prev.sala_key, prev.medicamento_key, prev.data_previsao
"""

df_forecast = pd.read_sql(query, engine)
print(f"Forecast records loaded: {len(df_forecast)}")

if len(df_forecast) == 0:
    print("WARNING: No forecast data found. Exiting.")
    conn.close()
    exit(0)

# Display sample
print(f"Period: {df_forecast['data_previsao'].min()} to {df_forecast['data_previsao'].max()}")
print(f"Combinations: {df_forecast[['sala_key', 'medicamento_key']].nunique()}")

# ============================================================================
# 2. UPDATE DIM_TEMPO WITH NEW DATES
# ============================================================================
# dim_tempo serves as the date dimension for all analytics.
# It must include every date that appears in fact tables for referential integrity.
# Using ON CONFLICT DO NOTHING ensures we only add new dates.
print("\nUpdating dim_tempo with new forecast dates...")

# Extract unique forecast dates
forecast_dates = df_forecast['data_previsao'].unique()
print(f"Unique forecast dates to add: {len(forecast_dates)}")

# Check which dates already exist in dim_tempo
cursor.execute("""
    SELECT semana_referencia FROM analytics.dim_tempo
    WHERE semana_referencia = ANY(%s)
""", (list(forecast_dates),))
existing_dates = {row[0] for row in cursor.fetchall()}

# Filter only new dates
new_dates = [d for d in forecast_dates if d not in existing_dates]
print(f"New dates to insert: {len(new_dates)}")

if len(new_dates) > 0:
    # Insert new dates into dim_tempo
    inserted = 0
    for date in new_dates:
        try:
            # Calculate dimension attributes from the date
            ano = date.year
            trimestre = (date.month - 1) // 3 + 1
            mes = date.month
            mes_nome = date.strftime('%B')  # Full month name
            semana_numero = date.isocalendar()[1]  # ISO week number
            
            # Calculate week start and end (assuming Monday as start)
            dia_inicio_semana = date - pd.Timedelta(days=date.weekday())
            dia_fim_semana = dia_inicio_semana + pd.Timedelta(days=6)
            
            cursor.execute("""
                INSERT INTO analytics.dim_tempo 
                (semana_referencia, ano, trimestre, mes, mes_nome, 
                 semana_numero, dia_inicio_semana, dia_fim_semana)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (semana_referencia) DO NOTHING
            """, (
                date,
                ano,
                trimestre,
                mes,
                mes_nome,
                semana_numero,
                dia_inicio_semana,
                dia_fim_semana
            ))
            inserted += 1
            if inserted % 50 == 0:
                conn.commit()
                print(f"  {inserted} dates inserted...")
        except Exception as e:
            print(f"Error inserting date {date}: {e}")
    
    conn.commit()
    print(f"dim_tempo updated: {inserted} new dates inserted")
else:
    print("No new dates to insert")

# ============================================================================
# 3. CREATE ANALYTICS TABLE
# ============================================================================
# Full refresh: drop and recreate the table.
# This ensures consistency since incremental load is handled at the raw layer.
# The fact table is denormalized for dashboard performance.
print("\nCreating analytics fact table...")

# Drop existing table
cursor.execute("DROP TABLE IF EXISTS analytics.fact_estoque_forecast CASCADE")
print("Dropped existing fact_estoque_forecast")

# Create fact table with references to dim_tempo and dimensions
cursor.execute("""
    CREATE TABLE analytics.fact_estoque_forecast (
        id INTEGER NOT NULL,
        sala_key INTEGER NOT NULL,
        medicamento_key INTEGER NOT NULL,
        tempo_key INTEGER NOT NULL,
        data_previsao DATE NOT NULL,
        previsao_saidas NUMERIC(10, 2),
        limite_inferior NUMERIC(10, 2),
        limite_superior NUMERIC(10, 2),
        recomendacao TEXT,
        createdt TIMESTAMP DEFAULT NOW(),
        changedtm TIMESTAMP DEFAULT NOW(),
        CONSTRAINT fact_estoque_forecast_pkey PRIMARY KEY (id, tempo_key)
    )
""")

# Add foreign key constraints for star schema integrity
cursor.execute("""
    ALTER TABLE analytics.fact_estoque_forecast 
    ADD CONSTRAINT fk_tempo FOREIGN KEY (tempo_key) 
    REFERENCES analytics.dim_tempo(tempo_key)
""")

conn.commit()
print("Table analytics.fact_estoque_forecast created")
print("Foreign key constraint added")

# ============================================================================
# 4. LOAD DATA INTO FACT TABLE
# ============================================================================
# Join forecast data with dim_tempo to get tempo_key for each forecast date.
# Using a lookup approach is more efficient than row-by-row subqueries.
print("\nLoading data into fact table...")

# Create a tempo_key lookup dictionary for performance
cursor.execute("""
    SELECT semana_referencia, tempo_key 
    FROM analytics.dim_tempo
    WHERE semana_referencia = ANY(%s)
""", (list(forecast_dates),))
tempo_lookup = {row[0]: row[1] for row in cursor.fetchall()}

# Add tempo_key to DataFrame
df_forecast['tempo_key'] = df_forecast['data_previsao'].map(tempo_lookup)

# Check for any dates without tempo_key
missing_tempo = df_forecast[df_forecast['tempo_key'].isna()]
if len(missing_tempo) > 0:
    print(f"WARNING: {len(missing_tempo)} records missing tempo_key")
    print("Skipping records without tempo_key...")
    df_forecast = df_forecast.dropna(subset=['tempo_key'])

print(f"Records to insert: {len(df_forecast)}")

# Insert in batches for performance
batch_size = 1000
inserted = 0

for i in range(0, len(df_forecast), batch_size):
    batch = df_forecast.iloc[i:i+batch_size]
    
    # Prepare data for bulk insert
    data_list = []
    for _, row in batch.iterrows():
        data_list.append((
            int(row['id']),
            int(row['sala_key']),
            int(row['medicamento_key']),
            int(row['tempo_key']),
            row['data_previsao'],
            float(row['previsao_saidas']),
            float(row['limite_inferior']),
            float(row['limite_superior']),
            str(row['recomendacao'])
        ))
    
    cursor.executemany("""
        INSERT INTO analytics.fact_estoque_forecast 
        (id, sala_key, medicamento_key, tempo_key, data_previsao, 
         previsao_saidas, limite_inferior, limite_superior, recomendacao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data_list)
    
    inserted += len(data_list)
    if inserted % 5000 == 0:
        conn.commit()
        print(f"  {inserted} records inserted...")

conn.commit()
print(f"fact_estoque_forecast loaded: {inserted} records")

# ============================================================================
# 5. VERIFY LOAD
# ============================================================================
print("\nVerifying load...")

cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT sala_key) as total_salas,
        COUNT(DISTINCT medicamento_key) as total_medicamentos,
        COUNT(DISTINCT tempo_key) as total_semanas,
        MIN(data_previsao) as data_inicio,
        MAX(data_previsao) as data_fim,
        ROUND(AVG(previsao_saidas), 2) as media_previsao,
        ROUND(SUM(previsao_saidas), 2) as total_previsao
    FROM analytics.fact_estoque_forecast
""")

result = cursor.fetchone()
print("\nFACT TABLE STATISTICS:")
print(f"  Total records: {result[0]:,}")
print(f"  Total salas: {result[1]}")
print(f"  Total medications: {result[2]}")
print(f"  Total weeks: {result[3]}")
print(f"  Period: {result[4]} to {result[5]}")
print(f"  Average forecast: {result[6]}")
print(f"  Total forecast: {result[7]:,.2f}")

# ============================================================================
# 6. CREATE SUPPORTING INDEXES
# ============================================================================
# Indexes improve dashboard query performance
print("\nCreating indexes for performance...")

cursor.execute("""
    CREATE INDEX idx_fact_forecast_sala_medicamento 
    ON analytics.fact_estoque_forecast (sala_key, medicamento_key)
""")

cursor.execute("""
    CREATE INDEX idx_fact_forecast_data_previsao 
    ON analytics.fact_estoque_forecast (data_previsao)
""")

cursor.execute("""
    CREATE INDEX idx_fact_forecast_tempo_key 
    ON analytics.fact_estoque_forecast (tempo_key)
""")

conn.commit()
print("Indexes created:")
print("  - idx_fact_forecast_sala_medicamento")
print("  - idx_fact_forecast_data_previsao")
print("  - idx_fact_forecast_tempo_key")

# ============================================================================
# 7. FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("LOAD COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nDIM_TEMPO:")
print(f"  New dates inserted: {len(new_dates)}")

print("\nFACT_ESTOQUE_FORECAST:")
print(f"  Records loaded: {result[0]:,}")
print(f"  Salas: {result[1]}")
print(f"  Medications: {result[2]}")
print(f"  Weeks: {result[3]}")
print(f"  Period: {result[4]} to {result[5]}")

print("\n" + "=" * 70)
print("LOAD COMPLETED")
print("=" * 70)

# ============================================================================
# 8. CLEANUP
# ============================================================================
conn.close()
print("\nDatabase connection closed")