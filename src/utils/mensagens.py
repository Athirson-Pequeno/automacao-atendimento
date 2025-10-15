import pandas as pd

def gerarMensagem(subgrupo: pd.DataFrame):
    nomes_medidores = subgrupo["DescriçãoSensor"].astype(str).tolist() if "DescriçãoSensor" in subgrupo.columns else []

    # Converte DataÚltimaLeitura com tratamento de erro
    ultima_info = []
    for val in subgrupo["DataÚltimaLeitura"]:
        try:
            # Remove espaços extras
            val = str(val).strip()
            data = pd.to_datetime(val, dayfirst=True, errors="raise")
            ultima_info.append(data.strftime("%d/%m/%Y"))
        except Exception:
            ultima_info.append("data não informada")  # Nunca falha na exibição

    partes = []
    for i, medidor in enumerate(nomes_medidores):
        data = ultima_info[i]
        partes.append(f"    • {medidor} desde {data}\n")

    lista_medidores = "".join(partes)

    medidores_com_erro = (
        "Identificamos que os medidores a seguir não estão enviando dados de consumo."
        if len(partes) > 1 else
        "Identificamos que o medidor a seguir não está enviando dados de consumo."
    )

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
