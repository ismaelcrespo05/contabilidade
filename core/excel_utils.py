import re
from datetime import date, timedelta, datetime

EPOCA_EXCEL = date(1899, 12, 30)


def _converter_valor_data(valor):
    """
    Converte o valor de uma célula de "data de vencimento" em um objeto
    date, aceitando os 3 formatos que aparecem na prática: já é uma
    data, é um número serial do Excel, ou é texto livre (às vezes com
    erro de digitação). Retorna None quando não dá pra confiar.
    """
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    if isinstance(valor, (int, float)):
        try:
            return EPOCA_EXCEL + timedelta(days=int(valor))
        except (OverflowError, ValueError):
            return None

    if isinstance(valor, str):
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,6})", valor)
        if not m:
            return None

        dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))

        texto_ano = m.group(3)
        if len(texto_ano) == 5 and texto_ano.startswith("20"):
            ano = int(texto_ano[:2] + texto_ano[3:])

        if not (2000 <= ano <= 2100):
            return None

        try:
            return date(ano, mes, dia)
        except ValueError:
            return None

    return None


def ler_planilha_certificados(arquivo):
    """
    Lê um .xlsx com duas colunas (nome / data de vencimento), na
    primeira aba, ignorando o cabeçalho. Retorna uma lista de dicts:
    {"nome_empresa": str, "data_vencimento": date | None, "valor_original": str}.
    """
    import openpyxl

    workbook = openpyxl.load_workbook(arquivo, data_only=True)
    aba = workbook.worksheets[0]

    linhas = []

    for linha in aba.iter_rows(min_row=2, values_only=False):
        nome_celula = linha[0].value if len(linha) > 0 else None
        data_celula = linha[1].value if len(linha) > 1 else None

        nome = str(nome_celula).strip() if nome_celula else None
        if not nome:
            continue

        data_convertida = _converter_valor_data(data_celula)

        linhas.append({
            "nome_empresa": nome,
            "data_vencimento": data_convertida,
            "valor_original": str(data_celula) if data_celula is not None else "",
        })

    return linhas