import pandas as pd
import unicodedata

def remover_acentos(valor):
    if pd.isna(valor):
        return valor

    valor = unicodedata.normalize('NFKD', valor)
    return "".join(
        caractere
        for caractere in valor
        if not unicodedata.combining(caractere)
    )

def normalizar_nomes(coluna):
    coluna = coluna.astype("string")

    coluna = coluna.str.strip()
    coluna = coluna.str.replace(r"\s+", " ", regex=True)
    # O mesmo prefixo cadastral deve ser removido na base e nas listas de nomes.
    coluna = coluna.str.replace(r"^\d{1,3}(?:\.\d{3}){2}\s+", "", regex=True)
    coluna = coluna.str.upper()
    coluna = coluna.apply(remover_acentos)

    return coluna
