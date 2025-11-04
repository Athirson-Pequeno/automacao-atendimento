import os

import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Caminho absoluto até a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(TABELAS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)


def salvarTabela(arquivo):
    # Nome do banco dentro da pasta src/database
    df = pd.read_excel(arquivo)

    # Converter a coluna de data para o formato padrão SQLite
    df['DataAtual'] = pd.to_datetime(df['DataAtual'], dayfirst=True).dt.strftime('%Y-%m-%d')
    df['DataÚltimaLeitura'] = pd.to_datetime(df['DataÚltimaLeitura'], dayfirst=True).dt.strftime('%Y-%m-%d')

    df.rename(columns={
        "DataAtual": "data_registro",
        "Nome": "nome",
        "Email": "email",
        "DescriçãoSensor": "descricao_sensor",
        "DataÚltimaLeitura": "ultima_leitura",
        "Plataforma": "plataforma",
        "Dias off.": "dias_off",
        "TipoMedidor": "tipo_medidor"
    }, inplace=True)

    # --- Conexão com o PostgreSQL ---
    conn = psycopg2.connect(
        host="localhost",  # ou "postgres" se rodar dentro do Docker Compose
        port="5432",
        database="atendimento_cliente",
        user="admin",
        password="asp36412"
    )
    cursor = conn.cursor()

    # --- Criar tabela se não existir ---
    cursor.execute("""
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
        )
    """)

    conn.commit()

    # --- Inserir dados novos evitando duplicados ---
    for _, row in df.iterrows():
        cursor.execute("""
                INSERT INTO historico_sensores (
                    data_registro, nome, descricao_sensor, email, ultima_leitura, plataforma, tipo_medidor, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (data_registro, nome, descricao_sensor) DO NOTHING
            """, (
            row["data_registro"],
            row["nome"],
            row["descricao_sensor"],
            row["email"],
            row.get("ultima_leitura", None),
            row.get("plataforma", ""),
            row["tipo_medidor"],
            "OFF" if row["dias_off"] > 0 else "ON"
        ))

    conn.commit()

    # Gerar relatório
    ano = str(pd.Timestamp.today().year)
    mes = str(pd.Timestamp.today().month).zfill(2)

    engine = create_engine("postgresql+psycopg2://admin:asp36412@localhost:5432/atendimento_cliente")
    df_mensal = pd.read_sql_query("SELECT * FROM historico_sensores ORDER BY data_registro ASC", engine)

    nome_relatorio = os.path.join(RELATORIOS_DIR, f"historico_{ano}_{mes}.xlsx")
    df_mensal.to_excel(nome_relatorio, index=False)

    conn.close()
