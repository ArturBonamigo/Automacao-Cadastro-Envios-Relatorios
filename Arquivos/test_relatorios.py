"""Regressões da classificação de envios, com dados fictícios."""

import unittest

import pandas as pd

from relatorios import (
    COLUNAS_TELEFONES,
    TEMPLATE_AGENDADOS,
    TEMPLATE_EFETIVADOS,
    gerar_relatorio_agendados,
    gerar_relatorio_efetivados,
)


def base_telefone(nome="Pessoa Teste", celular="(11) 99999-0001", comercial=None):
    row = {coluna: None for coluna in COLUNAS_TELEFONES}
    row.update(nome=nome)
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
             "telefones": "5511999990001; 5511999990002"},
        ])

    def test_telefones_incluem_falhas_e_numeros_sem_notificacao_sem_repetir(self):
        campanha = resultados([("5511999990001", "Falha ao enviar")])
        base = base_telefone(comercial="(11) 99999-0002")
        base["Telefone Recado"] = "(11) 99999-0001"
        out = gerar_relatorio_efetivados(self.nomes, base, campanha)
        self.assertEqual(out["status_envio"].tolist(), ["Não enviado"])
        self.assertEqual(out["telefones"].tolist(), ["5511999990001; 5511999990002"])

    def test_sem_telefone_sem_nome_correspondente_e_ambiguo_ficam_vazios(self):
        campanha = resultados([("5511999990001", "Lido")])
        for base in (
            base_telefone(celular=None),
            base_telefone(nome="Outra Pessoa"),
            pd.concat([base_telefone(), base_telefone()], ignore_index=True),
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


if __name__ == "__main__":
    unittest.main()
