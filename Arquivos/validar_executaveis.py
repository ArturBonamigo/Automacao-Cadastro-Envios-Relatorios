"""Compara os executáveis aos scripts, usando cópias locais das entradas."""

from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

import pandas as pd


def rodar(comando, pasta, esperado=0):
    resultado = subprocess.run(
        [str(item) for item in comando], cwd=pasta,
        capture_output=True, text=True, errors="replace", timeout=180,
    )
    if resultado.returncode != esperado:
        raise AssertionError(
            f"Retorno {resultado.returncode}, esperado {esperado}.\n"
            f"{resultado.stdout}\n{resultado.stderr}"
        )
    return resultado


def main():
    arquivos = Path(__file__).resolve().parent
    raiz = arquivos.parent
    teste = arquivos / "build" / f"validacao-{uuid4().hex[:8]}"
    referencia = teste / "referencia"
    referencia.mkdir(parents=True)
    shutil.copytree(raiz / "Entradas", referencia / "Entradas")
    (referencia / "Saídas").mkdir()
    rodar([sys.executable, arquivos / "cruzamentos.py"], referencia)
    rodar([sys.executable, arquivos / "relatorios.py"], referencia)

    for nome, prefixo in [("Gerar Envios", "Envio"), ("Gerar Relatorios", "Resultados")]:
        destino = teste / nome
        destino.mkdir()
        exe = destino / f"{nome}.exe"
        shutil.copy2(raiz / exe.name, exe)
        shutil.copytree(raiz / "Entradas", destino / "Entradas")
        if prefixo == "Envio":
            # O gerador de envios deve funcionar antes de haver resultados.
            (destino / "Entradas" / "Resultados.xlsx").unlink()
        rodar([exe, "--sem-pausa"], raiz)
        esperados = sorted((referencia / "Saídas").glob(f"{prefixo} *.xlsx"))
        obtidos = sorted((destino / "Saídas").glob("*.xlsx"))
        assert esperados, "Nenhuma saída de referência foi gerada."
        assert [p.name for p in esperados] == [p.name for p in obtidos]
        for esperado, obtido in zip(esperados, obtidos):
            pd.testing.assert_frame_equal(pd.read_excel(esperado), pd.read_excel(obtido))
            print(f"OK: {nome} / {obtido.name} idêntico ao script original.")

        # Verifica também os inicializadores .py na nova pasta Arquivos.
        fontes = destino / "Arquivos"
        fontes.mkdir()
        for fonte in arquivos.glob("*.py"):
            shutil.copy2(fonte, fontes / fonte.name)
        inicializador = "gerar_envios.py" if prefixo == "Envio" else "gerar_relatorios.py"
        rodar([sys.executable, fontes / inicializador, "--sem-pausa"], raiz)
        for esperado, obtido in zip(esperados, obtidos):
            pd.testing.assert_frame_equal(pd.read_excel(esperado), pd.read_excel(obtido))
        print(f"OK: {nome} funciona também pelo código em Arquivos.")

        shutil.move(str(destino / "Entradas"), str(destino / "Entradas-teste"))
        erro = rodar([exe, "--sem-pausa"], raiz, esperado=1)
        assert "Entradas" in erro.stdout
        assert (destino / "Logs" / f"{nome} - erro.log").is_file()
        assert sorted(p.name for p in destino.iterdir() if p.is_file()) == [exe.name]
        print(f"OK: {nome} salva o erro em Logs e mantém apenas o exe solto na raiz.")

    print(f"Validação concluída. Cópias de teste em: {teste}")


if __name__ == "__main__":
    main()
