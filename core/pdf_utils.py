import re


def extrair_dados_recibo(arquivo):
    """
    Lê um PDF de recibo de entrega (SPED, EFD, etc.) e tenta extrair:
      - cnpj: no formato 00.000.000/0000-00
      - periodo_inicio / periodo_fim: no formato DD/MM/AAAA
    """
    from pypdf import PdfReader

    reader = PdfReader(arquivo)
    texto = "\n".join(pagina.extract_text() or "" for pagina in reader.pages)

    cnpj_match = re.search(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto)
    periodo_match = re.search(
        r"(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})", texto
    )

    return {
        "cnpj": cnpj_match.group(1) if cnpj_match else None,
        "periodo_inicio": periodo_match.group(1) if periodo_match else None,
        "periodo_fim": periodo_match.group(2) if periodo_match else None,
        "texto": texto,
    }
    
def _extrair_secao(texto, inicio_regex, fim_regex=None):
    """Recorta o trecho do texto entre um cabeçalho e o próximo (ou o fim)."""
    m_inicio = re.search(inicio_regex, texto, re.IGNORECASE)
    if not m_inicio:
        return ""

    inicio = m_inicio.end()

    if fim_regex:
        m_fim = re.search(fim_regex, texto[inicio:], re.IGNORECASE)
        fim = inicio + m_fim.start() if m_fim else len(texto)
    else:
        fim = len(texto)

    return texto[inicio:fim]


def extrair_dados_documento(arquivo):
    """
    Extração genérica para qualquer documento fiscal em PDF (nota fiscal,
    boleto, etc. — RF-08). Como o layout varia muito de documento para
    documento, tudo aqui é uma *melhor tentativa*: o usuário sempre revisa
    e corrige na tela seguinte (RF-21), então preferimos arriscar um
    palpite razoável a não preencher nada.
    """
    from pypdf import PdfReader

    reader = PdfReader(arquivo)
    texto = "\n".join(pagina.extract_text() or "" for pagina in reader.pages)

    cnpjs = list(dict.fromkeys(
        re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    ))

    secao_emitente = _extrair_secao(texto, r"EMITENTE", r"DESTINAT[ÁA]RIO")
    secao_destinatario = _extrair_secao(texto, r"DESTINAT[ÁA]RIO", r"Valor\s*Total")

    def _razao_social(secao):
        m = re.search(r"Raz[ãa]o\s*Social[:\s]*([^\n]+)", secao, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def _cnpj_da_secao(secao):
        m = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", secao)
        return m.group(0) if m else None

    cnpj_emitente = _cnpj_da_secao(secao_emitente) or (cnpjs[0] if cnpjs else None)
    cnpj_destinatario = _cnpj_da_secao(secao_destinatario) or (
        cnpjs[1] if len(cnpjs) > 1 else None
    )

    valor_match = re.search(
        r"Valor\s*Total[:\s]*R?\$?\s*([\d.,]+)", texto, re.IGNORECASE
    )
    data_match = re.search(
        r"(?:Data\s*de\s*Emiss[ãa]o|Emiss[ãa]o|Data)[:\s]*(\d{2}/\d{2}/\d{4})",
        texto, re.IGNORECASE
    )
    numero_match = re.search(
        r"N[úu]mero[:\s]*([\w./-]+)", texto, re.IGNORECASE
    )

    impostos_conhecidos = ["ICMS", "ISS", "PIS", "COFINS", "IPI", "IR", "CSLL"]
    impostos_encontrados = []
    for nome in impostos_conhecidos:
        m = re.search(rf"\b{nome}\b[:\s]*R?\$?\s*([\d.,]+)", texto, re.IGNORECASE)
        if m:
            impostos_encontrados.append({"nome": nome, "valor": m.group(1)})

    return {
        "cnpjs": cnpjs,
        "cnpj_emitente": cnpj_emitente,
        "razao_social_emitente": _razao_social(secao_emitente),
        "cnpj_destinatario": cnpj_destinatario,
        "razao_social_destinatario": _razao_social(secao_destinatario),
        "valor_total": valor_match.group(1) if valor_match else None,
        "data_emissao": data_match.group(1) if data_match else None,
        "numero_documento": numero_match.group(1) if numero_match else None,
        "impostos": impostos_encontrados,
        "texto": texto,
    }


def parse_valor_brl(texto):
    """Converte '1.234,56' -> Decimal('1234.56'). Retorna None se inválido."""
    from decimal import Decimal, InvalidOperation

    if not texto:
        return None

    limpo = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation:
        return None


def parse_data_br(texto):
    """Converte 'DD/MM/AAAA' -> date. Retorna None se inválido."""
    from datetime import datetime

    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None    