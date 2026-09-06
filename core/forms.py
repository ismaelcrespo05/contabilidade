from django import forms
from .models import  Empresa, Competencia, ApuracaoImposto, Documento, PerfilUsuario, LancamentoContabil, Certificado, ConfiguracaoSistema
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class EmpresaForm(forms.ModelForm):

    class Meta:
        model = Empresa

        fields = [
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "tipo_empresa",
            "regime_tributario",
            "cnae_principal",
            "impostos",
            "obrigacoes_acessorias",        
        ]

        labels = {
            "cnpj": "CNPJ",
            "razao_social": "Razão Social",
            "nome_fantasia": "Nome Fantasia",
            "tipo_empresa": "Tipo de empresa",
            "regime_tributario": "Regime tributário",
            "cnae_principal": "CNAE principal",
            "impostos": "Impostos",
            "obrigacoes_acessorias": "Obrigações acessórias",
        }

        widgets = {
            "cnpj": forms.TextInput(attrs={"placeholder": "00.000.000/0000-00"}),
            "razao_social": forms.TextInput(attrs={"placeholder": "Razão social da empresa"}),
            "nome_fantasia": forms.TextInput(attrs={"placeholder": "Nome fantasia"}),
            # Uma empresa pode ter vários impostos e obrigações ao mesmo
            # tempo, então usamos checkboxes em vez de um select múltiplo.
            "impostos": forms.CheckboxSelectMultiple(),
            "obrigacoes_acessorias": forms.CheckboxSelectMultiple(),
        }


class CompetenciaForm(forms.ModelForm):

    class Meta:
        model = Competencia
        fields = ["ano", "mes"]
        labels = {"ano": "Ano", "mes": "Mês"}
        widgets = {
            "ano": forms.NumberInput(attrs={"placeholder": "2026"}),
            "mes": forms.Select(choices=[(m, f"{m:02d}") for m in range(1, 13)]),
        }


class ApuracaoImpostoForm(forms.ModelForm):

    class Meta:
        model = ApuracaoImposto
        fields = ["imposto", "valor", "data_vencimento", "status", "data_pagamento", "observacao"]
        labels = {
            "imposto": "Imposto",
            "valor": "Valor",
            "data_vencimento": "Vencimento",
            "status": "Status",
            "data_pagamento": "Data de pagamento",
            "observacao": "Observação",
        }
        widgets = {
            "valor": forms.NumberInput(attrs={"step": "0.01", "placeholder": "0,00"}),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}),
            "data_pagamento": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }
        
class DocumentoForm(forms.ModelForm):
    """
    Formulário de revisão (RF-21): os dados aqui vêm pré-preenchidos pela
    extração automática, mas o usuário pode corrigir qualquer campo antes
    de confirmar.
    """

    class Meta:
        model = Documento

        fields = [
            "tipo_documento",
            "empresa",
            "fornecedor",
            "cnpj_emitente",
            "razao_social_emitente",
            "cnpj_destinatario",
            "numero_documento",
            "data_emissao",
            "valor_total",
        ]

        labels = {
            "tipo_documento": "Tipo de documento",
            "empresa": "Empresa vinculada",
            "fornecedor": "Fornecedor identificado",
            "cnpj_emitente": "CNPJ do emitente",
            "razao_social_emitente": "Razão social do emitente",
            "cnpj_destinatario": "CNPJ do destinatário",
            "numero_documento": "Número do documento",
            "data_emissao": "Data de emissão",
            "valor_total": "Valor total",
        }

        widgets = {
            "data_emissao": forms.DateInput(attrs={"type": "date"}),
            "valor_total": forms.NumberInput(attrs={"step": "0.01"}),
        }
        
