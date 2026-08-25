from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DeleteView
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import EmpresaForm, CompetenciaForm, ApuracaoImpostoForm
from .models import (
    TipoEmpresa, RegimeTributario, Imposto, CNAE, ObrigacaoAcessoria,
    Empresa, Competencia, ApuracaoImposto, CumprimentoObrigacao,
)


def inicio(request):
    return render(request, "core/inicio.html")


# ---------------------------------------------------------------------
# Login / Logout personalizados (substituem o login do admin do Django)
# ---------------------------------------------------------------------
class PainelLoginView(auth_views.LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


class PainelLogoutView(auth_views.LogoutView):
    next_page = "login"


# ---------------------------------------------------------------------
# Registro de catálogos administrados pelo painel.
# ---------------------------------------------------------------------
CATALOGOS = {
    "tipos-empresa": {
        "model": TipoEmpresa, "titulo": "Tipos de Empresa",
        "titulo_singular": "Tipo de Empresa", "fields": ["nome"],
        "columns": [("nome", "Nome")],
    },
    "regimes": {
        "model": RegimeTributario, "titulo": "Regimes Tributários",
        "titulo_singular": "Regime Tributário", "fields": ["nome"],
        "columns": [("nome", "Nome")],
    },
    "impostos": {
        "model": Imposto, "titulo": "Impostos",
        "titulo_singular": "Imposto", "fields": ["nome", "descricao"],
        "columns": [("nome", "Nome"), ("descricao", "Descrição")],
    },
    "cnae": {
        "model": CNAE, "titulo": "CNAE",
        "titulo_singular": "CNAE", "fields": ["codigo", "descricao"],
        "columns": [("codigo", "Código"), ("descricao", "Descrição")],
    },
    "obrigacoes": {
        "model": ObrigacaoAcessoria, "titulo": "Obrigações Acessórias",
        "titulo_singular": "Obrigação Acessória", "fields": ["nome", "descricao", "dia_vencimento"],
        "columns": [("nome", "Nome"), ("descricao", "Descrição"), ("dia_vencimento", "Vence dia")],
    },
}


def get_catalogo_ou_404(slug):
    if slug not in CATALOGOS:
        from django.http import Http404
        raise Http404("Catálogo não encontrado")
    return CATALOGOS[slug]


@login_required
def painel_dashboard(request):
    context = {
        "total_empresas": Empresa.objects.count(),
        "total_impostos": Imposto.objects.count(),
        "apuracoes_pendentes": ApuracaoImposto.objects.filter(
            status__in=["PENDENTE", "ATRASADO"]
        ).count(),
        "catalogos": [
            {"slug": slug, "titulo": conf["titulo"]}
            for slug, conf in CATALOGOS.items()
        ],
    }
    return render(request, "core/painel_dashboard.html", context)


# ---------------------------------------------------------------------
# Empresas
# ---------------------------------------------------------------------
class EmpresaListView(LoginRequiredMixin, ListView):
    model = Empresa
    template_name = "core/empresa_list.html"
    context_object_name = "empresas"
    paginate_by = 20

    def get_queryset(self):
        qs = Empresa.objects.select_related(
            "tipo_empresa", "regime_tributario"
        ).order_by("razao_social")
        busca = self.request.GET.get("q")
        if busca:
            qs = qs.filter(razao_social__icontains=busca)
        return qs


@login_required
def nova_empresa(request):
    if request.method == "POST":
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa cadastrada com sucesso.")
            return redirect("empresa_list")
    else:
        form = EmpresaForm()

    return render(request, "core/empresa_form.html", {"form": form, "titulo": "Nova Empresa"})


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == "POST":
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa atualizada com sucesso.")
            return redirect("empresa_list")
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, "core/empresa_form.html", {
        "form": form, "titulo": f"Editar — {empresa.razao_social}"
    })


class EmpresaDeleteView(LoginRequiredMixin, DeleteView):
    model = Empresa
    template_name = "core/confirm_delete.html"
    success_url = "/painel/empresas/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["titulo"] = "Excluir empresa"
        return context


# ---------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------
@login_required
def catalogo_list(request, slug):
    conf = get_catalogo_ou_404(slug)
    itens = conf["model"].objects.all().order_by("pk")
    return render(request, "core/catalogo_list.html", {"slug": slug, "conf": conf, "itens": itens})


@login_required
def catalogo_form(request, slug, pk=None):
    from django.forms import modelform_factory

    conf = get_catalogo_ou_404(slug)
    Form = modelform_factory(conf["model"], fields=conf["fields"])

    instancia = None
    if pk is not None:
        instancia = get_object_or_404(conf["model"], pk=pk)

    if request.method == "POST":
        form = Form(request.POST, instance=instancia)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro salvo com sucesso.")
            return redirect("catalogo_list", slug=slug)
    else:
        form = Form(instance=instancia)

    return render(request, "core/catalogo_form.html", {
        "form": form, "conf": conf, "slug": slug,
        "titulo": (f"Editar {conf['titulo_singular']}" if instancia else f"Novo {conf['titulo_singular']}"),
    })


