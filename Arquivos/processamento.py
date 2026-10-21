import pandas as pd

def processar_nomes_telefones_base():
    df = pd.read_excel(
        r"Entradas\Telefones de Associados 3251.xlsx",
        usecols=["Nome Cliente", "Telefone Celular", "Telefone Comercial", "Telefone Fax", "Telefone Recado", "Telefone Residencial", "Email"]
    )
    df = df.rename(columns={"Nome Cliente": "Cliente", "Email": "email"})

    # A nova base usa -2 para indicar ausência de telefone.
    colunas_telefones = [
        "Telefone Celular", "Telefone Comercial", "Telefone Fax",
        "Telefone Recado", "Telefone Residencial",
    ]
    df[colunas_telefones] = df[colunas_telefones].replace(
        [-2, "-2"], pd.NA
    )
    df["email"] = df["email"].astype("string").str.strip()
    df["email"] = df["email"].mask(
        df["email"].str.upper().isin(["", "NÃO INFORMADO"]), pd.NA
    )

    df["nome"] = df["Cliente"].str.replace(
        r"^\d{1,3}(?:\.\d{3}){2}\s+",
        "",
        regex=True
    )

    return df
    
def processar_nomes_agendados():
    df = pd.read_excel(
        r"Entradas\Nomes Agendados.xlsx",
    )

    df = df.rename(columns={"NOMES": "nome"})

    return df

def processar_nomes_efetivados():
    df = pd.read_excel(
        r"Entradas\Nomes Efetivados.xlsx",
    )

    df = df.rename(columns={"NOMES": "nome"})

    return df

def processar_resultados():
    df = pd.read_excel(
        r"Entradas\Resultados.xlsx",
        usecols=["Desc. Template", "Número do cliente", "Status"]
    )

    return df

#print(processar_nomes_telefones_base())
#print(processar_nomes_agendados())
#print(processar_nomes_efetivados())

