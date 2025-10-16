import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

DB_PATH = os.path.join(DATABASE_DIR, "sensores_atrasados.db")

# Conectar no banco
conn = sqlite3.connect(DB_PATH)

st.set_page_config(page_title="Histórico medidores de Medidores", layout="wide")

# --- Sidebar: seleção de período ---
hoje = datetime.today()

data_inicio = st.sidebar.date_input(
    "Data início:",
    value=hoje - timedelta(days=30),
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

# Buscar lista de tags
df_tags = pd.read_sql_query("SELECT DISTINCT descricao_sensor FROM sensores_atrasados", conn)
tags = df_tags['descricao_sensor'].tolist()

# Montar tabela
tabela = []
for tag in tags:
    linha = {"Tag": tag}
    for data in datas:
        # Última leitura antes ou no dia
        query = f"""
        SELECT MAX(ultima_leitura) as ultima_leitura
        FROM sensores_atrasados
        WHERE descricao_sensor = ?
        AND ultima_leitura <= ?
        """
        df = pd.read_sql_query(query, conn, params=(tag, data))
        ultima = df.iloc[0]['ultima_leitura']
        if pd.isna(ultima):
            linha[data] = "❌"  # sem leitura → offline
        else:
            linha[data] = "✅" if ultima >= data else "❌"
    tabela.append(linha)

# Criar DataFrame final
df_tabela = pd.DataFrame(tabela)

config = {
    "Tag": st.column_config.Column(
        "Tag",
        help="Esta coluna será fixada à esquerda",
        pinned=True
)}

# Mostrar no Streamlit
st.title("📊 Histórico de Tags")
st.dataframe(df_tabela, use_container_width=True, column_config=config)

conn.close()