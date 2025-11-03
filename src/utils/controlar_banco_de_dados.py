import os
import sqlite3

import pandas as pd

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
    banco_sqlite = os.path.join(DATABASE_DIR, "sensores_atrasados.db")

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

    # --- Conectar SQLite ---
    conn = sqlite3.connect(banco_sqlite)
    cursor = conn.cursor()

    # --- Criar tabela se não existir ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensores_atrasados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        try:

            if row["dias_off"] > 0:
                status = "OFF"
            else:
                status = "ON"

            cursor.execute("""
            INSERT INTO sensores_atrasados (
                data_registro, nome, descricao_sensor, email, ultima_leitura, plataforma, tipo_medidor, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["data_registro"],
                row["nome"],
                row["descricao_sensor"],
                row["email"],
                row.get("ultima_leitura", None),
                row.get("plataforma", ""),
                row["tipo_medidor"],
                status
            ))
        except sqlite3.IntegrityError:
            # Ignora duplicados
            pass

    conn.commit()

    # --- Gerar relatório mensal (ex: outubro/2025) ---
    ano = "2025"
    mes = "10"
    query = f"""
    SELECT * FROM sensores_atrasados
    ORDER BY data_registro ASC
    """

    # Salvar planilha original na pasta relatorios
    df_mensal = pd.read_sql_query(query, conn)
    nome_relatorio = os.path.join(RELATORIOS_DIR, os.path.basename(f"historico_{ano}_{mes}.xlsx"))
    df_mensal.to_excel(nome_relatorio, index=False)

    conn.close()
