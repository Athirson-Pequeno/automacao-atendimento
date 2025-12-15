import calendar
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.controlar_banco_de_dados import (
    salvarUsuarios,
    salvarMetricas,
    buscarMetricasPorMes,
    buscarMetricasComUsuarios,
    alternarStatusUsuario
)
from utils.requisicoes import buscarUsuarios, buscarMetricas
from utils.ui import aplicar_estilo_sidebar

aplicar_estilo_sidebar()

st.set_page_config(page_title="Acessos dos clientes", layout="wide")
st.title("Relatório de Acessos dos clientes")

hoje = datetime.today()

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("📅 Início", value=datetime(hoje.year, hoje.month, 1))
with col2:
    data_fim = st.date_input("📅 Fim", value=hoje)


hoje = datetime.today()

st.sidebar.header("Início")

anos = list(range(2020, hoje.year + 1))
meses = list(range(1, 13))

col1Ini, col2Ini = st.sidebar.columns(2)

with col1Ini:
    mesIni = st.selectbox(
        "Mês ini.",
        meses,
        format_func=lambda m: calendar.month_name[m],
        index=meses.index(hoje.month - 1)
    )
with col2Ini:
    anoIni = st.selectbox("Ano ini.", anos, index=anos.index(hoje.year))

st.sidebar.header("Fim")

col1Fim, col2Fim = st.sidebar.columns(2)

with col1Fim:
    mesFim = st.selectbox(
        "Mês fim",
        meses,
        format_func=lambda m: calendar.month_name[m],
        index=meses.index(hoje.month)
    )

with col2Fim:
    anoFim = st.selectbox("Ano fim", anos, index=anos.index(hoje.year))


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


mes_ano_inicio = f"{mesIni:02d}/{anoIni}"
mes_ano_fim = f"{mesFim:02d}/{anoFim}"

dados = buscarMetricasComUsuarios(mes_ano_inicio, mes_ano_fim)

df = pd.DataFrame(dados, columns=[
    "user_id",
    "nome",
    "email",
    "cliente_ativo",
    "mes",
    "acessos"
])

filtro_status = st.sidebar.radio(
    "Filtrar usuários:",
    ["Todos", "Ativos", "Inativos"],
    horizontal=False
)

if filtro_status == "Ativos":
    df = df[df["cliente_ativo"] == True]
elif filtro_status == "Inativos":
    df = df[df["cliente_ativo"] == False]

df_pivot = df.pivot_table(
    index=["user_id", "nome", "email", "cliente_ativo"],
    columns="mes",
    values="acessos",
    fill_value=0,
    aggfunc="sum"
).reset_index()

df_pivot["_original_status"] = df_pivot["cliente_ativo"]

colunas_visiveis = [c for c in df_pivot.columns if c != "_original_status" and c != "user_id"]

edited_df = st.data_editor(
    df_pivot,
    width='stretch',
    hide_index=True,
    column_order=colunas_visiveis,
    column_config={
        "cliente_ativo": st.column_config.CheckboxColumn(
            label="Ativo?",
            help="Ativa ou inativa o cliente"
        )
    },
    disabled=["user_id", "nome", "email", "_original_status"]
)

for _, row in edited_df.iterrows():
    if row["cliente_ativo"] != row["_original_status"]:
        alternarStatusUsuario(int(row["user_id"]), bool(row["cliente_ativo"]))
        st.success(f"Status de {row['nome']} atualizado!")
        st.rerun()