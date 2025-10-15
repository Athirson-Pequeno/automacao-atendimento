import pandas as pd
import streamlit as st
from utils.mensagens import gerarMensagem
from utils.requisicoes import gerarTabelas
from utils.controlar_banco_de_dados import salvarTabela

#Configurar página do streamlit
st.set_page_config(page_title="Relatório de Medidores", layout="wide")

#Definir titulo da página
st.title("Relatório de Medidores offline")

#Definir campo para fazer upload de arquivo
uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

# --- Botão para gerar tabelas ---
if st.button("🔄 Gerar Tabelas de Requisições"):
    with st.spinner("Gerando tabelas e atualizando dados..."):
        try:
            if gerarTabelas():  # <- chama sua função
                st.success("Tabelas geradas e salvas com sucesso!")
                uploaded_file = '../data/sensores_atrasados.xlsx'
                salvarTabela(uploaded_file)
        except Exception as e:
            st.error(f"Erro ao gerar tabelas: {e}")

#Verifica se o arquivo foi enviado
if uploaded_file is not None:
    try:
        #Lê o arquivo enviado e seleciona a aba dados
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

        # Remove a coluna OBS, se existir
        if 'OBS' in df.columns:
            df = df.drop(columns=['OBS'])

        # Remove a coluna OBS, se existir
        if 'Nome+Descrição' in df.columns:
            df = df.drop(columns=['Nome+Descrição'])

        #Filtra os dados a partir da coluna de dias offline
        dados_filtrados = df[df['Dias off.'] > 0]

        st.success(f"{len(dados_filtrados)} registros encontrados com mais de 3 dias sem informações")

        #Configurar filtros
        #Filtro por Plataforma
        st.sidebar.header("Filtros")
        plataformas = sorted(df['Plataforma'].dropna().unique())
        plataforma_selecionada = st.sidebar.multiselect(
            "Filtrar por plataforma:", plataformas, default=plataformas)

        #Filtro por Data
        dias_min = int(df['Dias off.'].min())
        dias_max = int(df['Dias off.'].max())
        dias_range = st.sidebar.slider("Filtrar por dias off:", dias_min, dias_max, (dias_min, dias_max))

        # Aplica filtros
        dados_filtrados = df[
            (df['Plataforma'].isin(plataforma_selecionada)) &
            (df['Dias off.'].between(dias_range[0], dias_range[1])) &
            (df['Dias off.'] > 0)]

        # Estatísticas extras
        st.subheader("Resumo Geral")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Registros", len(dados_filtrados))
        col2.metric("Usuários com problemas", dados_filtrados['Email'].nunique())
        col3.metric("Sensores com problemas", dados_filtrados['DescriçãoSensor'].nunique())
        col4.metric("Maior número de dias OFF", int(dados_filtrados['Dias off.'].max()))

        with st.expander(f"Tabela de medidores sem registro"):
            st.dataframe(dados_filtrados, use_container_width=True)

        st.divider()

        #Agrupa os clientes por nome
        grupos = dados_filtrados.groupby('Nome')

        st.subheader("📬 Detalhes por Usuário")
        for nome, grupo_cliente in grupos:
            with st.expander(f"{nome}  -  {len(grupo_cliente)} registro(s)"):

                # Subgrupos dos cliente por plataforma
                subgrupos = grupo_cliente.groupby("Plataforma")

                for plataforma, subgrupo in subgrupos:
                    st.markdown(f"### 🌐 Plataforma: {plataforma} - {len(subgrupo)} registro(s)")
                    st.dataframe(subgrupo, use_container_width=True)

                    # Exibe a mensagem
                    st.code(gerarMensagem(subgrupo), language="markdown")

    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
else:
    st.info("Faça o upload do arquivo Excel para visualizar os dados.")


