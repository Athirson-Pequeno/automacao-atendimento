import os

import pandas as pd
import streamlit as st

from utils.controlar_banco_de_dados import salvarTabela
from utils.mensagens import gerarMensagem, gerarMensagemHTML_bonito
from utils.requisicoes import gerarTabelas
from utils.ui import aplicar_estilo_sidebar
from utils.enviar_emails import send_email

aplicar_estilo_sidebar()

# Caminho absoluto até a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
TABELAS_DIR = os.path.join(DATABASE_DIR, "tabelas")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(TABELAS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# Configurar página do streamlit
st.set_page_config(page_title="Relatório de Medidores", layout="wide")

# Definir titulo da página
st.title("Relatório de Medidores offline")

# Definir campo para fazer upload de arquivo
uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

# Usa arquivo da sessão, se já existir
if uploaded_file is not None:
    st.session_state["uploaded_file"] = uploaded_file
elif "uploaded_file" in st.session_state:
    uploaded_file = st.session_state["uploaded_file"]

# --- Botão para gerar tabelas ---
if st.button("🔄 Gerar Tabelas de Requisições"):
    with st.spinner("Gerando tabelas e atualizando dados..."):
        try:
            if gerarTabelas():  # <- chama sua função
                st.success("Tabelas geradas e salvas com sucesso!")
                uploaded_file = os.path.join(TABELAS_DIR, 'sensores_atrasados.xlsx')
                st.session_state["uploaded_file"] = uploaded_file
        except Exception as e:
            st.error(f"Erro ao gerar tabelas: {e}")

# Verifica se o arquivo foi enviado
if uploaded_file is not None:
    # Salva o arquivo enviado na sessão
    if "df" not in st.session_state:
        st.session_state["df"] = pd.read_excel(uploaded_file, sheet_name="Sheet1")

    df = st.session_state["df"]

    salvarTabela(uploaded_file)

    try:
        # Remove a coluna OBS, se existir
        if 'OBS' in df.columns:
            df = df.drop(columns=['OBS'])

        # Remove a coluna OBS, se existir
        if 'Nome+Descrição' in df.columns:
            df = df.drop(columns=['Nome+Descrição'])

        # Filtra os dados a partir da coluna de dias offline
        dados_filtrados = df[df['Dias off.'] >= 2]

        #Informa a quantidade de registro encontrados
        st.success(f"{len(dados_filtrados)} registros encontrados com mais de 2 dias sem informações")

        # Configurar filtros
        # Filtro por Plataforma
        st.sidebar.header("Filtros")
        plataformas = sorted(df['Plataforma'].dropna().unique())
        plataforma_selecionada = st.sidebar.multiselect(
            "Filtrar por plataforma:", plataformas, default=plataformas)

        # Filtro por Data
        dias_min = st.sidebar.number_input("Qtd. dias iniciais", value=2, min_value=0, step=1)
        dias_max = int(df['Dias off.'].max())

        # Aplica filtros
        dados_filtrados = df[
            (df['Plataforma'].isin(plataforma_selecionada)) &
            (df['Dias off.'].between(dias_min, dias_max)) &
            (df['Dias off.'] > 0)]

        # Estatísticas extras
        st.subheader("Resumo Geral")
        col1, col2, col3 = st.columns(3)
        col1.metric("Sensores com problemas", dados_filtrados['DescriçãoSensor'].nunique())
        col2.metric("Usuários com problemas", dados_filtrados['Email'].nunique())
        col3.metric("Maior número de dias OFF", int(dados_filtrados['Dias off.'].max()))

        st.divider()

        #Exibe todos os medidores sem registro
        st.subheader("Medidores sem registros")
        st.dataframe(dados_filtrados, width='stretch')

        st.divider()

        # Agrupa os clientes por nome
        grupos = dados_filtrados.groupby('Nome')

        st.subheader("Detalhes por Usuário")
        for nome, grupo_cliente in grupos:
            with st.expander(f"{nome}  -  {len(grupo_cliente)} registro(s)"):

                # Subgrupos dos cliente por plataforma
                subgrupos = grupo_cliente.groupby("Plataforma")

                for plataforma, subgrupo in subgrupos:
                    st.markdown(f"### 🌐 Plataforma: {plataforma} - {len(subgrupo)} registro(s)")
                    st.dataframe(subgrupo, width='stretch')

                    # Exibe a mensagem
                    st.code(gerarMensagem(subgrupo), language="markdown")

                    # Botão para enviar e-mail
                    email_destinatario = subgrupo['Email'].iloc[0]  # pega o email do cliente
                    if st.button(f"✉️ Enviar e-mail para {nome} ({email_destinatario})"):
                        with st.spinner(f"Enviando e-mail para {email_destinatario}..."):
                            try:
                                resultado = send_email(
                                    to_address=email_destinatario,
                                    subject="Atualização de Medidores Offline",
                                    content=gerarMensagemHTML_bonito(subgrupo)
                                )
                                st.success(f"E-mail enviado com sucesso para {email_destinatario}!")
                            except Exception as e:
                                st.error(f"Erro ao enviar e-mail: {e}")

    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
else:
    st.info("Faça o upload do arquivo Excel para visualizar os dados.")
