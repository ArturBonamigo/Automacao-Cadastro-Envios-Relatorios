"""Programa independente para gerar as duas planilhas de envio."""

from execucao import executar


def gerar():
    # O módulo existente realiza as exportações ao ser importado.
    import cruzamentos

    print(f"Agendados: {len(cruzamentos.df_envio_agendados)} telefones.")
    print(f"Efetivados: {len(cruzamentos.df_envio_efetivados)} telefones.")


if __name__ == "__main__":
    raise SystemExit(executar("Gerar Envios", gerar))
