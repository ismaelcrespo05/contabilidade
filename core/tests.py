from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import (
    ApuracaoImposto, Competencia, CumprimentoObrigacao, Empresa, Imposto,
    ObrigacaoAcessoria, RegimeTributario,
)
from .rotinas_import_utils import importar_log_para_banco


class ImportacaoRotinasTest(TestCase):
    def test_importa_status_de_cada_mes_da_mesma_obrigacao(self):
        importar_log_para_banco([
            ("empresa", "Simples", "Empresa", None),
            ("obrigacao", "Empresa", "EFD", [
                (1, 2026, CumprimentoObrigacao.STATUS_CONCLUIDA),
                (2, 2026, CumprimentoObrigacao.STATUS_CONCLUIDA),
                (3, 2026, CumprimentoObrigacao.STATUS_RISCO),
            ]),
        ])

        cumprimentos = CumprimentoObrigacao.objects.filter(
            competencia__empresa__razao_social="Empresa",
            obrigacao__nome="EFD",
        ).order_by("competencia__mes")

        self.assertEqual(cumprimentos.count(), 3)
        self.assertTrue(cumprimentos[0].cumprido)
        self.assertTrue(cumprimentos[1].cumprido)
        self.assertEqual(
            cumprimentos[2].status_manual,
            CumprimentoObrigacao.STATUS_RISCO,
        )
        self.assertFalse(cumprimentos[2].cumprido)

    def test_reimportacao_atualiza_status_existente(self):
        importar_log_para_banco([
            ("empresa", "Simples", "Empresa", None),
            ("obrigacao", "Empresa", "EFD", [
                (1, 2018, CumprimentoObrigacao.STATUS_CONCLUIDA),
            ]),
        ])
        importar_log_para_banco([
            ("empresa", "Simples", "Empresa", None),
            ("obrigacao", "Empresa", "EFD", [
                (1, 2026, CumprimentoObrigacao.STATUS_RISCO),
            ]),
        ])

        cumprimento = CumprimentoObrigacao.objects.get(
            competencia__ano=2026,
            competencia__mes=1,
            obrigacao__nome="EFD",
        )
        self.assertEqual(
            cumprimento.status_manual,
            CumprimentoObrigacao.STATUS_RISCO,
        )
        self.assertFalse(cumprimento.cumprido)
        self.assertFalse(
            CumprimentoObrigacao.objects.filter(competencia__ano=2018).exists()
        )

    def test_reimportar_cnpj_atualiza_empresa_sem_apagar_historico(self):
        regime_antigo = RegimeTributario.objects.create(nome="Antigo")
        regime_novo = RegimeTributario.objects.create(nome="Novo")
        empresa = Empresa.objects.create(
            cnpj="12.345.678/0001-90", razao_social="Nome anterior",
            regime_tributario=regime_antigo,
        )
        obrigacao_antiga = ObrigacaoAcessoria.objects.create(nome="SPED")
        empresa.obrigacoes_acessorias.add(obrigacao_antiga)
        competencia = Competencia.objects.create(empresa=empresa, ano=2026, mes=1)
        cumprimento = CumprimentoObrigacao.objects.create(
            competencia=competencia, obrigacao=obrigacao_antiga, cumprido=True
        )

        importar_log_para_banco([
            ("empresa", "Novo", "Nome atualizado", "12.345.678/0001-90"),
            ("obrigacao", "Nome atualizado", "DCTF", [(1, 2026, 2)]),
        ])

        empresa.refresh_from_db()
        cumprimento.refresh_from_db()
        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(empresa.razao_social, "Nome atualizado")
        self.assertEqual(empresa.regime_tributario, regime_novo)
        self.assertTrue(empresa.obrigacoes_acessorias.filter(nome="SPED").exists())
        self.assertTrue(empresa.obrigacoes_acessorias.filter(nome="DCTF").exists())
        self.assertTrue(cumprimento.cumprido)


class StatusVencimentoTest(TestCase):
    def setUp(self):
        regime = RegimeTributario.objects.create(nome="Simples")
        empresa = Empresa.objects.create(razao_social="Empresa", regime_tributario=regime)
        self.competencia = Competencia.objects.create(empresa=empresa, ano=2026, mes=1)
        self.obrigacao = ObrigacaoAcessoria.objects.create(nome="EFD")

    def test_obrigacao_cumprida_e_concluida(self):
        cumprimento = CumprimentoObrigacao.objects.create(
            competencia=self.competencia, obrigacao=self.obrigacao,
            cumprido=True, status_manual=CumprimentoObrigacao.STATUS_ATRASADA,
        )
        self.assertEqual(cumprimento.status_calculado(), CumprimentoObrigacao.STATUS_CONCLUIDA)

    def test_obrigacao_vencida_nao_concluida_e_atrasada(self):
        cumprimento = CumprimentoObrigacao.objects.create(
            competencia=self.competencia, obrigacao=self.obrigacao,
            status_manual=CumprimentoObrigacao.STATUS_EM_DIA,
            data_vencimento_manual=date.today() - timedelta(days=1),
        )
        self.assertEqual(cumprimento.status_calculado(), CumprimentoObrigacao.STATUS_ATRASADA)

    def test_status_concluida_exige_cumprido(self):
        cumprimento = CumprimentoObrigacao.objects.create(
            competencia=self.competencia, obrigacao=self.obrigacao,
            status_manual=CumprimentoObrigacao.STATUS_CONCLUIDA,
            data_vencimento_manual=date.today() + timedelta(days=20),
        )
        self.assertNotEqual(cumprimento.status_calculado(), CumprimentoObrigacao.STATUS_CONCLUIDA)

    def test_marcar_obrigacao_concluida_registra_cumprido(self):
        cumprimento = CumprimentoObrigacao.objects.create(
            competencia=self.competencia, obrigacao=self.obrigacao,
        )
        from django.contrib.auth.models import User
        user = User.objects.create_user(username="editor", password="senha")
        user.perfil.papel = "AUXILIAR"
        user.perfil.save()
        self.client.force_login(user)

        response = self.client.post(reverse("atualizar_status_cumprimento", args=[cumprimento.pk]), {
            "concluida": "on",
        })

        cumprimento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(cumprimento.cumprido)
        self.assertIsNotNone(cumprimento.data_cumprimento)

    def test_imposto_nao_pode_duplicar_na_competencia(self):
        imposto = Imposto.objects.create(nome="IRPJ")
        ApuracaoImposto.objects.create(
            competencia=self.competencia, imposto=imposto,
            data_vencimento=date.today() + timedelta(days=10),
        )
        with self.assertRaises(Exception):
            ApuracaoImposto.objects.create(competencia=self.competencia, imposto=imposto)
