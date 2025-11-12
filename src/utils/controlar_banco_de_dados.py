import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Caminho absoluto até a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(TABELAS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


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
        "TipoMedidor": "tipo_medidor",
        "Manutencao": "manutencao"
    }, inplace=True)

    # --- Conexão com o PostgreSQL ---
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
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
            manutencao TEXT,
            UNIQUE(data_registro, nome, descricao_sensor)
        )
    """)

    conn.commit()

    # --- Inserir dados novos evitando duplicados ---
    for _, row in df.iterrows():
        cursor.execute("""
                INSERT INTO historico_sensores (
                    data_registro, nome, descricao_sensor, email, ultima_leitura, plataforma, tipo_medidor, status, manutencao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (data_registro, nome, descricao_sensor) DO UPDATE
                SET 
                ultima_leitura = EXCLUDED.ultima_leitura, 
                status = EXCLUDED.status, 
                manutencao = EXCLUDED.manutencao
            """, (
            row["data_registro"],
            row["nome"],
            row["descricao_sensor"],
            row["email"],
            row.get("ultima_leitura", None),
            row.get("plataforma", ""),
            row["tipo_medidor"],
            "OFF" if row["dias_off"] > 0 else "ON",
            row["manutencao"]
        ))

    conn.commit()

    # Gerar relatório
    ano = str(pd.Timestamp.today().year)
    mes = str(pd.Timestamp.today().month).zfill(2)

    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    df_mensal = pd.read_sql_query("SELECT * FROM historico_sensores ORDER BY data_registro ASC", engine)

    nome_relatorio = os.path.join(RELATORIOS_DIR, f"historico_{ano}_{mes}.xlsx")
    df_mensal.to_excel(nome_relatorio, index=False)

    conn.close()