@login_required
def catalogo_delete(request, slug, pk):
    conf = get_catalogo_ou_404(slug)
    instancia = get_object_or_404(conf["model"], pk=pk)

    if request.method == "POST":
        instancia.delete()
        messages.success(request, "Registro excluído com sucesso.")
        return redirect("catalogo_list", slug=slug)

    return render(request, "core/confirm_delete.html", {
        "object": instancia,
        "cancel_url": reverse("catalogo_list", args=[slug]),
        "titulo": f"Excluir {conf['titulo_singular']}",
    })


# ---------------------------------------------------------------------
# Competências
# ---------------------------------------------------------------------
@login_required
def competencia_list(request, empresa_pk):
    empresa = get_object_or_404(Empresa, pk=empresa_pk)
    competencias = empresa.competencias.order_by("-ano", "-mes")
    return render(request, "core/competencia_list.html", {"empresa": empresa, "competencias": competencias})


@login_required
def nova_competencia(request, empresa_pk):
    empresa = get_object_or_404(Empresa, pk=empresa_pk)

    if request.method == "POST":
        form = CompetenciaForm(request.POST)
        if form.is_valid():
            competencia = form.save(commit=False)
            competencia.empresa = empresa
            competencia.save()

            CumprimentoObrigacao.objects.bulk_create([
                CumprimentoObrigacao(competencia=competencia, obrigacao=obrigacao)
                for obrigacao in empresa.obrigacoes_acessorias.all()
            ])

            messages.success(request, "Competência criada com sucesso.")
            return redirect("competencia_list", empresa_pk=empresa.pk)
    else:
        form = CompetenciaForm()

    return render(request, "core/competencia_form.html", {"form": form, "empresa": empresa})


