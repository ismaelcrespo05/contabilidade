from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """
    Papel do usuário dentro do sistema (RF-42). Cada User do Django ganha
    automaticamente um PerfilUsuario (via signal, logo abaixo) assim que
    é criado — superusuários viram Administrador por padrão, os demais
    começam como Consulta (o papel mais restrito).
    """

    ADMINISTRADOR = "ADMIN"
    CONTADOR = "CONTADOR"
    AUXILIAR = "AUXILIAR"
    CONSULTA = "CONSULTA"

    PAPEL_CHOICES = [
        (ADMINISTRADOR, "Administrador"),
        (CONTADOR, "Contador"),
        (AUXILIAR, "Auxiliar"),
        (CONSULTA, "Consulta"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil"
    )

    papel = models.CharField(
        max_length=20,
        choices=PAPEL_CHOICES,
        default=CONSULTA
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_papel_display()})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        papel_padrao = (
            PerfilUsuario.ADMINISTRADOR if instance.is_superuser
            else PerfilUsuario.CONSULTA
        )
        PerfilUsuario.objects.get_or_create(user=instance, defaults={"papel": papel_padrao})


class TipoEmpresa(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class RegimeTributario(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Imposto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class CNAE(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField()

    dia_vencimento = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Dia do mês em que essa obrigação normalmente vence (ex: 25)."
    )
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class ObrigacaoAcessoria(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True)
    
    dia_vencimento = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Dia do mês em que essa obrigação normalmente vence (ex: 25)."
    )

    def __str__(self):
        return self.nome


class Empresa(models.Model):
    cnpj = models.CharField(max_length=18, unique=True)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)

    tipo_empresa = models.ForeignKey(
        TipoEmpresa,
        on_delete=models.PROTECT
    )

    regime_tributario = models.ForeignKey(
        RegimeTributario,
        on_delete=models.PROTECT
    )

    cnae_principal = models.ForeignKey(
        CNAE,
        on_delete=models.PROTECT
    )

    impostos = models.ManyToManyField(
        Imposto,
        blank=True
    )

    obrigacoes_acessorias = models.ManyToManyField(
        ObrigacaoAcessoria,
        blank=True
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.razao_social


class Competencia(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="competencias"
    )

    ano = models.PositiveIntegerField()

    mes = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "ano", "mes"],
                name="empresa_competencia_unica"
            )
        ]

    def __str__(self):
        return f"{self.empresa} - {self.mes:02d}/{self.ano}"


class ApuracaoImposto(models.Model):

    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("INFORMADO", "Informado ao cliente"),
        ("PAGO", "Pago"),
        ("ATRASADO", "Atrasado"),
        ("DISPENSADO", "Dispensado"),
    ]

    competencia = models.ForeignKey(
        Competencia,
        on_delete=models.CASCADE,
        related_name="apuracoes_imposto"
    )

    imposto = models.ForeignKey(
        Imposto,
        on_delete=models.PROTECT,
        related_name="apuracoes"
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    data_vencimento = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDENTE"
    )

    data_pagamento = models.DateField(
        null=True,
        blank=True
    )

    observacao = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.imposto} - {self.competencia}"
    