class NovoUsuarioForm(UserCreationForm):
    """
    RF-41: cadastro de usuário. Reaproveita o UserCreationForm do Django
    (já valida senha, confirmação de senha, username único) e só agrega
    o campo de papel (RF-42).
    """

    papel = forms.ChoiceField(
        choices=PerfilUsuario.PAPEL_CHOICES,
        label="Papel",
        initial=PerfilUsuario.CONSULTA,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class EditarUsuarioForm(forms.ModelForm):
    """
    RF-41/RF-42: edita e-mail, se o usuário está ativo, e o papel dele.
    Não mexe em senha aqui — troca de senha é um fluxo separado.
    """

    papel = forms.ChoiceField(choices=PerfilUsuario.PAPEL_CHOICES, label="Papel")

    class Meta:
        model = User
        fields = ["email", "is_active"]
        labels = {"is_active": "Usuário ativo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "perfil"):
            self.fields["papel"].initial = self.instance.perfil.papel

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
            perfil.papel = self.cleaned_data["papel"]
            perfil.save()
        return usuario      
    
class LancamentoContabilForm(forms.ModelForm):
    """
    RF-34: formulário de revisão do lançamento. Só é usado enquanto o
    lançamento está em RASCUNHO.
    """

    class Meta:
        model = LancamentoContabil

        fields = [
            "data_lancamento",
            "historico",
            "conta_debito",
            "conta_credito",
            "valor",
        ]

        labels = {
            "data_lancamento": "Data do lançamento",
            "historico": "Histórico",
            "conta_debito": "Conta débito",
            "conta_credito": "Conta crédito",
            "valor": "Valor",
        }

        widgets = {
            "data_lancamento": forms.DateInput(attrs={"type": "date"}),
            "historico": forms.TextInput(attrs={"placeholder": "Ex: Compra conforme NF nº 123456"}),
            "conta_debito": forms.TextInput(attrs={"placeholder": "Ex: Despesas com mercadorias"}),
            "conta_credito": forms.TextInput(attrs={"placeholder": "Ex: Fornecedores a pagar"}),
            "valor": forms.NumberInput(attrs={"step": "0.01"}),
        }
        
class CertificadoForm(forms.ModelForm):

    class Meta:
        model = Certificado
        fields = ["nome_empresa", "data_vencimento", "empresa", "nome", "observacao"]

        labels = {
            "nome_empresa": "Nome (titular do certificado)",
            "data_vencimento": "Data de vencimento",
            "empresa": "Vincular a uma empresa cadastrada (opcional)",
            "nome": "Tipo de certificado",
            "observacao": "Observação",
        }

        widgets = {
            "nome_empresa": forms.TextInput(attrs={"placeholder": "Ex: CBS FILHO", "autofocus": True}),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}),
            "nome": forms.TextInput(attrs={"placeholder": "Ex: e-CNPJ A1"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

class ConfiguracaoSistemaForm(forms.ModelForm):

    class Meta:
        model = ConfiguracaoSistema
        fields = [
            "dias_alerta_certificado", "dias_alerta_obrigacao", "dias_alerta_imposto",
            "notificacoes_sistema_ativas", "notificacoes_email_ativas",
            "notificar_obrigacoes_proximas", "notificar_obrigacoes_vencidas",
            "notificar_certificados_proximos", "notificar_erros_processamento",
        ]
        labels = {
            "dias_alerta_certificado": "Dias de antecedência — Certificados",
            "dias_alerta_obrigacao": "Dias de antecedência — Obrigações",
            "dias_alerta_imposto": "Dias de antecedência — Impostos",
        }
        widgets = {
            "dias_alerta_certificado": forms.NumberInput(attrs={"min": 1}),
            "dias_alerta_obrigacao": forms.NumberInput(attrs={"min": 1}),
            "dias_alerta_imposto": forms.NumberInput(attrs={"min": 1}),
        }

# Formulário mínimo (só nome + data) usado na carga rápida em lote 
CertificadoRapidoFormSet = forms.modelformset_factory(
    Certificado,
    fields=["nome_empresa", "data_vencimento"],
    extra=15,
    widgets={
        "nome_empresa": forms.TextInput(attrs={"placeholder": "Nome"}),
        "data_vencimento": forms.DateInput(attrs={"type": "date"}),
    },
)


class ImportarCertificadosExcelForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo Excel (.xlsx)")
    
class ImportarRotinasForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo Excel (.xlsx)")
    ano = forms.IntegerField(
        label="Ano padrão (usado só quando a planilha não traz o ano nas datas)",
        min_value=2000, max_value=2100
    )    