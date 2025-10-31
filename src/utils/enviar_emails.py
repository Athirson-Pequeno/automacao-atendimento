import subprocess
import json
import os
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LISTA_REQUISICOES = json.loads(os.getenv("LISTA_REQUISICOES"))

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
ACCESS_TOKEN  = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

def refresh_access_token():
    """Renova o access_token usando o refresh_token"""
    global ACCESS_TOKEN
    cmd = [
        "curl",
        "-X", "POST",
        "https://accounts.zoho.com/oauth/v2/token",
        "-d", f"grant_type=refresh_token",
        "-d", f"client_id={CLIENT_ID}",
        "-d", f"client_secret={CLIENT_SECRET}",
        "-d", f"refresh_token={REFRESH_TOKEN}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    ACCESS_TOKEN = data["access_token"]
    print("Access token renovado!")

def send_email(to_address, subject, content):
    """Envia e-mail usando a API do Zoho Mail"""
    cmd = [
        "curl",
        "-X", "POST",
        f"https://mail.zoho.com/api/accounts/{ACCOUNT_ID}/messages",
        "-H", f"Authorization: Zoho-oauthtoken {ACCESS_TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "fromAddress": "suporte02@liteme.com.br",
            "toAddress": to_address,
            "subject": subject,
            "content": content
        })
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if "authFail" in result.stdout or "INVALID_OAUTHTOKEN" in result.stdout:
        print("Token expirado! Renovando...")
        refresh_access_token()
        send_email(to_address, subject, content)  # tenta de novo
    else:
        print("E-mail enviado com sucesso!")
        print(result.stdout)