class CumprimentoObrigacao(models.Model):
    """
    Marca se uma obrigação acessória (rotina fiscal: MIT, SPED, EFD, etc.)
    foi cumprida em uma determinada competência (mês/ano) de uma empresa.
    Equivale, na planilha antiga, à "bolinha" (semáforo) de cada mês:
    3 = Em dia (verde), 2 = Risco de atraso (amarelo), 1 = Atrasada (vermelho).
    """

    STATUS_EM_DIA = 3
    STATUS_RISCO = 2
    STATUS_ATRASADA = 1

    STATUS_CHOICES = [
        (STATUS_EM_DIA, "Em dia"),
        (STATUS_RISCO, "Risco de atraso"),
        (STATUS_ATRASADA, "Atrasada"),
    ]

    competencia = models.ForeignKey(
        Competencia, on_delete=models.CASCADE,
        related_name="cumprimentos_obrigacao"
    )

    obrigacao = models.ForeignKey(
        ObrigacaoAcessoria, on_delete=models.PROTECT,
        related_name="cumprimentos"
    )

    cumprido = models.BooleanField(default=False)
    data_cumprimento = models.DateField(null=True, blank=True)

    # PDF do recibo de entrega (ex: recibo de EFD/SPED) que comprova
    # o cumprimento dessa obrigação nesse mês.
    comprovante = models.FileField(
        upload_to="comprovantes/%Y/%m/",
        null=True,
        blank=True
    )
    
    # Se preenchido, este valor manda e o semáforo automático é ignorado.
    status_manual = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Deixe em branco para o sistema calcular sozinho pela data de vencimento."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["competencia", "obrigacao"],
                name="competencia_obrigacao_unica"
            )
        ]

    def __str__(self):
        status = "cumprida" if self.cumprido else "pendente"
        return f"{self.obrigacao} - {self.competencia} ({status})"

    def status_calculado(self):
        """
        Retorna 3 (em dia), 2 (risco) ou 1 (atrasada).
        Prioridade: status_manual > cumprido > data de vencimento.
        """
        if self.status_manual:
            return self.status_manual

        if self.cumprido:
            return self.STATUS_EM_DIA

        import calendar
        from datetime import date

        dia = self.obrigacao.dia_vencimento or 28
        ultimo_dia_do_mes = calendar.monthrange(
            self.competencia.ano, self.competencia.mes
        )[1]
        vencimento = date(
            self.competencia.ano,
            self.competencia.mes,
            min(dia, ultimo_dia_do_mes)
        )

        hoje = date.today()

        if hoje > vencimento:
            return self.STATUS_ATRASADA

        if (vencimento - hoje).days <= 5:
            return self.STATUS_RISCO

        return self.STATUS_EM_DIA

    def status_calculado_display(self):
        valores = dict(self.STATUS_CHOICES)
        return valores.get(self.status_calculado(), "")

class Fornecedor(models.Model):
    """
    Pessoa jurídica que fornece produtos/serviços — conceitualmente
    separado de Empresa (a empresa administrada pelo escritório) e de
    Emitente/Destinatário (papéis que variam por documento). RF-32.
    """

    cnpj = models.CharField(max_length=18, unique=True)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.razao_social    

class Documento(models.Model):
    """
    Documento fiscal genérico (nota fiscal, recibo, boleto, etc.). Existe
    independente de uma Empresa cadastrada — pode ficar "solto" (RF-16)
    até que o usuário decida associá-lo a uma empresa já cadastrada ou
    cadastrar uma nova a partir dos dados extraídos (RF-13/RF-14).
    """

    TIPO_NFE = "NFE"
    TIPO_RECIBO_OBRIGACAO = "RECIBO_OBRIGACAO"
    TIPO_BOLETO = "BOLETO"
    TIPO_OUTRO = "OUTRO"

    TIPO_CHOICES = [
        (TIPO_NFE, "Nota Fiscal"),
        (TIPO_RECIBO_OBRIGACAO, "Recibo de Obrigação Acessória"),
        (TIPO_BOLETO, "Boleto"),
        (TIPO_OUTRO, "Outro"),
    ]

    arquivo = models.FileField(upload_to="documentos/%Y/%m/")

    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_OUTRO
    )

    # Empresa administrada à qual esse documento foi associado. Pode ficar
    # em branco (RF-05, RF-14, RF-16): nem todo documento precisa estar
    # ligado a uma empresa cadastrada.
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos"
    )
    
    # Fornecedor identificado automaticamente pelo CNPJ do emitente
    # (RF-31), quando esse CNPJ não pertence à empresa administrada.
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos"
    )

    # Dados extraídos automaticamente do PDF (RF-08). Tudo aqui pode ser
    # corrigido manualmente na revisão (RF-21) — por isso são campos
    # normais, editáveis, e não só um JSON fixo.
    cnpj_emitente = models.CharField(max_length=18, blank=True)
    razao_social_emitente = models.CharField(max_length=200, blank=True)
    cnpj_destinatario = models.CharField(max_length=18, blank=True)

    numero_documento = models.CharField(max_length=50, blank=True)
    data_emissao = models.DateField(null=True, blank=True)
    valor_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )

    # Dados adicionais que a extração encontrar (impostos detectados,
    # lista de CNPJs candidatos, texto bruto, etc.) — guardados à parte
    # para não precisar de uma coluna nova cada vez que a extração melhora.
    dados_extraidos = models.JSONField(default=dict, blank=True)

    revisado = models.BooleanField(
        default=False,
        help_text="Marca se o usuário já conferiu/corrigiu os dados extraídos."
    )

    data_upload = models.DateTimeField(auto_now_add=True)

    @property
    def papel_empresa(self):
        """
        Não guardamos o papel (emitente/destinatário) como campo à parte
        para não arriscar ficar desatualizado — comparamos o CNPJ da
        empresa vinculada com os CNPJs extraídos do documento (RF-09).
        """
        if not self.empresa:
            return None
        if self.empresa.cnpj == self.cnpj_emitente:
            return "Emitente"
        if self.empresa.cnpj == self.cnpj_destinatario:
            return "Destinatário"
        return "Não identificado"

    def __str__(self):
        return self.numero_documento or f"Documento #{self.pk}"    
    
