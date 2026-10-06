"""Relatórios por nome, sem executar as exportações de cruzamentos.py."""

from pathlib import Path

from normalizacao import normalizar_nomes
from processamento import (
    processar_nomes_agendados,
    processar_nomes_efetivados,
    processar_nomes_telefones_base,
    processar_resultados,
)


COLUNAS_TELEFONES = [
    "Telefone Celular",
    "Telefone Comercial",
    "Telefone Fax",
    "Telefone Recado",
    "Telefone Residencial",
]

TEMPLATE_EFETIVADOS = "Termo de Efetivação de Encerramento"
TEMPLATE_AGENDADOS = "Comunicado de Agendamento de Encerramento de Conta Corrente"


def _selecionar_numeros_recebidos(df_resultados, template):
    """Seleciona números completos com status exatamente Recebido no template."""
    campanha = df_resultados.loc[
        df_resultados["Desc. Template"].eq(template)
    ]

    # Não confundir uma campanha ausente com uma campanha sem sucesso.
    if campanha.empty:
        raise ValueError(f"Template não encontrado no relatório: {template!r}")

    numeros = campanha.loc[
        campanha["Status"].eq("Recebido"), "Número do cliente"
    ].astype("string")

    # O Excel pode devolver identificadores numéricos como 5549999999999.0.
    numeros = (
        numeros.str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"[\s()+-]+", "", regex=True)
    )

    formato_aceito = numeros.str.fullmatch(r"55[0-9]{10,11}", na=False)
    return numeros.loc[formato_aceito].drop_duplicates()


def _relacionar_nomes_telefones(df_base):
    """Mantém a associação nome/telefone apenas para nomes únicos na base."""
    base = df_base[["nome", *COLUNAS_TELEFONES]].copy()
    base["nome_normalizado"] = normalizar_nomes(base["nome"])

    nome_preenchido = (
        base["nome_normalizado"].notna()
        & base["nome_normalizado"].ne("")
    )
    base = base.loc[nome_preenchido]

    # keep=False exclui todas as ocorrências dos nomes ambíguos.
    base_unica = base.loc[
        ~base["nome_normalizado"].duplicated(keep=False)
    ]

    relacao = base_unica.melt(
        id_vars=["nome_normalizado"],
        value_vars=COLUNAS_TELEFONES,
        var_name="tipo_telefone",
        value_name="telefone_original",
    )

    telefones_limpos = (
        relacao["telefone_original"]
        .astype("string")
        .str.replace(r"[\s-]+", "", regex=True)
    )
    partes = telefones_limpos.str.extract(
        r"^\(([0-9]{2})\)([0-9]{8,9})$"
    )
    partes.columns = ["DDD", "telefone"]

    # A mesma regra de formato usada na preparação das listas de envio.
    relacao["numero_completo"] = "55" + partes["DDD"] + partes["telefone"]
    return (
        relacao[["nome_normalizado", "numero_completo"]]
        .dropna(subset=["numero_completo"])
        .drop_duplicates()
    )


def _gerar_relatorio(df_nomes, df_base, df_resultados, template):
    """Um telefone recebido é suficiente para marcar o nome como Enviada."""
    numeros_recebidos = _selecionar_numeros_recebidos(df_resultados, template)
    relacao = _relacionar_nomes_telefones(df_base)

    nomes_com_recebimento = relacao.loc[
        relacao["numero_completo"].isin(numeros_recebidos),
        "nome_normalizado",
    ]

    # Partir da lista completa inclui nomes sem telefone ou sem correspondência.
    relatorio = df_nomes[["nome"]].copy()
    relatorio["nome_normalizado"] = normalizar_nomes(relatorio["nome"])
    nome_preenchido = (
        relatorio["nome_normalizado"].notna()
        & relatorio["nome_normalizado"].ne("")
    )
    relatorio = (
        relatorio.loc[nome_preenchido]
        .drop_duplicates(subset=["nome_normalizado"])
        .copy()
    )

    relatorio["status_envio"] = "Não enviado"
    relatorio.loc[
        relatorio["nome_normalizado"].isin(nomes_com_recebimento),
        "status_envio",
    ] = "Enviada"

    return relatorio[["nome", "status_envio"]].reset_index(drop=True)


def gerar_relatorio_efetivados(
    df_efetivados, df_base, df_resultados, template=TEMPLATE_EFETIVADOS
):
    """Recebe a lista de Efetivados, a base processada e os resultados."""
    return _gerar_relatorio(df_efetivados, df_base, df_resultados, template)


def gerar_relatorio_agendados(
    df_agendados, df_base, df_resultados, template=TEMPLATE_AGENDADOS
):
    """Compara Agendados apenas com os resultados do seu template."""
    return _gerar_relatorio(df_agendados, df_base, df_resultados, template)


def salvar_relatorio(df_relatorio, caminho):
    """Exporta somente nome e status_envio; substitui o arquivo se já existir."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df_relatorio.to_excel(
        caminho,
        columns=["nome", "status_envio"],
        index=False,
    )
    return caminho


def main():
    """Gera os relatórios dos grupos presentes em Entradas/Resultados.xlsx."""
    df_resultados = processar_resultados()
    templates_presentes = set(df_resultados["Desc. Template"].dropna())

    grupos = [
        (
            "Efetivados",
            TEMPLATE_EFETIVADOS,
            processar_nomes_efetivados,
            gerar_relatorio_efetivados,
        ),
        (
            "Agendados",
            TEMPLATE_AGENDADOS,
            processar_nomes_agendados,
            gerar_relatorio_agendados,
        ),
    ]

    if not templates_presentes.intersection(
        {TEMPLATE_EFETIVADOS, TEMPLATE_AGENDADOS}
    ):
        raise ValueError(
            "Nenhum template de Efetivados ou Agendados foi encontrado "
            "em Entradas/Resultados.xlsx."
        )

    df_base = processar_nomes_telefones_base()

    for grupo, template, carregar_nomes, gerar_relatorio in grupos:
        if template not in templates_presentes:
            print(
                f"{grupo}: template ausente nesta entrada; "
                "relatório não gerado. Eventual arquivo anterior não foi atualizado."
            )
            continue

        df_nomes = carregar_nomes()
        relatorio = gerar_relatorio(df_nomes, df_base, df_resultados, template)
        caminho = salvar_relatorio(relatorio, f"Saídas/Resultados {grupo}.xlsx")
        print(f"Relatório de {grupo} salvo em: {caminho}")
        print(relatorio["status_envio"].value_counts().to_string())


if __name__ == "__main__":
    main()
