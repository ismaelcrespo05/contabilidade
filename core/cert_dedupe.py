import re


def extrair_cnpj_do_texto(texto):
    """Extrai um CNPJ (14 dígitos) de dentro de um texto qualquer —
    usado para achar o CNPJ dentro do CN do certificado (formato
    "NOME:CNPJ")."""
    if not texto:
        return None
    m = re.search(r"(\d{14})", texto.replace(".", "").replace("/", "").replace("-", ""))
    return m.group(1) if m else None


def buscar_certificado_relacionado(nome_empresa, data_vencimento, cnpj=None):
    """
    Compara o certificado novo com os já cadastrados do mesmo titular
    (mesmo CNPJ, ou mesmo nome quando não há CNPJ disponível):

      - Mesmo titular + mesma data de vencimento  -> ("exato", existente)
        É literalmente o mesmo arquivo sendo importado de novo.

      - Mesmo titular + data de vencimento DIFERENTE -> ("atualizacao", existente)
        É uma renovação: o certificado novo substitui o antigo.

      - Nenhum encontrado -> (None, None)
    """
    from .models import Certificado

    if cnpj:
        mesmo_titular = Certificado.objects.filter(observacao__icontains=cnpj)
    else:
        mesmo_titular = Certificado.objects.filter(nome_empresa__iexact=nome_empresa.strip())

    exato = mesmo_titular.filter(data_vencimento=data_vencimento).first()
    if exato:
        return "exato", exato

    atualizacao = mesmo_titular.exclude(data_vencimento=data_vencimento).first()
    if atualizacao:
        return "atualizacao", atualizacao

    return None, None