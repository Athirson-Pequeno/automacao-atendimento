import os
import sqlite3
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from utils.ui import aplicar_estilo_sidebar

aplicar_estilo_sidebar()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

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

# --- Montar tabela ---
tabela = []

# Buscar todos os registros dentro do intervalo selecionado
query_dados = """
    SELECT descricao_sensor, nome, plataforma, tipo_medidor, data_registro, status
    FROM historico_sensores
    WHERE data_registro BETWEEN %(inicio)s AND %(fim)s
"""
parametros_periodo = {
    "inicio": data_inicio.strftime("%Y-%m-%d"),
    "fim": data_fim.strftime("%Y-%m-%d")
}

df_dados = pd.read_sql_query(query_dados, engine, params=parametros_periodo)

# Garantir que as datas estão ordenadas
df_dados['data_registro'] = pd.to_datetime(df_dados['data_registro'])
df_dados = df_dados.sort_values(['descricao_sensor', 'data_registro'])

# Obter listas de sensores únicos
sensores_unicos = df_dados[['descricao_sensor', 'nome', 'plataforma', 'tipo_medidor']].drop_duplicates()

# Montar cada linha
for _, sensor in sensores_unicos.iterrows():
    tag = sensor['descricao_sensor']
    nome = sensor['nome']
    plataforma = sensor['plataforma']
    tipo = sensor['tipo_medidor']

    linha = {
        "Tag": tag,
        "Nome": nome,
        "Plataforma": plataforma,
        "Tipo medidor": tipo
    }

    # Filtrar dados desse sensor
    df_sensor = df_dados[df_dados['descricao_sensor'] == tag]

    for data in datas:
        status_dia = df_sensor.loc[df_sensor['data_registro'] == data, 'status']
        linha[data] = status_dia.iloc[0] if not status_dia.empty else "—"

    tabela.append(linha)


def colorir_celulas(valor):
    if valor == "ON":
        return "color: green; font-weight: bold; text-align: center; vertical-align: middle;"
    elif valor == "OFF":
        return "color: red; font-weight: bold; text-align: center; vertical-align: middle;"
    return "text-align: center; vertical-align: middle;"


# Criar DataFrame final
df_tabela = pd.DataFrame(tabela)

# Remover as colunas de datas em que todos os sensores estão com "—"
datas_validas = [data for data in datas if not (df_tabela[data] == "—").all()]
df_tabela = df_tabela[["Tag", "Nome", "Plataforma", "Tipo medidor"] + datas_validas]

# Atualizar a lista de datas para o gráfico
datas = datas_validas

config = {
    "Tag": st.column_config.Column(
        "Tag",
        pinned=True
    )}

tags_filtradas = st.sidebar.multiselect("Filtrar por Tag:", df_tabela["Tag"].unique())
if tags_filtradas:
    df_tabela = df_tabela[df_tabela["Tag"].isin(tags_filtradas)]

filtro_por_nome = st.sidebar.multiselect("Filtrar por Nome:", df_tabela["Nome"].unique())
if filtro_por_nome:
    df_tabela = df_tabela[df_tabela["Nome"].isin(filtro_por_nome)]

filtro_por_tipo = st.sidebar.multiselect("Filtrar por Tipo:", df_tabela["Tipo medidor"].unique())
if filtro_por_tipo:
    df_tabela = df_tabela[df_tabela["Tipo medidor"].isin(filtro_por_tipo)]

# ----------------- NOVOS FILTROS DE STATUS -----------------
st.sidebar.markdown("---")
colunas_datas = [col for col in df_tabela.columns if col in datas]

aplicar_filtro_variacao = st.sidebar.checkbox("Ativar filtro por status")

if aplicar_filtro_variacao:
    opcao_status_todos = st.sidebar.selectbox(
        "Mostrar sensores que estão:",
        ["Todos com Variações", "Todos ON", "Todos OFF", "Todos —"]
    )

    colunas_datas = [col for col in df_tabela.columns if col in datas]

    if opcao_status_todos == "Todos com Variações":
        mascara_variacao = df_tabela[colunas_datas].apply(lambda linha: len(set(linha)) > 1, axis=1)
        df_tabela = df_tabela[mascara_variacao]
    elif opcao_status_todos == "Todos ON":
        df_tabela = df_tabela[df_tabela[colunas_datas].apply(lambda l: set(l) == {"ON"}, axis=1)]
    elif opcao_status_todos == "Todos OFF":
        df_tabela = df_tabela[df_tabela[colunas_datas].apply(lambda l: set(l) == {"OFF"}, axis=1)]
    elif opcao_status_todos == "Todos —":
        df_tabela = df_tabela[df_tabela[colunas_datas].apply(lambda l: set(l) == {"—"}, axis=1)]

st.title("📊 Histórico de Tags")
df_styled = df_tabela.style.map(colorir_celulas, subset=datas)

aba1, aba2 = st.tabs(["📋 Tabela", "📈 Gráfico"])

with aba1:
    st.dataframe(df_styled, width='stretch', hide_index=True)

with aba2:
    df_counts = pd.DataFrame({
        "Data": datas,
        "OFF": df_tabela[datas].apply(lambda col: (col == "OFF").sum()),
        "ON": df_tabela[datas].apply(lambda col: (col == "ON").sum())
    }).melt("Data", var_name="Status", value_name="Quantidade")

    # --- Gráfico base (linhas + pontos) ---
    base = (
        alt.Chart(df_counts)
        .mark_line(point=True)
        .encode(
            x=alt.X("Data:N", title="Data"),
            y=alt.Y("Quantidade:Q", title="Quantidade"),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(domain=["ON", "OFF"], range=["#10B981", "#EF4444"]),
                legend=alt.Legend(title="Status")
            ),
            tooltip=["Data", "Status", "Quantidade"]
        )
    )

    # --- Texto dentro das bolinhas ---
    text = (
        alt.Chart(df_counts)
        .mark_text(
            align="center",
            baseline="middle",
            dy=-12,  # ajuste vertical (negativo = acima, positivo = abaixo)
            fontSize=14,
            fontWeight="bold",
            color="black"
        )
        .encode(
            x="Data:N",
            y="Quantidade:Q",
            text="Quantidade:Q",
            color=alt.Color("Status:N", scale=alt.Scale(domain=["ON", "OFF"], range=["#10B981", "#EF4444"]))
        )
    )

    # --- Combina os dois ---
    chart = (base + text).properties(
        title="Status dos Equipamentos por Dia",
        width=700,
        height=400
    ).configure_title(
        fontSize=20,
        fontWeight="bold",
        anchor="start"
    )

    st.altair_chart(chart, use_container_width=True)

conn.close()
