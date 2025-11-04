import os
import sqlite3
import psycopg2
import pandas as pd

# Caminhos locais
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
banco_sqlite = os.path.join(DATABASE_DIR, "sensores_atrasados.db")

# --- Conexão com o SQLite ---
conn_sqlite = sqlite3.connect(banco_sqlite)

# Ler os dados da tabela SQLite
df = pd.read_sql_query("SELECT * FROM sensores_atrasados", conn_sqlite)

print(f"Total de registros lidos do SQLite: {len(df)}")

# --- Conexão com o PostgreSQL ---
conn_postgres = psycopg2.connect(
    host="localhost",      # ou "postgres" se rodar dentro do Docker Compose
    port="5432",
    database="atendimento_cliente",
    user="admin",
    password="asp36412"
)
cursor_pg = conn_postgres.cursor()

# Criar tabela no PostgreSQL (se não existir)
cursor_pg.execute("""
CREATE TABLE IF NOT EXISTS historico_sensores (
    id SERIAL PRIMARY KEY,
    data_registro DATE NOT NULL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    descricao_sensor TEXT NOT NULL,
    ultima_leitura DATE,
    plataforma TEXT,
    status TEXT,
    tipo_medidor TEXT,
    UNIQUE(data_registro, nome, descricao_sensor)
);
""")
conn_postgres.commit()

# Inserir registros
for _, row in df.iterrows():
    try:
        cursor_pg.execute("""
            INSERT INTO historico_sensores (
                data_registro, nome, email, descricao_sensor,
                ultima_leitura, plataforma, status, tipo_medidor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data_registro, nome, descricao_sensor) DO NOTHING;
        """, (
            row["data_registro"],
            row["nome"],
            row["email"],
            row["descricao_sensor"],
            row["ultima_leitura"],
            row["plataforma"],
            row["status"],
            row["tipo_medidor"]
        ))
    except Exception as e:
        print(f"Erro ao inserir linha: {e}")

conn_postgres.commit()

print("✅ Migração concluída com sucesso!")

# Fechar conexões
conn_sqlite.close()
conn_postgres.close()
