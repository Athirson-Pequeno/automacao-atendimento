import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from utils.ui import aplicar_estilo_sidebar

aplicar_estilo_sidebar()

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

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Configuração da página
st.set_page_config(page_title="Consultas de Sensores", layout="wide")
st.title("Consultas de Sensores Atrasados")

# Filtros
st.sidebar.header("Filtros")
ano = st.sidebar.text_input("Ano (ex: 2025):", "")
mes = st.sidebar.text_input("Mês (ex: 10):", "")

nome = st.sidebar.text_input("Nome do cliente:")
email = st.sidebar.text_input("Email: ")
plataforma = st.sidebar.text_input("Plataforma:")

query = "SELECT * FROM historico_sensores WHERE 1=1"
params = []

if ano:
    query += " AND strftime('%Y', data_registro) = %s"
    params.append(ano)
if mes:
    query += " AND strftime('%m', data_registro) = %s"
    params.append(mes)
if nome:
    query += " AND nome LIKE %s"
    params.append(f"%{nome}%")
if email:
    query += " AND email LIKE %s"
    params.append(f"%{email}%")
if plataforma:
    query += " AND plataforma LIKE %s"
    params.append(f"%{plataforma}%")

# Executar consulta
df = pd.read_sql_query(query, engine, params=params)

# Exibir resultados
if not df.empty:
    st.success(f"{len(df)} registros encontrados")
    st.dataframe(df, width='stretch')

    # Exportar
    if st.download_button("⬇️ Baixar como Excel", df.to_csv(index=False).encode('utf-8'), "consultas_sensores.csv"):
        st.toast("Arquivo exportado com sucesso!")
else:
    st.warning("Nenhum registro encontrado com esses filtros.")

