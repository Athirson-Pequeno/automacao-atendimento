import os
import pandas as pd
import sqlite3


# Caminho absoluto até a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

def salvarTabela(arquivo):

    # Pastas
    pasta_relatorios = os.path.join(RELATORIOS_DIR)
    pasta_banco = os.path.join(DATABASE_DIR)

    # Garantir que as pastas existam
    os.makedirs(pasta_banco, exist_ok=True)
    os.makedirs(pasta_relatorios, exist_ok=True)

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
        "Plataforma": "plataforma"
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
        UNIQUE(data_registro, nome, descricao_sensor)
    )
    """)
    conn.commit()

    # --- Inserir dados novos evitando duplicados ---
    for _, row in df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO sensores_atrasados (
                data_registro, nome, descricao_sensor, email, ultima_leitura, plataforma
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row["data_registro"],
                row["nome"],
                row["descricao_sensor"],
                row["email"],
                row.get("ultima_leitura", None),
                row.get("plataforma", "")
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
    nome_relatorio = os.path.join(pasta_relatorios, os.path.basename(f"historico_{ano}_{mes}.xlsx"))
    df_mensal.to_excel(nome_relatorio, index=False)

    conn.close()