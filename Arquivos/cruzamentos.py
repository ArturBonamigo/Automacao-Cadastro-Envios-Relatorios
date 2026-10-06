import pandas as pd

from normalizacao import normalizar_nomes
from processamento import processar_nomes_telefones_base, processar_nomes_agendados, processar_nomes_efetivados

df_base = processar_nomes_telefones_base()
df_agendados = processar_nomes_agendados()
df_efetivados = processar_nomes_efetivados()

df_base["nome_normalizado"] = normalizar_nomes(df_base["nome"])
df_agendados["nome_normalizado"] = normalizar_nomes(df_agendados["nome"])
df_efetivados["nome_normalizado"] = normalizar_nomes(df_efetivados["nome"])

base_telefones = df_base[
    [
        "nome_normalizado",
        "Telefone Celular",
        "Telefone Comercial",
        "Telefone Fax",
        "Telefone Recado",
        "Telefone Residencial"
    ]
]

def cruzar_agendados(base_telefones, df_agendados):

    colunas_telefones = [
        "Telefone Celular",
        "Telefone Comercial",
        "Telefone Fax",
        "Telefone Recado",
        "Telefone Residencial"
    ]

    nome_preenchido = (
        base_telefones["nome_normalizado"].notna()
        & base_telefones["nome_normalizado"].ne(""))

    base_valida = base_telefones.loc[nome_preenchido].copy()

    contagem = base_valida["nome_normalizado"].value_counts()

    df_cruzados = df_agendados.copy()
    
    df_cruzados["quantidade_base"] = (
        df_cruzados["nome_normalizado"]
        .map(contagem)
        .fillna(0)
        .astype(int)
    )

    nome_unico = base_valida["nome_normalizado"].map(contagem).eq(1)

    base_unica = base_valida.loc[nome_unico]

    df_cruzados = df_cruzados.merge(
        base_unica,
        on="nome_normalizado",
        how="left",
        validate="many_to_one"
    )

    df_cruzados[colunas_telefones] = (
        df_cruzados[colunas_telefones].replace(
        r"^\s*-?\s*$",
        pd.NA,
        regex=True
        )
    )

    tem_telefone = df_cruzados[colunas_telefones].notna().any(axis=1)

    quantidade = df_cruzados["quantidade_base"]

    df_cruzados["status"] = "não encontrado"

    df_cruzados.loc[
        quantidade.eq(1) & ~tem_telefone, "status"
    ] = "sem telefone"

    df_cruzados.loc[
        quantidade.eq(1) & tem_telefone, "status"
    ] = "encontrado"

    df_cruzados.loc[
        quantidade.gt(1), "status"
    ] = "ambíguo"

    return df_cruzados

def cruzar_efetivados(base_telefones, df_efetivados):

    colunas_telefones = [
        "Telefone Celular",
        "Telefone Comercial",
        "Telefone Fax",
        "Telefone Recado",
        "Telefone Residencial"
    ]

    nome_preenchido = (
        base_telefones["nome_normalizado"].notna()
        & base_telefones["nome_normalizado"].ne(""))

    base_valida = base_telefones.loc[nome_preenchido].copy()

    contagem = base_valida["nome_normalizado"].value_counts()

    df_cruzados = df_efetivados.copy()
    
    df_cruzados["quantidade_base"] = (
        df_cruzados["nome_normalizado"]
        .map(contagem)
        .fillna(0)
        .astype(int)
    )

    nome_unico = base_valida["nome_normalizado"].map(contagem).eq(1)

    base_unica = base_valida.loc[nome_unico]

    df_cruzados = df_cruzados.merge(
        base_unica,
        on="nome_normalizado",
        how="left",
        validate="many_to_one"
    )

    df_cruzados[colunas_telefones] = (
            df_cruzados[colunas_telefones].replace(
            r"^\s*-?\s*$",
            pd.NA,
            regex=True
            )
        )
    
    tem_telefone = df_cruzados[colunas_telefones].notna().any(axis=1)

    quantidade = df_cruzados["quantidade_base"]

    df_cruzados["status"] = "não encontrado"

    df_cruzados.loc[
        quantidade.eq(1) & ~tem_telefone, "status"
    ] = "sem telefone"

    df_cruzados.loc[
        quantidade.eq(1) & tem_telefone, "status"
    ] = "encontrado"

    df_cruzados.loc[
        quantidade.gt(1), "status"
    ] = "ambíguo"

    return df_cruzados

