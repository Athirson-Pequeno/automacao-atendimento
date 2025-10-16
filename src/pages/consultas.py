import os
import sqlite3

import pandas as pd
import streamlit as st

# Caminho absoluto até a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(TABELAS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# Caminho do banco
banco_sqlite = os.path.join(DATABASE_DIR, "sensores_atrasados.db")

# Configuração da página
st.set_page_config(page_title="Consultas de Sensores", layout="wide")
st.title("Consultas de Sensores Atrasados")

# Conectar ao banco
if not os.path.exists(banco_sqlite):
    st.error("O banco de dados ainda não foi criado. Gere os dados primeiro na tela principal.")
else:
    conn = sqlite3.connect(banco_sqlite)

    # Filtros
    st.sidebar.header("Filtros")
    ano = st.sidebar.text_input("Ano (ex: 2025):", "")
    mes = st.sidebar.text_input("Mês (ex: 10):", "")

    nome = st.sidebar.text_input("Nome do cliente:")
    email = st.sidebar.text_input("Email: ")
    plataforma = st.sidebar.text_input("Plataforma:")

    query = "SELECT * FROM sensores_atrasados WHERE 1=1"
    params = []

    if ano:
        query += " AND strftime('%Y', data_registro) = ?"
        params.append(ano)
    if mes:
        query += " AND strftime('%m', data_registro) = ?"
        params.append(mes)
    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if email:
        query += " AND email LIKE ?"
        params.append(f"%{email}%")
    if plataforma:
        query += " AND plataforma LIKE ?"
        params.append(f"%{plataforma}%")

    # Executar consulta
    df = pd.read_sql_query(query, conn, params=params)

    # Exibir resultados
    if not df.empty:
        st.success(f"{len(df)} registros encontrados")
        st.dataframe(df, use_container_width=True)

        # Exportar
        if st.download_button("⬇️ Baixar como Excel", df.to_csv(index=False).encode('utf-8'), "consultas_sensores.csv"):
            st.toast("Arquivo exportado com sucesso!")
    else:
        st.warning("Nenhum registro encontrado com esses filtros.")

    conn.close()