class LancamentoContabil(models.Model):
    """
    Lançamento contábil gerado a partir de um Documento processado
    (RF-33). Fica como RASCUNHO até o usuário revisar e confirmar
    (RF-34, RF-35) — depois de confirmado, não pode mais ser editado
    nem excluído, para manter o histórico íntegro (RF-36).
    """

    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_CONFIRMADO = "CONFIRMADO"

    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho — aguardando revisão"),
        (STATUS_CONFIRMADO, "Confirmado"),
    ]

    documento = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos"
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="lancamentos"
    )

    data_lancamento = models.DateField()
    historico = models.CharField(max_length=255)
    conta_debito = models.CharField(max_length=100, blank=True)
    conta_credito = models.CharField(max_length=100, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RASCUNHO
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_confirmacao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.historico} — R$ {self.valor} ({self.get_status_display()})"    

class ConfiguracaoSistema(models.Model):
    """
    Configurações gerais do sistema. Usamos um único registro (padrão
    "singleton" via obter()) em vez de espalhar constantes pelo código —
    assim, mudar um parâmetro aqui vale para o sistema inteiro na hora.
    """

    dias_alerta_certificado = models.PositiveIntegerField(
        default=30,
        help_text=(
            "Quantos dias antes do vencimento um certificado já deve "
            "aparecer em amarelo (próximo a vencer)."
        )
    )

    @classmethod
    def obter(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configurações do sistema"


class Certificado(models.Model):
    """
    Certificado digital (e-CNPJ, e-CPF, etc.), com data de vencimento.
    O titular é sempre um texto livre (nome_empresa) — não exige que
    exista um cadastro de Empresa. Vincular a uma Empresa cadastrada é
    opcional, só para quando fizer sentido.
    """

    STATUS_SEM_DATA = 0
    STATUS_VENCIDO = 1
    STATUS_PROXIMO = 2
    STATUS_EM_DIA = 3

    nome_empresa = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nome do titular do certificado — não precisa estar cadastrado no sistema."
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados",
        help_text="Opcional — só selecione se essa empresa já estiver cadastrada."
    )

    nome = models.CharField(
        max_length=150,
        blank=True,
        default="Certificado Digital",
        help_text="Ex: e-CNPJ A1 (opcional)"
    )

    data_vencimento = models.DateField(
        null=True,
        blank=True,
        help_text="Deixe em branco se ainda não souber a data (aparece para completar depois)."
    )

    observacao = models.TextField(blank=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    def status_calculado(self):
        from datetime import date

        if not self.data_vencimento:
            return self.STATUS_SEM_DATA

        hoje = date.today()

        if hoje > self.data_vencimento:
            return self.STATUS_VENCIDO

        dias_restantes = (self.data_vencimento - hoje).days
        dias_alerta = ConfiguracaoSistema.obter().dias_alerta_certificado

        if dias_restantes <= dias_alerta:
            return self.STATUS_PROXIMO

        return self.STATUS_EM_DIA

    def status_calculado_display(self):
        return {
            self.STATUS_SEM_DATA: "Sem data",
            self.STATUS_VENCIDO: "Vencido",
            self.STATUS_PROXIMO: "Próximo a vencer",
            self.STATUS_EM_DIA: "Em dia",
        }.get(self.status_calculado(), "")

    def __str__(self):
        return f"{self.nome_empresa} — {self.nome}"