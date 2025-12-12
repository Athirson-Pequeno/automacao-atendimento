from utils.requisicoes import buscarUsuarios, buscarMetricas
from utils.controlar_banco_de_dados import salvarUsuarios, salvarMetricas, buscarMetricasPorMes, buscarTodasAsMetricas, \
    buscarMetricasComUsuarios

import os
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from utils.ui import aplicar_estilo_sidebar


# usuarios = buscarUsuarios()
# salvarUsuarios(usuarios)
# metricas = buscarMetricas(usuarios)
# salvarMetricas(metricas)

aplicar_estilo_sidebar()

st.set_page_config(page_title="Acessos dos clientes", layout="wide")
st.title("Relatório de Acessos dos clientes")

hoje = datetime.today()

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("📅 Início",
                                value=datetime(hoje.year, hoje.month, 1),
                                min_value=datetime(2000, 1, 1),
                                max_value=hoje)
with col2:
    data_fim = st.date_input("📅 Fim",
                             value=hoje,
                             min_value=datetime(2000, 1, 1),
                             max_value=hoje)

dt_inicio = datetime.combine(data_inicio, datetime.min.time())
dt_fim = datetime.combine(data_fim, datetime.min.time())

ts_inicio_ms = int(dt_inicio.timestamp() * 1000)
ts_fim_ms = int(dt_fim.timestamp() * 1000)

metricas_mes_atual = buscarMetricasPorMes(ts_fim_ms)

if not metricas_mes_atual:
    usuarios = buscarUsuarios()
    salvarUsuarios(usuarios)
    metricas = buscarMetricas(usuarios, ts_inicio_ms, ts_fim_ms)
    salvarMetricas(metricas)

dados = buscarMetricasComUsuarios()

df = pd.DataFrame(dados, columns=[
    "user_id",
    "nome",
    "email",
    "cliente_ativo",
    "mes",
    "acessos"
])

df_pivot = df.pivot_table(
    index=["nome", "email", "cliente_ativo"],
    columns="mes",
    values="acessos",
    fill_value=0,
    aggfunc="sum"
)

df_pivot = df_pivot.sort_index(axis=1, key=lambda x: pd.to_datetime(x, format="%m/%Y"))

df_pivot = df_pivot.reset_index()

st.subheader("📊 Relatório consolidado de acessos por usuário e mês")
st.dataframe(df_pivot, use_container_width=True)