"""Gera listas de envio aplicando as mesmas regras de cadastro dos relatórios."""

from contatos import AVISO_MANUAL, gerar_lista_envio, preparar_base
from normalizacao import normalizar_nomes
from processamento import (
    processar_nomes_agendados,
    processar_nomes_efetivados,
    processar_nomes_telefones_base,
)


df_base = processar_nomes_telefones_base()
df_agendados = processar_nomes_agendados()
df_efetivados = processar_nomes_efetivados()
analise_base = preparar_base(df_base)

df_envio_agendados = gerar_lista_envio(df_agendados, analise_base)
df_envio_efetivados = gerar_lista_envio(df_efetivados, analise_base)

for grupo, nomes, envio in (
    ("Agendados", df_agendados, df_envio_agendados),
    ("Efetivados", df_efetivados, df_envio_efetivados),
):
    base, _ = analise_base
    manuais = base.loc[
        ~base["cadastro_liberado"]
        & base["nome_normalizado"].isin(normalizar_nomes(nomes["nome"])),
        "nome_normalizado",
    ].nunique()
    if manuais:
        print(f"{grupo}: {manuais} nome(s): {AVISO_MANUAL}.")
    envio.to_excel(
        f"Saídas/Envio {grupo}.xlsx",
        columns=["DDI", "DDD", "telefone"],
        index=False,
    )
