from django.db.models import Q


def aplicar_busca_e_ordenacao(request, queryset, campos_busca, opcoes_ordenacao, padrao=None):
    """
    Adiciona busca por texto livre (?q=) e ordenação (?ordenar=chave) a
    qualquer queryset — reutilizável em qualquer tela de listagem
    (certificados, empresas, documentos, etc.), sem duplicar a lógica.

    campos_busca: lista de nomes de campo (aceita __ para relações) onde
        o texto digitado é procurado, ex: ["nome_empresa", "nome"].
    opcoes_ordenacao: dict {chave_usada_na_url: campo_orm_para_order_by},
        ex: {"nome": "nome_empresa", "vencimento": "data_vencimento"}.
    padrao: qual chave de opcoes_ordenacao usar quando a URL não pede
        nenhuma — se omitido, usa a primeira do dict.

    Retorna (queryset_filtrado_e_ordenado, termo_buscado, chave_ordenacao_atual).
    """
    termo = request.GET.get("q", "").strip()

    if termo:
        condicao = Q()
        for campo in campos_busca:
            condicao |= Q(**{f"{campo}__icontains": termo})
        queryset = queryset.filter(condicao)

    chave_padrao = padrao or next(iter(opcoes_ordenacao))
    ordenar = request.GET.get("ordenar", chave_padrao)

    if ordenar not in opcoes_ordenacao:
        ordenar = chave_padrao

    queryset = queryset.order_by(opcoes_ordenacao[ordenar])

    return queryset, termo, ordenar