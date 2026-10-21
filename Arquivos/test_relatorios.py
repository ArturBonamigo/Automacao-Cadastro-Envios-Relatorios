"""Regressões da classificação de envios, com dados fictícios."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from processamento import processar_nomes_telefones_base
from contatos import AVISO_MANUAL, gerar_lista_envio, preparar_base
from relatorios import (
    COLUNAS_TELEFONES,
    TEMPLATE_AGENDADOS,
    TEMPLATE_EFETIVADOS,
    gerar_relatorio_agendados,
    gerar_relatorio_efetivados,
    salvar_relatorio,
)


def base_telefone(nome="Pessoa Teste", celular="(11) 99999-0001", comercial=None,
                  email="pessoa@example.com"):
    row = {coluna: None for coluna in COLUNAS_TELEFONES}
    row.update(nome=nome, email=email)
    row["Telefone Celular"] = celular
    row["Telefone Comercial"] = comercial
    return pd.DataFrame([row])


def resultados(linhas, template=TEMPLATE_EFETIVADOS):
    return pd.DataFrame(
        [(template, numero, status) for numero, status in linhas],
        columns=["Desc. Template", "Número do cliente", "Status"],
    )


class RegrasEnvioTest(unittest.TestCase):
    def setUp(self):
        self.nomes = pd.DataFrame({"nome": ["Pessoa Teste"]})

    def test_enviado_recebido_lido_contam_nos_dois_grupos(self):
        for template, gerar in (
            (TEMPLATE_EFETIVADOS, gerar_relatorio_efetivados),
            (TEMPLATE_AGENDADOS, gerar_relatorio_agendados),
        ):
            for status in ("Enviado", "Recebido", "Lido"):
                with self.subTest(template=template, status=status):
                    campanha = resultados([("5511999990001", status)], template)
                    out = gerar(self.nomes, base_telefone(), campanha)
                    self.assertEqual(out["status_envio"].tolist(), ["Enviada"])
                    self.assertEqual(out["telefones"].tolist(), ["5511999990001"])

    def test_falha_desconhecido_e_vazio_nao_contam(self):
        for status in ("Falha ao enviar", "Pendente", None):
            with self.subTest(status=status):
                campanha = resultados([("5511999990001", status)])
                out = gerar_relatorio_efetivados(self.nomes, base_telefone(), campanha)
                self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])

    def test_dois_telefones_e_nomes_repetidos_contam_uma_pessoa(self):
        campanha = resultados([
            ("5511999990001", "Lido"),
            ("5511999990002", "Enviado"),
        ])
        base = base_telefone(comercial="(11) 99999-0002")
        nomes = pd.DataFrame({"nome": ["Pessoa Teste", " PESSOA TESTE "]})
        out = gerar_relatorio_efetivados(nomes, base, campanha)
        self.assertEqual(out.to_dict("records"), [
            {"nome": "Pessoa Teste", "status_envio": "Enviada",
             "telefones": "5511999990001; 5511999990002", "e-mail": "", "observacao": ""},
        ])

    def test_telefones_incluem_falhas_e_numeros_sem_notificacao_sem_repetir(self):
        campanha = resultados([("5511999990001", "Falha ao enviar")])
        base = base_telefone(comercial="(11) 99999-0002")
        base["Telefone Recado"] = "(11) 99999-0001"
        out = gerar_relatorio_efetivados(self.nomes, base, campanha)
        self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])
        self.assertEqual(out["telefones"].tolist(), ["5511999990001; 5511999990002"])

    def test_sem_telefone_ou_nome_correspondente_ficam_vazios(self):
        campanha = resultados([("5511999990001", "Lido")])
        for base in (
            base_telefone(celular=None),
            base_telefone(nome="Outra Pessoa"),
        ):
            with self.subTest(base=base.to_dict("records")):
                out = gerar_relatorio_efetivados(self.nomes, base, campanha)
                self.assertEqual(out["telefones"].tolist(), [""])
                self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])

    def test_sucesso_de_outra_campanha_nao_conta(self):
        campanha = pd.concat([
            resultados([("5511999990001", "Falha ao enviar")]),
            resultados([("5511999990001", "Lido")], TEMPLATE_AGENDADOS),
        ], ignore_index=True)
        out = gerar_relatorio_efetivados(self.nomes, base_telefone(), campanha)
        self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])

    def test_template_ausente_expoe_erro(self):
        campanha = resultados([("5511999990001", "Lido")], TEMPLATE_AGENDADOS)
        with self.assertRaisesRegex(ValueError, "Template não encontrado"):
            gerar_relatorio_efetivados(self.nomes, base_telefone(), campanha)

    def test_email_aparece_apenas_para_nao_enviados_nos_dois_grupos(self):
        for template, gerar in (
            (TEMPLATE_EFETIVADOS, gerar_relatorio_efetivados),
            (TEMPLATE_AGENDADOS, gerar_relatorio_agendados),
        ):
            for status in ("Enviado", "Recebido", "Lido", "Falha ao enviar", "Pendente", None):
                with self.subTest(template=template, status=status):
                    campanha = resultados([("5511999990001", status)], template)
                    out = gerar(self.nomes, base_telefone(), campanha)
                    esperado = "" if status in ("Enviado", "Recebido", "Lido") else "pessoa@example.com"
                    self.assertEqual(out["e-mail"].tolist(), [esperado])

    def test_email_sem_telefone_e_por_nome_normalizado(self):
        base = base_telefone(nome=" PÉSsoa   TESTE ", celular=None)
        campanha = resultados([("5511999990001", "Lido")])
        out = gerar_relatorio_efetivados(self.nomes, base, campanha)
        self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])
        self.assertEqual(out["telefones"].tolist(), [""])
        self.assertEqual(out["e-mail"].tolist(), ["pessoa@example.com"])

    def test_email_vazio_ausente_ou_nome_ambiguo_nao_e_preenchido(self):
        campanha = resultados([("5511999990001", "Falha ao enviar")])
        for base in (
            base_telefone(email=None),
            base_telefone(nome="Outra Pessoa"),
            pd.concat([
                base_telefone(), base_telefone(celular="(11) 99999-0002", email="outra@example.com"),
            ], ignore_index=True),
        ):
            with self.subTest(base=base.to_dict("records")):
                out = gerar_relatorio_efetivados(self.nomes, base, campanha)
                self.assertEqual(out["e-mail"].tolist(), [""])

    def test_exportacao_inclui_email_e_preserva_demais_colunas(self):
        campanha = resultados([("5511999990001", "Falha ao enviar")])
        relatorio = gerar_relatorio_efetivados(self.nomes, base_telefone(), campanha)
        with TemporaryDirectory() as pasta:
            caminho = salvar_relatorio(relatorio, Path(pasta) / "relatorio.xlsx")
            salvo = pd.read_excel(caminho, keep_default_na=False, dtype=str)
        pd.testing.assert_frame_equal(salvo, relatorio, check_dtype=False)


class CadastrosRepetidosTest(unittest.TestCase):
    def setUp(self):
        self.nomes = pd.DataFrame({"nome": ["15.829.339 Pessoa Teste"]})

    def test_telefone_compartilhado_libera_todos_os_numeros_nos_dois_grupos(self):
        base = pd.concat([
            base_telefone(),
            base_telefone(nome="15.829.339 Pessoa Teste", comercial="(11) 99999-0002"),
        ], ignore_index=True)
        base.loc[1, "Telefone Celular"] = "(11)999990001"
        envio = gerar_lista_envio(self.nomes, preparar_base(base))
        self.assertEqual(envio["telefone"].tolist(), ["999990001", "999990002"])
        for template, gerar in (
            (TEMPLATE_EFETIVADOS, gerar_relatorio_efetivados),
            (TEMPLATE_AGENDADOS, gerar_relatorio_agendados),
        ):
            with self.subTest(template=template):
                out = gerar(self.nomes, base, resultados([("5511999990002", "Lido")], template))
                self.assertEqual(out["status_envio"].tolist(), ["Enviada"])
                self.assertEqual(out["telefones"].tolist(), ["5511999990001; 5511999990002"])
                self.assertEqual(out["observacao"].tolist(), [""])

    def test_telefones_diversos_sao_exibidos_mas_exigem_envio_manual(self):
        base = pd.concat([
            base_telefone(), base_telefone(celular="(11) 99999-0002"),
        ], ignore_index=True)
        self.assertTrue(gerar_lista_envio(self.nomes, preparar_base(base)).empty)
        for template, gerar in (
            (TEMPLATE_EFETIVADOS, gerar_relatorio_efetivados),
            (TEMPLATE_AGENDADOS, gerar_relatorio_agendados),
        ):
            with self.subTest(template=template):
                out = gerar(self.nomes, base, resultados([("5511999990001", "Lido")], template))
                self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])
                self.assertEqual(out["telefones"].tolist(), ["5511999990001; 5511999990002"])
                self.assertEqual(out["observacao"].tolist(), [AVISO_MANUAL])
                self.assertEqual(out["e-mail"].tolist(), [""])

    def test_marcadores_vazios_e_invalidos_nao_comprovam_telefone_em_comum(self):
        for telefone in (None, -2, "-2", "123", "-"):
            with self.subTest(telefone=telefone):
                base = pd.concat([
                    base_telefone(celular=telefone), base_telefone(celular=telefone),
                ], ignore_index=True)
                cadastros, _ = preparar_base(base)
                self.assertFalse(cadastros["cadastro_liberado"].any())

    def test_terceiro_cadastro_isolado_bloqueia_o_grupo(self):
        base = pd.concat([
            base_telefone(), base_telefone(comercial="(11) 99999-0002"),
            base_telefone(celular="(11) 99999-0003"),
        ], ignore_index=True)
        self.assertTrue(gerar_lista_envio(self.nomes, preparar_base(base)).empty)

    def test_numero_em_campos_diferentes_tambem_confirma_a_ligacao(self):
        base = pd.concat([
            base_telefone(),
            base_telefone(celular="(11) 99999-0002", comercial="(11) 99999-0001"),
        ], ignore_index=True)
        envio = gerar_lista_envio(self.nomes, preparar_base(base))
        self.assertEqual(set(envio["telefone"]), {"999990001", "999990002"})

    def test_uniao_aproveita_mais_de_cinco_numeros_sem_truncar(self):
        base = pd.concat([base_telefone(), base_telefone()], ignore_index=True)
        for indice in range(1, 5):
            base.loc[0, COLUNAS_TELEFONES[indice]] = f"(11) 99999-{indice + 1:04d}"
            base.loc[1, COLUNAS_TELEFONES[indice]] = f"(11) 99999-{indice + 5:04d}"
        envio = gerar_lista_envio(self.nomes, preparar_base(base))
        self.assertEqual(len(envio), 9)
        self.assertEqual(envio["telefone"].nunique(), 9)

    def test_tres_cadastros_ligados_por_telefones_liberam_todos(self):
        base = pd.concat([
            base_telefone(),
            base_telefone(celular="(11) 99999-0003", comercial="(11) 99999-0002"),
            base_telefone(comercial="(11) 99999-0002"),
        ], ignore_index=True)
        envio = gerar_lista_envio(self.nomes, preparar_base(base))
        self.assertEqual(set(envio["telefone"]), {"999990001", "999990002", "999990003"})

    def test_emails_dos_cadastros_ligados_sao_reunidos_sem_repetir(self):
        base = pd.concat([
            base_telefone(), base_telefone(email="outra@example.com"), base_telefone(),
        ], ignore_index=True)
        out = gerar_relatorio_efetivados(
            self.nomes, base, resultados([("5511999990001", "Falha ao enviar")])
        )
        self.assertEqual(out["e-mail"].tolist(), ["pessoa@example.com; outra@example.com"])

    def test_nomes_diferentes_com_mesmo_telefone_seguem_separados(self):
        base = pd.concat([
            base_telefone(), base_telefone(nome="Outra Pessoa"),
        ], ignore_index=True)
        out = gerar_relatorio_efetivados(
            pd.DataFrame({"nome": ["Pessoa Teste", "Outra Pessoa"]}),
            base, resultados([("5511999990001", "Lido")]),
        )
        self.assertEqual(len(out), 2)
        self.assertEqual(out["observacao"].tolist(), ["", ""])


class LeituraNovaBaseTest(unittest.TestCase):
    def test_novo_cabecalho_telefones_menos_dois_e_email(self):
        linhas = []
        for email in (" pessoa@example.com ", "NÃO INFORMADO", None, "   "):
            linha = {coluna: -2 for coluna in COLUNAS_TELEFONES}
            linha.update({
                "Nome Cliente": "123.456.789 Pessoa Teste",
                "Telefone Celular": "(11) 99999-0001",
                "Telefone Comercial": "-2",
                "Email": email,
            })
            linhas.append(linha)
        with patch("processamento.pd.read_excel", return_value=pd.DataFrame(linhas)) as ler:
            base = processar_nomes_telefones_base()
        self.assertEqual(ler.call_args.args, (r"Entradas\Telefones de Associados 3251.xlsx",))
        self.assertNotIn("skiprows", ler.call_args.kwargs)
        self.assertIn("Nome Cliente", ler.call_args.kwargs["usecols"])
        self.assertIn("Email", ler.call_args.kwargs["usecols"])
        self.assertEqual(base["nome"].tolist(), ["Pessoa Teste"] * 4)
        self.assertEqual(base["Telefone Celular"].tolist(), ["(11) 99999-0001"] * 4)
        self.assertTrue(base[COLUNAS_TELEFONES[1:]].isna().all().all())
        self.assertEqual(base["email"].fillna("").tolist(), ["pessoa@example.com", "", "", ""])


if __name__ == "__main__":
    unittest.main()
