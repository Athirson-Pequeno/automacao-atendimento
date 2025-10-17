import os
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

DB_PATH = os.path.join(DATABASE_DIR, "sensores_atrasados.db")

# Conectar no banco
conn = sqlite3.connect(DB_PATH)

st.set_page_config(page_title="Histórico de Medidores", layout="wide")

# --- Sidebar: seleção de período ---
hoje = datetime.today()

data_inicio = st.sidebar.date_input(
    "Data início:",
    value=hoje - timedelta(days=2),
    min_value=datetime(2000, 1, 1),
    max_value=hoje
)

data_fim = st.sidebar.date_input(
    "Data fim:",
    value=hoje,
    min_value=datetime(2000, 1, 1),
    max_value=hoje
)

# Garantir que data_inicio <= data_fim
if data_inicio > data_fim:
    st.error("Data de início não pode ser maior que data de fim!")
    st.stop()

# Criar lista de datas para as colunas
delta = (data_fim - data_inicio).days + 1
datas = [(data_inicio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta)]

parametros = [datetime.today().strftime("%Y-%m-%d"), (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")]

# Buscar lista de tags
df_tags = pd.read_sql_query("""
                                    SELECT DISTINCT descricao_sensor, nome, data_registro, ultima_leitura
                                    FROM sensores_atrasados 
                                    WHERE data_registro = ? and ultima_leitura < ?
                                """, conn, params=parametros)

nomes = df_tags['nome'].tolist()

# Montar tabela
tabela = []
for i, tag in enumerate(df_tags['descricao_sensor']):
    linha = {"Tag": tag}

    # Buscar a última leitura dessa tag no banco
    query_ultima = """
        SELECT MAX(ultima_leitura) AS ultima_leitura
        FROM sensores_atrasados
        WHERE descricao_sensor = ?
    """

    df_ultima = pd.read_sql_query(query_ultima, conn, params=[tag])
    ultima_leitura = df_ultima.iloc[0]['ultima_leitura']

    if pd.isna(ultima_leitura):
        # Nunca teve leitura
        for data in datas:
            linha[data] = "❌"
    else:
        # Converter para datetime para comparar
        ultima_leitura_dt = datetime.strptime(ultima_leitura, "%Y-%m-%d")

        for data in datas:
            data_dt = datetime.strptime(data, "%Y-%m-%d")

            if data_dt <= ultima_leitura_dt:
                linha[data] = "✅"
            else:
                linha[data] = "❌"

    tabela.append(linha)

# Criar DataFrame final
df_tabela = pd.DataFrame(tabela)
config = {
    "Tag": st.column_config.Column(
        "Tag",
        pinned=True
    )}

# Mostrar no Streamlit
st.title("📊 Histórico de Tags")
st.data_editor(
    df_tabela,
    use_container_width=True,
    column_config=config,
    hide_index=True,
    disabled=False,
    key="historico_tags"
)

conn.close()
