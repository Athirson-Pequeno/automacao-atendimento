import pandas as pd

def gerarMensagem(subgrupo: pd.DataFrame):
    nomes_medidores = subgrupo["DescriçãoSensor"].astype(str).tolist() if "DescriçãoSensor" in subgrupo.columns else []

    # Converte DataÚltimaLeitura com tratamento de erro
    ultima_info = []
    for date in subgrupo["DataÚltimaLeitura"]:
        try:
            # Remove espaços extras
            date = str(date).strip()
            data = pd.to_datetime(date, dayfirst=True, errors="raise")
            ultima_info.append(data.strftime("%d/%m/%Y"))
        except Exception:
            ultima_info.append("data não informada")  # Nunca falha na exibição

    partes = []
    # Gera a lista de sensores sem dados
    for i, medidor in enumerate(nomes_medidores):
        data = ultima_info[i]
        partes.append(f"    • {medidor} desde {data}\n")

    lista_medidores = "".join(partes)

    #Muda a mensagem caso a quantidade de sensores seja maior que um
    mensagem_de_quantidade = (
        "Identificamos que os medidores a seguir não estão enviando dados de consumo."
        if len(partes) > 1 else
        "Identificamos que o medidor a seguir não está enviando dados de consumo."
    )

    #Gera a mensagem final pra o cliente
    mensagem = f"""
Olá, tudo bem?

{mensagem_de_quantidade}

{lista_medidores}
Gostaríamos de verificar junto a você se houve alguma intervenção recente no local (como manutenção elétrica, desligamento de equipamentos ou troca de rede).  
Caso não tenha ocorrido nenhuma alteração, nossa equipe pode auxiliar na verificação e restabelecimento da comunicação do equipamento.  
Por gentileza, confirme se podemos seguir com o suporte ou, se preferir, nos informe um horário conveniente para realizarmos o contato técnico.

Ficamos à disposição para ajudar.

Atenciosamente.
    """

    return mensagem



import pandas as pd

def gerarMensagemHTML_bonito(subgrupo: pd.DataFrame):
    nomes_medidores = subgrupo["DescriçãoSensor"].astype(str).tolist() if "DescriçãoSensor" in subgrupo.columns else []

    ultima_info = []
    for date in subgrupo["DataÚltimaLeitura"]:
        try:
            date = str(date).strip()
            data = pd.to_datetime(date, dayfirst=True, errors="raise")
            ultima_info.append(data.strftime("%d/%m/%Y"))
        except Exception:
            ultima_info.append("data não informada")

    # Lista de medidores como <li>
    lista_items = ""
    for i, medidor in enumerate(nomes_medidores):
        data = ultima_info[i]
        lista_items += f"<li style='margin-bottom: 5px;'><strong>{medidor}</strong> desde {data}</li>"

    mensagem_de_quantidade = (
        "Identificamos que os medidores a seguir não estão enviando dados de consumo."
        if len(nomes_medidores) > 1 else
        "Identificamos que o medidor a seguir não está enviando dados de consumo."
    )

    # HTML final
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; background-color: #fafafa;">
      <h2 style="color: #2E86C1;">Olá, tudo bem?</h2>
      <p>{mensagem_de_quantidade}</p>
      <ul style="margin-left: 20px; padding-left: 0;">
        {lista_items}
      </ul>
      <p>
        Gostaríamos de verificar junto a você se houve alguma intervenção recente no local (como manutenção elétrica, desligamento de equipamentos ou troca de rede).
        <br>
        <br>
        Caso não tenha ocorrido nenhuma alteração, nossa equipe pode auxiliar na verificação e restabelecimento da comunicação do equipamento.
        <br>
        <br>
        Por gentileza, confirme se podemos seguir com o suporte ou, se preferir, nos informe um horário conveniente para realizarmos o contato técnico.
      </p>
      <p>Ficamos à disposição para ajudar.</p>
      <p style="margin-top: 30px;">Atenciosamente,<br>
      <strong>Athirson Souza Pequeno</strong>
      <br>
      <strong>Suporte</strong>
      <br>
      <strong>LiteMe | Inteligência Energética</strong>
      </p>
      <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
      <p style="font-size: 12px; color: #888;">Suporte Liteme - www.liteme.com.br</p>
    </div>
  </body>
</html>
"""
    return html
