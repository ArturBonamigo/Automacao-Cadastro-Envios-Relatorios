"""Programa independente para gerar os relatórios dos resultados."""

from execucao import executar


def gerar():
    from relatorios import main

    main()


if __name__ == "__main__":
    raise SystemExit(executar("Gerar Relatorios", gerar))
