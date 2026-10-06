"""Inicialização comum para os programas executados por duplo clique."""

import os
from pathlib import Path
import sys
import traceback


def executar(titulo, tarefa):
    pasta = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent.parent
    )
    codigo = 0
    try:
        os.chdir(pasta)
        print(f"{titulo}\nPasta de trabalho: {pasta}\n", flush=True)
        if not Path("Entradas").is_dir():
            raise FileNotFoundError(
                "Crie a pasta Entradas ao lado do executável e coloque nela as planilhas."
            )
        Path("Saídas").mkdir(exist_ok=True)
        tarefa()
        print("\nConcluído. Consulte as planilhas na pasta Saídas.")
    except Exception as erro:
        codigo = 1
        print(f"\nERRO: {erro}")
        if isinstance(erro, PermissionError):
            print("Feche as planilhas abertas no Excel e verifique a permissão da pasta.")
        try:
            pasta_logs = pasta / "Logs"
            pasta_logs.mkdir(exist_ok=True)
            log = pasta_logs / f"{titulo} - erro.log"
            log.write_text(traceback.format_exc(), encoding="utf-8")
            print(f"Detalhes do erro: {log}")
        except OSError:
            traceback.print_exc()
    finally:
        if "--sem-pausa" not in sys.argv:
            try:
                input("\nPressione Enter para fechar...")
            except (EOFError, OSError):
                pass
    return codigo
