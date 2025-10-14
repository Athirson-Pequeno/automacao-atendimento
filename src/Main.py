import pandas as pd
import streamlit as st
import requests

import streamlit.components.v1 as components

#Gerar mensagem do ciente
def gerarMensagem(subgrupos):
    nomes_medidores = subgrupos["MEDIDOR"].astype(str).tolist() if "MEDIDOR" in subgrupo.columns else None

    # Tenta converter a coluna "ULTIMA INFO" para datetime e formatar
    if "ULTIMA INFO" in subgrupo.columns:
        ultima_info = pd.to_datetime(subgrupo["ULTIMA INFO"], errors="coerce").dt.strftime("%d/%m/%Y").tolist()
    else:
        ultima_info = []

    # Monta a primeira linha listando os medidores e as datas
    partes = []
    for i, medidor in enumerate(nomes_medidores):
        data = ultima_info[i] if ultima_info else "data não informada"
        partes.append(f"    • {medidor} desde {data.replace(" 00:00:00","")}\n")

    lista_medidores = "".join(partes[:-1]) + f"{partes[-1]}" if len(partes) > 1 else partes[0]

    # Monta a mensagem de acordo com a quantidade de medidores da plataforma
    if(len(partes) > 1):
        medidores_com_erro = "Identificamos que os medidores a seguir não estão enviando dados de consumo."
    else:
        medidores_com_erro = "Identificamos que o medidor a seguir não está enviando dados de consumo."

    mensagem = f"""
Olá, tudo bem?

{medidores_com_erro}

{lista_medidores}
Gostaríamos de verificar junto a você se houve alguma intervenção recente no local (como manutenção elétrica, desligamento de equipamentos ou troca de rede).  
Caso não tenha ocorrido nenhuma alteração, nossa equipe pode auxiliar na verificação e restabelecimento da comunicação do equipamento.  
Por gentileza, confirme se podemos seguir com o suporte ou, se preferir, nos informe um horário conveniente para realizarmos o contato técnico.

Ficamos à disposição para ajudar.

Atenciosamente.
    """

    return mensagem

#Configurar página do streamlit
st.set_page_config(page_title="Relatório de Medidores", layout="wide")

#Definir titulo da página
st.title("Relatório de Medidores com Dias OFF")

#Definir campo para fazer upload de arquivo
uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

#Verifica se o arquivo foi enviado
if uploaded_file is not None:
    try:
        #Lê o arquivo enviado e seleciona a aba dados
        df = pd.read_excel(uploaded_file, sheet_name="dados")

        # Remove a coluna OBS, se existir
        if 'OBS' in df.columns:
            df = df.drop(columns=['OBS'])

        #Filtra os dados a partir da coluna de dias offline
        dados_filtrados = df[df['DIAS OFF.'] > 0]

        st.success(f"{len(dados_filtrados)} registros encontrados com 'DIAS OFF.' > 0")

        #Configurar filtrosx
        #Filtro por Plataforma
        st.sidebar.header("Filtros")
        plataformas = sorted(df['PLATAFORMA'].dropna().unique())
        plataforma_selecionada = st.sidebar.multiselect(
            "Filtrar por plataforma:", plataformas, default=plataformas)

        #Filtro por Data
        dias_min = int(df['DIAS OFF.'].min())
        dias_max = int(df['DIAS OFF.'].max())
        dias_range = st.sidebar.slider("Filtrar por dias OFF:", dias_min, dias_max, (dias_min, dias_max))

        # Aplica filtros
        dados_filtrados = df[
            (df['PLATAFORMA'].isin(plataforma_selecionada)) &
            (df['DIAS OFF.'].between(dias_range[0], dias_range[1])) &
            (df['DIAS OFF.'] > 0)]

        # Estatísticas extras
        st.subheader("Resumo Geral")

        headers = {'Access-token': ''}
        response = requests.get('', headers=headers)

        data = response.json()

        # A lista principal está dentro de "data"
        dados = data["data"]

        # Usamos json_normalize para achatar as chaves "sensor" e "user"
        df = pd.json_normalize(dados, sep='_')

        # Exporta para Excel
        df.to_excel("../data/dados_sensores.xlsx", index=False)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Registros", len(dados_filtrados))
        col2.metric("Usuários com problemas", dados_filtrados['EMAIL'].nunique())
        col3.metric("Maior número de dias OFF", int(dados_filtrados['DIAS OFF.'].max()))


        with st.expander(f"Tabela de medidores sem registro"):
            st.dataframe(dados_filtrados, use_container_width=True)

        st.divider()

        #Agrupa os clientes por nome
        grupos = dados_filtrados.groupby('NOME')

        st.subheader("📬 Detalhes por Usuário")
        for nome, grupo_cliente in grupos:
            with st.expander(f"{nome}  -  {len(grupo_cliente)} registro(s)"):

                # Subagrupa o cliente por plataforma
                subgrupos = grupo_cliente.groupby("PLATAFORMA")

                for plataforma, subgrupo in subgrupos:
                    st.markdown(f"### 🌐 Plataforma: {plataforma} ({len(subgrupo)} registro(s))")
                    st.dataframe(subgrupo, use_container_width=True)

                    # Exibe a mensagem
                    st.code(gerarMensagem(subgrupo), language="markdown")


    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
else:
    st.info("📥 Faça o upload do arquivo Excel para visualizar os dados.")


