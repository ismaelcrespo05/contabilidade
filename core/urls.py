from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    # Login e Logout
    path("login/", views.PainelLoginView.as_view(), name="login"),
    path("logout/", views.PainelLogoutView.as_view(), name="logout"),

    # Painel — dashboard
    path("painel/", views.painel_dashboard, name="painel_dashboard"),

    # Exportação para Excel
    path("painel/exportar/excel/", views.exportar_excel, name="exportar_excel"),
    
    # Cargar pdf
    path("painel/comprovantes/importar/", views.importar_comprovante, name="importar_comprovante"),
    path("painel/comprovantes/confirmar/", views.confirmar_comprovante, name="confirmar_comprovante"),
    # Empresas
    path("painel/empresas/", views.EmpresaListView.as_view(), name="empresa_list"),
    path("painel/empresas/nova/", views.nova_empresa, name="nova_empresa"),
    path("painel/empresas/<int:pk>/editar/", views.editar_empresa, name="editar_empresa"),
    path("painel/empresas/<int:pk>/excluir/", views.EmpresaDeleteView.as_view(), name="excluir_empresa"),

    # Catálogos (tipos, regimes, impostos, cnae, obrigações)
    path("painel/catalogos/<slug:slug>/", views.catalogo_list, name="catalogo_list"),
    path("painel/catalogos/<slug:slug>/novo/", views.catalogo_form, name="catalogo_novo"),
    path("painel/catalogos/<slug:slug>/<int:pk>/editar/", views.catalogo_form, name="catalogo_editar"),
    path("painel/catalogos/<slug:slug>/<int:pk>/excluir/", views.catalogo_delete, name="catalogo_excluir"),

    # Competências (por empresa)
    path("painel/empresas/<int:empresa_pk>/competencias/", views.competencia_list, name="competencia_list"),
    path("painel/empresas/<int:empresa_pk>/competencias/nova/", views.nova_competencia, name="nova_competencia"),
    path("painel/competencias/<int:pk>/", views.competencia_detail, name="competencia_detail"),
    path("painel/competencias/<int:pk>/excluir/", views.CompetenciaDeleteView.as_view(), name="excluir_competencia"),

    # Apurações de imposto (dentro de uma competência)
    path("painel/competencias/<int:competencia_pk>/apuracoes/nova/", views.nova_apuracao, name="nova_apuracao"),
    path("painel/apuracoes/<int:pk>/editar/", views.editar_apuracao, name="editar_apuracao"),
    path("painel/apuracoes/<int:pk>/excluir/", views.ApuracaoDeleteView.as_view(), name="excluir_apuracao"),
    
    # Documentos
    path("painel/documentos/", views.documento_list, name="documento_list"),
    path("painel/documentos/novo/", views.novo_documento, name="novo_documento"),
    path("painel/documentos/<int:pk>/revisar/", views.revisar_documento, name="revisar_documento"),
]