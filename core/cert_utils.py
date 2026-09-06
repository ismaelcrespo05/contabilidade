EXTENSOES_CERTIFICADO = (".pfx", ".p12")


def eh_arquivo_certificado(nome_arquivo):
    """Filtra pelo nome — usado para ignorar qualquer arquivo que não
    seja um certificado quando o usuário sobe uma pasta inteira."""
    return nome_arquivo.lower().endswith(EXTENSOES_CERTIFICADO)


def extrair_dados_certificado(conteudo, senha):
    """
    Lê um arquivo .pfx/.p12 (em bytes) usando a senha informada e
    retorna o nome do titular e a data de vencimento reais, gravados
    dentro do próprio certificado — nada disso precisa ser digitado.

    Levanta ValueError se a senha estiver errada ou o arquivo não for
    um certificado válido.
    """
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID

    senha_bytes = senha.encode() if senha else None
    _chave, certificado, _cadeia = pkcs12.load_key_and_certificates(conteudo, senha_bytes)

    if certificado is None:
        raise ValueError("Não foi possível ler o certificado desse arquivo.")

    atributos_cn = certificado.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    nome_completo = atributos_cn[0].value if atributos_cn else ""

    # Certificados e-CNPJ/e-CPF brasileiros costumam gravar o nome no
    # formato "NOME DA EMPRESA:CNPJ" — separamos só o nome.
    nome_empresa = nome_completo.split(":")[0].strip() if nome_completo else ""

    try:
        data_vencimento = certificado.not_valid_after_utc.date()
    except AttributeError:
        data_vencimento = certificado.not_valid_after.date()

    return {
        "nome_empresa": nome_empresa or "Certificado sem nome identificado",
        "nome_completo_cn": nome_completo,
        "data_vencimento": data_vencimento,
    }