import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from utils.ui import aplicar_estilo_sidebar

aplicar_estilo_sidebar()

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

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("📅 Início",
                                value=hoje - timedelta(days=2),
                                min_value=datetime(2000, 1, 1),
                                max_value=hoje)
with col2:
    data_fim = st.date_input("📅 Fim",
                             value=hoje,
                             min_value=datetime(2000, 1, 1),
                             max_value=hoje)

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
                                    SELECT DISTINCT descricao_sensor, nome, data_registro, ultima_leitura, plataforma
                                    FROM sensores_atrasados 
                                    WHERE data_registro = ? and ultima_leitura < ?
                                """, conn, params=parametros)

nomes = df_tags['nome'].tolist()
plataformas = df_tags['plataforma'].tolist()

# Montar tabela
tabela = []
for i, tag in enumerate(df_tags['descricao_sensor']):
    linha = {"Tag": tag, "Nome": nomes[i], "Plataforma": plataformas[i]}

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
            linha[data] = "OFF"
    else:
        # Converter para datetime para comparar
        ultima_leitura_dt = datetime.strptime(ultima_leitura, "%Y-%m-%d")

        for data in datas:
            data_dt = datetime.strptime(data, "%Y-%m-%d")

            if data_dt <= ultima_leitura_dt:
                linha[data] = "ON"
            else:
                linha[data] = "OFF"

    tabela.append(linha)


def colorir_celulas(valor):
    if valor == "ON":
        return "color: green; font-weight: bold; text-align: center; vertical-align: middle;"
    elif valor == "OFF":
        return "color: red; font-weight: bold; text-align: center; vertical-align: middle;"
    return "text-align: center; vertical-align: middle;"


# Criar DataFrame final
df_tabela = pd.DataFrame(tabela)
config = {
    "Tag": st.column_config.Column(
        "Tag",
        pinned=True
    )}

tags_filtradas = st.sidebar.multiselect("Filtrar por Tag:", df_tabela["Tag"].unique())
if tags_filtradas:
    df_tabela = df_tabela[df_tabela["Tag"].isin(tags_filtradas)]

st.title("📊 Histórico de Tags")
df_styled = df_tabela.style.applymap(colorir_celulas, subset=datas)

aba1, aba2 = st.tabs(["📋 Tabela", "📈 Gráfico"])

with aba1:
    st.dataframe(df_styled, use_container_width=True, hide_index=True)

with aba2:
    st.line_chart(df_tabela[datas].apply(lambda col: (col == "OFF").sum()))

conn.close()
