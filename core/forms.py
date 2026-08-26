from django import forms

from .models import Empresa, Competencia, ApuracaoImposto, Documento


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
            "cnpj_emitente",
            "razao_social_emitente",
            "cnpj_destinatario",
            "numero_documento",
            "data_emissao",
            "valor_total",
        ]

        widgets = {
            "data_emissao": forms.DateInput(attrs={"type": "date"}),
            "valor_total": forms.NumberInput(attrs={"step": "0.01"}),
        }        