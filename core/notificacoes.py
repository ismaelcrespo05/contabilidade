def gerar_notificacoes():
    """
    Varre obrigações e certificados pendentes e cria uma Notificacao
    para cada situação nova — respeitando exatamente quais tipos o
    usuário deixou ligados em Configurações. Idempotente.
    """
    from .models import ConfiguracaoSistema, Notificacao, CumprimentoObrigacao, Certificado

    config = ConfiguracaoSistema.obter()

    if not config.notificacoes_sistema_ativas and not config.notificacoes_email_ativas:
        return 0

    criadas = 0

    if config.notificar_obrigacoes_vencidas or config.notificar_obrigacoes_proximas:
        cumprimentos = CumprimentoObrigacao.objects.filter(cumprido=False).select_related(
            "competencia__empresa", "obrigacao"
        )

        for cumprimento in cumprimentos:
            status = cumprimento.status_calculado()

            if status == 1 and config.notificar_obrigacoes_vencidas:
                tipo = Notificacao.TIPO_OBRIGACAO_VENCIDA
                mensagem = (
                    f"Obrigação vencida: {cumprimento.obrigacao.nome} — "
                    f"{cumprimento.competencia.empresa.razao_social}"
                )
            elif status == 2 and config.notificar_obrigacoes_proximas:
                tipo = Notificacao.TIPO_OBRIGACAO_PROXIMA
                mensagem = (
                    f"Obrigação próxima do vencimento: {cumprimento.obrigacao.nome} — "
                    f"{cumprimento.competencia.empresa.razao_social}"
                )
            else:
                continue

            criada = _registrar_notificacao(
                config,
                chave=f"obrigacao:{cumprimento.id}:{tipo}",
                tipo=tipo,
                mensagem=mensagem,
                link=f"/painel/competencias/{cumprimento.competencia_id}/",
            )
            if criada:
                criadas += 1

    if config.notificar_certificados_proximos:
        for certificado in Certificado.objects.filter(data_vencimento__isnull=False):
            status = certificado.status_calculado()

            if status not in (1, 2):
                continue

            tipo = Notificacao.TIPO_CERTIFICADO_PROXIMO
            situacao = "vencido" if status == 1 else "próximo de vencer"
            mensagem = f"Certificado {situacao}: {certificado.nome_empresa}"

            criada = _registrar_notificacao(
                config,
                chave=f"certificado:{certificado.id}:{status}",
                tipo=tipo,
                mensagem=mensagem,
                link="/painel/certificados/",
            )
            if criada:
                criadas += 1

    return criadas


def registrar_erro_processamento(mensagem, link=""):
    """
    Chame isso de qualquer lugar do sistema que capture um erro relevante
    (ex: falha ao ler um PDF, uma planilha malformada) para que ele
    também apareça como notificação.
    """
    from .models import ConfiguracaoSistema, Notificacao
    from django.utils import timezone

    config = ConfiguracaoSistema.obter()
    if not config.notificar_erros_processamento:
        return

    chave = f"erro:{timezone.now().timestamp()}"
    _registrar_notificacao(
        config, chave=chave, tipo=Notificacao.TIPO_ERRO_PROCESSAMENTO,
        mensagem=mensagem, link=link,
    )


def _registrar_notificacao(config, chave, tipo, mensagem, link):
    from .models import Notificacao
    from django.core.mail import send_mail

    _, criada = Notificacao.objects.get_or_create(
        chave=chave,
        defaults={"tipo": tipo, "mensagem": mensagem, "link": link},
    )

    if criada and config.notificacoes_email_ativas and config.email_notificacoes:
        send_mail(
            subject=f"TRINUS — {mensagem}",
            message=mensagem,
            from_email=None,
            recipient_list=[config.email_notificacoes],
            fail_silently=True,
        )

    return criada