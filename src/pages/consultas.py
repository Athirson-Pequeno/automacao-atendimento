import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from utils.ui import aplicar_estilo_sidebar

aplicar_estilo_sidebar()

# Caminhos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(TABELAS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# Banco de dados
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Página
st.set_page_config(page_title="Consultas de Sensores", layout="wide")
st.title("Consultas de Sensores Atrasados")

# Filtros
st.sidebar.header("Filtros")
ano = st.sidebar.text_input("Ano (ex: 2025):", "")
mes = st.sidebar.text_input("Mês (ex: 10):", "")
data_registro = st.sidebar.text_input("Data específica (ex: 2025-11-01):", "")
nome = st.sidebar.text_input("Nome do cliente:")
email = st.sidebar.text_input("Email:")
plataforma = st.sidebar.text_input("Plataforma:")

# Query base
query = "SELECT * FROM historico_sensores WHERE 1=1"
params = {}

# Filtros dinâmicos
if ano:
    query += " AND EXTRACT(YEAR FROM data_registro) = %(ano)s"
    params["ano"] = int(ano)
if mes:
    query += " AND EXTRACT(MONTH FROM data_registro) = %(mes)s"
    params["mes"] = int(mes)
if data_registro:
    query += " AND DATE(data_registro) = %(data_registro)s"
    params["data_registro"] = data_registro
if nome:
    query += " AND nome ILIKE %(nome)s"
    params["nome"] = f"%{nome}%"
if email:
    query += " AND email ILIKE %(email)s"
    params["email"] = f"%{email}%"
if plataforma:
    query += " AND plataforma ILIKE %(plataforma)s"
    params["plataforma"] = f"%{plataforma}%"

# ✅ O segredo: use %(nome)s e params = dict, não lista
df = pd.read_sql_query(query, engine, params=params)

# Exibir resultados
if not df.empty:
    st.success(f"{len(df)} registros encontrados")
    st.dataframe(df, width='stretch')

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar como CSV", csv_data, "consultas_sensores.csv", "text/csv")
else:
    st.warning("Nenhum registro encontrado com esses filtros.")
