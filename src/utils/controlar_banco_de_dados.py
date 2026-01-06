import os
from datetime import datetime

import pandas as pd
import psycopg2
from dateutil.utils import today
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

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


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def salvarTabela(arquivo):
    conn = get_connection()
    cursor = conn.cursor()
    df = pd.read_excel(arquivo)

    df['DataAtual'] = pd.to_datetime(df['DataAtual'], dayfirst=True).dt.strftime('%Y-%m-%d')
    df['DataÚltimaLeitura'] = pd.to_datetime(df['DataÚltimaLeitura'], dayfirst=True).dt.strftime('%Y-%m-%d')

    df.rename(columns={
        "DataAtual": "data_registro",
        "Nome": "nome",
        "Email": "email",
        "DescriçãoSensor": "descricao_sensor",
        "DataÚltimaLeitura": "ultima_leitura",
        "Plataforma": "plataforma",
        "Dias off.": "dias_off",
        "TipoMedidor": "tipo_medidor",
        "Manutencao": "manutencao"
    }, inplace=True)

    # --- Criar tabela se não existir ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_sensores (
            id SERIAL PRIMARY KEY,
            data_registro DATE NOT NULL,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            descricao_sensor TEXT NOT NULL,
            ultima_leitura DATE,
            plataforma TEXT,
            status TEXT,
            tipo_medidor TEXT,
            manutencao TEXT,
            UNIQUE(data_registro, nome, descricao_sensor)
        )
    """)

    conn.commit()

    # --- Inserir dados novos evitando duplicados ---
    for _, row in df.iterrows():
        cursor.execute("""
                INSERT INTO historico_sensores (
                    data_registro, nome, descricao_sensor, email, ultima_leitura, plataforma, tipo_medidor, status, manutencao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (data_registro, nome, descricao_sensor) DO UPDATE
                SET 
                ultima_leitura = EXCLUDED.ultima_leitura, 
                status = EXCLUDED.status, 
                manutencao = EXCLUDED.manutencao
            """, (
            row["data_registro"],
            row["nome"],
            row["descricao_sensor"],
            row["email"],
            row.get("ultima_leitura", None),
            row.get("plataforma", ""),
            row["tipo_medidor"],
            "OFF" if row["dias_off"] > 0 else "ON",
            row["manutencao"]
        ))

    conn.commit()

    # Gerar relatório
    ano = str(pd.Timestamp.today().year)
    mes = str(pd.Timestamp.today().month).zfill(2)

    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    df_mensal = pd.read_sql_query("SELECT * FROM historico_sensores ORDER BY data_registro ASC", engine)

    nome_relatorio = os.path.join(RELATORIOS_DIR, f"historico_{ano}_{mes}.xlsx")
    df_mensal.to_excel(nome_relatorio, index=False)

    conn.commit()
    cursor.close()
    conn.close()


def criarTabelasAcesso():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            cliente_ativo BOOLEAN,
            plataforma TEXT,
            UNIQUE(email, plataforma)
        );
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_acesso (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            data_registro DATE NOT NULL,
            acessos INTEGER,
            mes TEXT,
            UNIQUE(user_id, mes)
        );
        """)

    conn.commit()
    cursor.close()
    conn.close()


def salvarUsuarios(usuarios):
    conn = get_connection()
    cursor = conn.cursor()
    criarTabelasAcesso()

    for usuario in usuarios:
        cursor.execute("""
                        INSERT INTO usuarios (
                            nome, email, cliente_ativo, plataforma
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
            usuario["nome"],
            usuario["email"],
            usuario["cliente_ativo"],
            usuario["plataforma"]
        ))

    conn.commit()
    cursor.close()
    conn.close()


def salvarMetricas(metricas):
    conn = get_connection()
    cursor = conn.cursor()
    criarTabelasAcesso()

    for metrica in metricas:
        data_registro = today().strftime("%Y-%m-%d")
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (metrica["email"],))
        result = cursor.fetchone()

        if not result:
            print(f"Usuário não encontrado: {metrica['email']}")
            continue

        user_id = result[0]

        for acesso in metrica.get("acessos_por_mes", []):
            cursor.execute("""
                        INSERT INTO historico_acesso (
                            user_id, data_registro, acessos, mes
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, mes) DO UPDATE
                        SET acessos = EXCLUDED.acessos
                    """, (
                user_id,
                data_registro,
                acesso["access"],
                acesso["month"]
            ))

    conn.commit()
    cursor.close()
    conn.close()


def buscarMetricasPorMes(timestamp_data_fim):
    conn = get_connection()
    cursor = conn.cursor()
    criarTabelasAcesso()

    mes = timestampParaMes(timestamp_data_fim)

    cursor.execute("SELECT * FROM historico_acesso WHERE mes = %s", (str(mes),))
    result = cursor.fetchall()
    cursor.close()
    return result

def buscarTodasAsMetricas():
    conn = get_connection()
    cursor = conn.cursor()
    criarTabelasAcesso()

    cursor.execute("SELECT * FROM historico_acesso")
    result = cursor.fetchall()
    cursor.close()
    return result


def buscarMetricasComUsuarios(inicio, fim):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id,
            u.nome,
            u.email,
            u.cliente_ativo,
            ha.mes,
            ha.acessos
        FROM historico_acesso ha
        INNER JOIN usuarios u ON u.id = ha.user_id
        WHERE to_date(ha.mes, 'MM/YYYY') BETWEEN to_date(%s, 'MM/YYYY') AND to_date(%s, 'MM/YYYY')
        ORDER BY u.nome ASC, to_date(ha.mes, 'MM/YYYY')
    """, (inicio, fim))

    result = cursor.fetchall()
    cursor.close()
    return result

def alternarStatusUsuario(user_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET cliente_ativo = %s
        WHERE id = %s
    """, (status, user_id))

    conn.commit()
    cursor.close()
    conn.close()

def timestampParaMes(timestamp_ms):
    data = datetime.fromtimestamp(timestamp_ms / 1000)
    return data.date().strftime("%m/%Y")