class CompetenciaDeleteView(LoginRequiredMixin, DeleteView):
    model = Competencia
    template_name = "core/confirm_delete.html"

    def get_success_url(self):
        return reverse("competencia_list", args=[self.object.empresa_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        context["titulo"] = "Excluir competência"
        return context


@login_required
def competencia_detail(request, pk):
    competencia = get_object_or_404(Competencia, pk=pk)
    apuracoes = competencia.apuracoes_imposto.select_related("imposto")
    cumprimentos = competencia.cumprimentos_obrigacao.select_related("obrigacao").order_by("obrigacao__nome")

    if request.method == "POST":
        from django.utils import timezone

        for cumprimento in cumprimentos:
            # Cada linha manda dois campos próprios, identificados pelo id:
            # "concluido_<id>" (checkbox) e "status_manual_<id>" (select).
            concluido_agora = request.POST.get(f"concluido_{cumprimento.id}") == "on"
            status_manual_raw = request.POST.get(f"status_manual_{cumprimento.id}", "")

            mudou = False

            if concluido_agora and not cumprimento.cumprido:
                cumprimento.cumprido = True
                cumprimento.data_cumprimento = timezone.localdate()
                mudou = True
            elif not concluido_agora and cumprimento.cumprido:
                cumprimento.cumprido = False
                cumprimento.data_cumprimento = None
                mudou = True

            novo_status_manual = int(status_manual_raw) if status_manual_raw else None
            if novo_status_manual != cumprimento.status_manual:
                cumprimento.status_manual = novo_status_manual
                mudou = True

            if mudou:
                cumprimento.save()

        messages.success(request, "Rotinas fiscais atualizadas.")
        return redirect("competencia_detail", pk=competencia.pk)

    return render(request, "core/competencia_detail.html", {
        "competencia": competencia, "apuracoes": apuracoes, "cumprimentos": cumprimentos,
    })


# ---------------------------------------------------------------------
# Apurações de imposto
# ---------------------------------------------------------------------
@login_required
def nova_apuracao(request, competencia_pk):
    competencia = get_object_or_404(Competencia, pk=competencia_pk)

    if request.method == "POST":
        form = ApuracaoImpostoForm(request.POST)
        if form.is_valid():
            apuracao = form.save(commit=False)
            apuracao.competencia = competencia
            apuracao.save()
            messages.success(request, "Apuração registrada com sucesso.")
            return redirect("competencia_detail", pk=competencia.pk)
    else:
        form = ApuracaoImpostoForm()

    return render(request, "core/apuracao_form.html", {
        "form": form, "competencia": competencia, "titulo": "Nova Apuração"
    })


@login_required
def editar_apuracao(request, pk):
    apuracao = get_object_or_404(ApuracaoImposto, pk=pk)

    if request.method == "POST":
        form = ApuracaoImpostoForm(request.POST, instance=apuracao)
        if form.is_valid():
            form.save()
            messages.success(request, "Apuração atualizada com sucesso.")
            return redirect("competencia_detail", pk=apuracao.competencia_id)
    else:
        form = ApuracaoImpostoForm(instance=apuracao)

    return render(request, "core/apuracao_form.html", {
        "form": form, "competencia": apuracao.competencia, "titulo": "Editar Apuração",
    })

@login_required
def exportar_excel(request):
    """
    Gera um .xlsx no mesmo layout da planilha modelo enviada pelo cliente:
    título mesclado no topo, uma aba por regime tributário, um bloco por
    empresa (nome mesclado + linha "Rotinas Fiscais" mesclada + uma linha
    por obrigação), sem linha em branco entre empresas — e o "semáforo"
    (verde/amarelo/vermelho) em cada mês usando o recurso real de
    formatação condicional do Excel (iconSet), não um texto colorido.

    Valores gravados na célula (ocultos, só o ícone aparece):
      3 = Em dia (verde) | 2 = Risco de atraso (amarelo) | 1 = Atrasada (vermelho)

    Parâmetros via querystring: ?ano=2026 (padrão: ano atual)
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.formatting.rule import IconSetRule
    from django.http import HttpResponse
    from datetime import date

    ano = int(request.GET.get("ano", date.today().year))
    meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    titulo_font = Font(bold=True, size=18)
    secao_fill = PatternFill("solid", fgColor="E7E7E7")
    secao_font = Font(bold=True, size=12)
    centro = Alignment(horizontal="center")
    esquerda = Alignment(horizontal="left")

    def nova_regra_semaforo():
        return IconSetRule(
            icon_style="3TrafficLights1",
            type="num",
            values=[0, 2, 3],
            showValue=False,
        )

    for regime in RegimeTributario.objects.all():
        aba = workbook.create_sheet(title=regime.nome[:31])

        aba.merge_cells("B1:N1")
        titulo = aba.cell(row=1, column=2,
            value=f"ACOMPANHAMENTO: Departamento Fiscal - Empresas {regime.nome}.")
        titulo.font = titulo_font
        titulo.alignment = centro
        aba.row_dimensions[1].height = 31.5

        aba.cell(row=1, column=16, value="Legenda").fill = secao_fill
        aba.cell(row=2, column=16, value="Em dia (3)")
        aba.cell(row=2, column=17, value=3)
        aba.cell(row=3, column=16, value="Risco de atraso (2)")
        aba.cell(row=3, column=17, value=2)
        aba.cell(row=4, column=16, value="Atrasada (1)")
        aba.cell(row=4, column=17, value=1)
        aba.conditional_formatting.add("Q2:Q4", nova_regra_semaforo())

        for col, nome_mes in enumerate(meses_nomes, start=3):
            celula = aba.cell(row=2, column=col, value=nome_mes)
            celula.alignment = centro
            celula.font = Font(bold=True)
            celula.fill = secao_fill

        linha = 3
        empresas = Empresa.objects.filter(
            regime_tributario=regime
        ).prefetch_related("obrigacoes_acessorias")

        for empresa in empresas:
            aba.merge_cells(f"B{linha}:N{linha}")
            celula = aba.cell(row=linha, column=2, value=empresa.razao_social)
            celula.fill = secao_fill
            celula.font = secao_font
            celula.alignment = centro
            linha += 1

            obrigacoes = empresa.obrigacoes_acessorias.all()
            if not obrigacoes:
                continue

            aba.merge_cells(f"B{linha}:N{linha}")
            celula = aba.cell(row=linha, column=2, value="Rotinas Fiscais")
            celula.fill = secao_fill
            celula.font = secao_font
            celula.alignment = esquerda
            linha += 1

            cumprimentos = CumprimentoObrigacao.objects.filter(
                competencia__empresa=empresa, competencia__ano=ano,
            ).select_related("competencia", "obrigacao")

            por_mes_obrigacao = {
                (c.competencia.mes, c.obrigacao_id): c.status_calculado()
                for c in cumprimentos
            }

            for obrigacao in obrigacoes:
                linha_inicial = linha
                aba.cell(row=linha, column=2, value=obrigacao.nome)

                for mes in range(1, 13):
                    status = por_mes_obrigacao.get((mes, obrigacao.id))
                    if status is not None:
                        aba.cell(row=linha, column=2 + mes, value=status)

                aba.conditional_formatting.add(
                    f"C{linha_inicial}:N{linha_inicial}", nova_regra_semaforo()
                )
                linha += 1

            # Sem linha em branco entre empresas — igual à planilha modelo.

        aba.column_dimensions["A"].width = 3
        aba.column_dimensions["B"].width = 42
        for col in range(3, 15):
            aba.column_dimensions[
                openpyxl.utils.get_column_letter(col)
            ].width = 11
        aba.column_dimensions["P"].width = 21.5
        aba.column_dimensions["Q"].width = 8.4

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )
    response["Content-Disposition"] = (
        f'attachment; filename="acompanhamento_fiscal_{ano}.xlsx"'
    )
    workbook.save(response)
    return response


class ApuracaoDeleteView(LoginRequiredMixin, DeleteView):
    model = ApuracaoImposto
    template_name = "core/confirm_delete.html"

    def get_success_url(self):
        return reverse("competencia_detail", args=[self.object.competencia_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        context["titulo"] = "Excluir apuração"
        return context