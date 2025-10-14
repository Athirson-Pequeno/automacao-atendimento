import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# --- Configurações ---
LIMITE_ATRASO_MS = 3 * 24 * 60 * 60 * 1000  # 3 dias
AGORA_MS = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

REQUISICOES = [
    {
        "url": "",
        "token": "",
        "fonte": ""
    },
    {
        "url": "",
        "token": "",
        "fonte": ""
    },
    {
        "url": "",
        "token": "",
        "fonte": ""
    }
]

# --- Função para buscar sensores atrasados ---
def buscar_atrasados(url, token, nome_fonte):
    try:
        print(f"Buscando dados de {nome_fonte}...")

        response = requests.get(url, headers={"Access-Token": token})
        if response.status_code != 200:
            print(f"❌ Erro {response.status_code} em {nome_fonte}: {response.text}")
            return []

        data = response.json()

        # Garante que o formato contém 'data'
        if "data" not in data:
            print(f"⚠️ Estrutura inesperada em {nome_fonte}: chaves = {list(data.keys())}")
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

        print(f"✅ {len(atrasados)} sensores atrasados encontrados em {nome_fonte}")
        return atrasados

    except Exception as e:
        print(f"⚠️ Erro ao processar {nome_fonte}: {e}")
        return []


# --- Executa todas as requisições ---
todos = []
for req in REQUISICOES:
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
        data_leitura = datetime.fromtimestamp(ultima_leitura / 1000).strftime("%d/%m/%Y")
    else:
        data_leitura = ""

    linhas.append({
        "DataAtual": datetime.now().strftime("%d/%m/%Y"),
        "Nome+Descrição": f"{nome} {descricao}",
        "Nome": nome,
        "Email": email,
        "DescriçãoSensor": descricao,
        "DataÚltimaLeitura": data_leitura,
        "Fonte": item.get("fonte")
    })

df = pd.DataFrame(linhas)
df.to_excel("../data/sensores_atrasados.xlsx", index=False)

print("📁 Planilha gerada com sucesso: ../data/sensores_atrasados.xlsx")