df_efetivados_cruzados = cruzar_efetivados(base_telefones, df_efetivados)
df_agendados_cruzados = cruzar_agendados(base_telefones, df_agendados)

#Lista apenas com os telefones agendados
#Separar apenas os encontrados
df_telefones_agendados_encontrados = df_agendados_cruzados.loc[
    df_agendados_cruzados["status"].eq("encontrado")
]


df_telefones_agendados = df_telefones_agendados_encontrados.melt(
    value_vars=["Telefone Celular", "Telefone Comercial", "Telefone Fax", "Telefone Recado", "Telefone Residencial"],
    var_name="tipo_telefone",
    value_name="telefone",
)

df_telefones_agendados = df_telefones_agendados.dropna(subset=["telefone"])

#Limpar telefones agendados
telefones_limpos_agendados = (
    df_telefones_agendados["telefone"]
    .astype("string")
    .str.replace(r"[\s-]+", "", regex=True)                
)

#Separar DDD
partes_agendados = telefones_limpos_agendados.str.extract(
    r"^\(([0-9]{2})\)([0-9]{8,9})$"
)

partes_agendados.columns = ["DDD", "telefone"]

formato_aceito_agendados = partes_agendados.notna().all(axis=1)

df_telefones_agendados_revisar = df_telefones_agendados.loc[
    ~formato_aceito_agendados
].copy()

df_envio_agendados = partes_agendados.loc[formato_aceito_agendados].copy()

df_envio_agendados.insert(0, "DDI", "55")

df_envio_agendados = df_envio_agendados.drop_duplicates(
    subset=["DDI", "DDD", "telefone"]
).reset_index(drop=True)

#Lista apenas com os telefones efetivados
df_telefones_efetivados_encontrados = df_efetivados_cruzados.loc[
    df_efetivados_cruzados["status"].eq("encontrado")
]

df_telefones_efetivados = df_telefones_efetivados_encontrados.melt(
    value_vars=["Telefone Celular", "Telefone Comercial", "Telefone Fax", "Telefone Recado", "Telefone Residencial"],
    var_name="tipo_telefone",
    value_name="telefone",
)

df_telefones_efetivados = df_telefones_efetivados.dropna(subset=["telefone"])

#Limpar telefones efetivados
telefones_limpos_efetivados = (
    df_telefones_efetivados["telefone"]
    .astype("string")
    .str.replace(r"[\s-]+", "", regex=True)                
)

#Separar DDD
partes_efetivados = telefones_limpos_efetivados.str.extract(
    r"^\(([0-9]{2})\)([0-9]{8,9})$"
)

partes_efetivados.columns = ["DDD", "telefone"]

formato_aceito_efetivados = partes_efetivados.notna().all(axis=1)

df_telefones_efetivados_revisar = df_telefones_efetivados.loc[
    ~formato_aceito_efetivados
].copy()

df_envio_efetivados = partes_efetivados.loc[formato_aceito_efetivados].copy()

df_envio_efetivados.insert(0, "DDI", "55")

df_envio_efetivados = df_envio_efetivados.drop_duplicates(
    subset=["DDI", "DDD", "telefone"]
).reset_index(drop=True)

#Transformar em Excel
df_envio_agendados.to_excel(
    r"Saídas\Envio Agendados.xlsx",
    columns=["DDI", "DDD", "telefone"],
    index=False,
)

df_envio_efetivados.to_excel(
    r"Saídas\Envio Efetivados.xlsx",
    columns=["DDI", "DDD", "telefone"],
    index=False,
)
