import json
import os
from datetime import datetime, timezone
import pandas as pd
import requests
from dotenv import load_dotenv

# --- Configurações ---
DIAS_LIMITES = 2
LIMITE_ATRASO_MS = DIAS_LIMITES * 24 * 60 * 60 * 1000  # 2 dias
AGORA_MS = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Carrega variáveis de ambiente ---
load_dotenv(".env")

# Lê a variável do .env e converte JSON → lista Python
LISTA_REQUISICOES = json.loads(os.getenv("LISTA_REQUISICOES"))


# --- Função para buscar sensores atrasados ---
def buscar_atrasados(url, token, nome_fonte):
    try:
        response = requests.get(url, headers={"Access-Token": token})
        if response.status_code != 200:
            return []

        data = response.json()

        # Garante que o formato contém 'data'
        if "data" not in data:
            return []

        sensores = data["data"]

        # Corrige timestamps para Lyum
        if nome_fonte == "Lyum":
            for item in sensores:
                if "lastMeasurementTimestamp" in item and item["lastMeasurementTimestamp"]:
                    ts = item["lastMeasurementTimestamp"] * 1000  # segundos → ms
                    corrigido = ts - 3 * 60 * 60 * 1000  # UTC → BRT (-3h)
                    item["lastMeasurementTimestamp"] = corrigido

        # Corrige nome do usuário (LiteMe e UFCG)
        if nome_fonte in ["LiteMe", "LiteMe - UFCG"]:
            for item in sensores:
                user = item.get("user", {})
                nome_completo = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                item["user"]["name"] = nome_completo

        # Filtra atrasados
        atrasados = []
        for item in sensores:
            ts = item.get("lastMeasurementTimestamp")
            if ts and ts <= AGORA_MS - LIMITE_ATRASO_MS:
                atrasados.append({**item, "fonte": nome_fonte})

        return atrasados

    except Exception as e:
        return []


def gerarTabelas():
    # --- Executa todas as requisições ---
    todos = []
    for req in LISTA_REQUISICOES:
        todos.extend(buscar_atrasados(req["url"], req["token"], req["fonte"]))

    print(f"\nTotal geral de sensores atrasados: {len(todos)}")

    # --- Monta DataFrame e gera planilha ---
    linhas = []
    for item in todos:
        user = item.get("user", {})
        sensor = item.get("sensor", {})

        nome = user.get("name", "")
        email = user.get("email", "")
        descricao = sensor.get("description", "")
        ultima_leitura = item.get("lastMeasurementTimestamp")

        if ultima_leitura:
            data_leitura = datetime.fromtimestamp(ultima_leitura / 1000)
            dias_off = (datetime.now() - data_leitura).days
        else:
            data_leitura = ""
            dias_off = 0

        linhas.append({
            "DataAtual": datetime.now().strftime("%d/%m/%Y"),
            "Nome+Descrição": f"{nome}{descricao}",
            "Nome": nome,
            "Email": email,
            "DescriçãoSensor": descricao,
            "DataÚltimaLeitura": data_leitura.strftime("%d/%m/%Y"),
            "Plataforma": item.get("fonte"),
            "Dias off.": dias_off
        })

    df = pd.DataFrame(linhas)

    # "../data/sensores_atrasados.xlsx"
    PASTA_TABELA = os.path.join('database', 'tabelas')
    os.makedirs(PASTA_TABELA, exist_ok=True)

    df.to_excel(os.path.join(PASTA_TABELA, os.path.basename('sensores_atrasados.xlsx')), index=False, engine='openpyxl')

    return True
