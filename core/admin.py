from django.contrib import admin

from .models import (
    TipoEmpresa,
    RegimeTributario,
    Imposto,
    CNAE,
    ObrigacaoAcessoria,
    Empresa,
    Competencia,
    ApuracaoImposto,
)


@admin.register(TipoEmpresa)
class TipoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(RegimeTributario)
class RegimeTributarioAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Imposto)
class ImpostoAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao")
    search_fields = ("nome",)


@admin.register(CNAE)
class CNAEAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao")
    search_fields = ("codigo", "descricao")


@admin.register(ObrigacaoAcessoria)
class ObrigacaoAcessoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao")
    search_fields = ("nome",)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "razao_social",
        "cnpj",
        "tipo_empresa",
        "regime_tributario",
        "cnae_principal",
    )

    search_fields = (
        "razao_social",
        "nome_fantasia",
        "cnpj",
    )

    list_filter = (
        "tipo_empresa",
        "regime_tributario",
    )

    filter_horizontal = (
        "impostos",
        "obrigacoes_acessorias",
    )


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "mes",
        "ano",
    )

    list_filter = (
        "ano",
        "mes",
    )

    search_fields = (
        "empresa__razao_social",
        "empresa__cnpj",
    )


@admin.register(ApuracaoImposto)
class ApuracaoImpostoAdmin(admin.ModelAdmin):
    list_display = (
        "competencia",
        "imposto",
        "valor",
        "data_vencimento",
        "status",
        "data_pagamento",
    )

    list_filter = (
        "status",
        "imposto",
    )

    search_fields = (
        "competencia__empresa__razao_social",
        "competencia__empresa__cnpj",
        "imposto__nome",
    )