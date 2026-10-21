"""Regras comuns de associação de cadastros para envios e relatórios."""

import pandas as pd

from normalizacao import normalizar_nomes


COLUNAS_TELEFONES = [
    "Telefone Celular",
    "Telefone Comercial",
    "Telefone Fax",
    "Telefone Recado",
    "Telefone Residencial",
]
AVISO_MANUAL = "números diversos para nomes iguais, mandar manualmente"


def _cadastros_conectados(conjuntos):
    """Cada cadastro precisa estar ligado aos demais por telefone em comum."""
    pendentes = list(conjuntos)
    conhecidos = set(pendentes.pop(0))
    while pendentes:
        for indice, numeros in enumerate(pendentes):
            if conhecidos.intersection(numeros):
                conhecidos.update(pendentes.pop(indice))
                break
        else:
            return False
    return True


def preparar_base(df_base):
    """Mantém todos os telefones e sinaliza quais cadastros permitem envio."""
    base = df_base.copy().reset_index(drop=True)
    base["nome_normalizado"] = normalizar_nomes(base["nome"])
    base = base.loc[
        base["nome_normalizado"].notna() & base["nome_normalizado"].ne("")
    ].copy()
    base["_cadastro"] = base.index

    relacao = base.melt(
        id_vars=["nome_normalizado", "_cadastro"],
        value_vars=COLUNAS_TELEFONES,
        var_name="tipo_telefone",
        value_name="telefone_original",
    )
    limpos = (
        relacao["telefone_original"].astype("string")
        .str.replace(r"[\s-]+", "", regex=True)
    )
    partes = limpos.str.extract(r"^\(([0-9]{2})\)([0-9]{8,9})$")
    relacao["numero_completo"] = "55" + partes[0] + partes[1]
    relacao = relacao.dropna(subset=["numero_completo"])

    numeros_por_cadastro = relacao.groupby("_cadastro")["numero_completo"].agg(set)
    conflitos = set()
    repetidos = base.loc[base["nome_normalizado"].duplicated(keep=False)]
    for nome, cadastros in repetidos.groupby("nome_normalizado", sort=False):
        conjuntos = [numeros_por_cadastro.get(indice, set()) for indice in cadastros.index]
        if not _cadastros_conectados(conjuntos):
            conflitos.add(nome)

    base["cadastro_liberado"] = ~base["nome_normalizado"].isin(conflitos)
    relacao["cadastro_liberado"] = ~relacao["nome_normalizado"].isin(conflitos)
    relacao = relacao[
        ["nome_normalizado", "numero_completo", "cadastro_liberado"]
    ].drop_duplicates()
    return base, relacao


def gerar_lista_envio(df_nomes, analise_base):
    """Usa todos os números dos cadastros liberados, sem repetir telefones."""
    _, relacao = analise_base
    nomes = normalizar_nomes(df_nomes["nome"])
    numeros = relacao.loc[
        relacao["cadastro_liberado"] & relacao["nome_normalizado"].isin(nomes),
        "numero_completo",
    ].drop_duplicates().reset_index(drop=True)
    return pd.DataFrame({
        "DDI": numeros.str[:2],
        "DDD": numeros.str[2:4],
        "telefone": numeros.str[4:],
    })
