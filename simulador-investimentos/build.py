#!/usr/bin/env python3
"""
Gerador do Simulador de Investimentos.

A planilha é um ARTEFATO GERADO: o código-fonte é este projeto Python. Isso
resolve o problema mais chato de planilha profissional — manutenção. Para
mudar uma fórmula do motor, muda-se aqui e roda-se de novo; nada de sair
arrastando célula em 20 mil linhas e torcer para não quebrar uma referência.

    python3 build.py [caminho_de_saida.xlsx] [--sem-recalculo]

Ao final, se o LibreOffice estiver instalado, os valores já são preenchidos —
assim o arquivo entregue mostra os números em qualquer visualizador. Não é
obrigatório: a planilha pede recálculo sozinha ao abrir no Excel.
"""

import os
import sys
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import refs as R                       # noqa: E402
from src.estilo import define_nome              # noqa: E402
from src import abas_dados, carga, motor, interface    # noqa: E402

SAIDA_PADRAO = Path(__file__).resolve().parent / "Simulador_Investimentos.xlsx"


def montar():
    # Dados externos (mercado.json / produtos.csv) entram antes de qualquer aba.
    carga.aplicar()

    wb = Workbook()
    wb.remove(wb.active)
    for nome in R.ORDEM_ABAS:
        wb.create_sheet(nome)

    # Nomes definidos primeiro: as fórmulas de todas as abas dependem deles.
    for nome, ref in R.NOMES.items():
        define_nome(wb, nome, ref)

    # Camada de dados
    abas_dados.construir_produtos(wb)
    abas_dados.construir_premissas(wb)
    abas_dados.construir_fontes(wb)
    abas_dados.construir_glossario(wb)

    # Camada de cálculo
    motor.construir_motor(wb)
    motor.construir_motor_imovel(wb)
    motor.construir_adequacao(wb)

    # Camada de interface
    interface.construir_inicio(wb)
    interface.construir_cliente(wb)
    interface.construir_comparar(wb)
    interface.construir_consultor(wb)
    interface.construir_mesames(wb)
    interface.construir_imovel(wb)
    interface.construir_previdencia(wb)
    interface.construir_relatorio(wb)

    wb.active = wb.index(wb[R.AB_INICIO])
    for nome in (R.AB_MOTOR, R.AB_MOTOR_IMOVEL, R.AB_ADEQUACAO):
        wb[nome].sheet_state = "visible"   # visíveis de propósito: o consultor
                                           # precisa poder auditar cada número
    # Faz Excel e LibreOffice recalcularem tudo ao abrir. openpyxl não grava
    # valores em cache, então sem isso a planilha abriria com células em branco
    # em qualquer visualizador que só leia o cache.
    wb.calculation.fullCalcOnLoad = True

    wb.properties.title = "Simulador de Investimentos"
    wb.properties.subject = "Ferramenta de apoio à venda consultiva de investimentos"
    wb.properties.creator = "Gerado por build.py — ver README.md"
    return wb


def recalcular(caminho):
    """Preenche os valores usando o LibreOffice, se ele estiver instalado.

    Não é obrigatório: a planilha já pede recálculo ao abrir. Serve para o
    arquivo entregue mostrar os números em qualquer visualizador, inclusive
    os que só leem o valor em cache.
    """
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("soffice"):
        print("    (soffice não encontrado — a planilha recalcula sozinha ao abrir)")
        return
    macro = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">\n'
             '<script:module xmlns:script="http://openoffice.org/2000/script" '
             'script:name="Module1" script:language="StarBasic">\n'
             'Sub RecalculateAndSave()\n ThisComponent.calculateAll()\n'
             ' ThisComponent.store()\n ThisComponent.close(True)\nEnd Sub\n</script:module>')
    with tempfile.TemporaryDirectory(prefix="perfil_lo_") as perfil:
        url = Path(perfil).as_uri()
        env = {**os.environ, "SAL_USE_VCLPLUGIN": "svp"}
        try:
            subprocess.run(["soffice", "--headless", "--terminate_after_init",
                            f"-env:UserInstallation={url}"],
                           capture_output=True, timeout=120, env=env)
            destino = Path(perfil) / "user" / "basic" / "Standard"
            destino.mkdir(parents=True, exist_ok=True)
            (destino / "Module1.xba").write_text(macro)
            subprocess.run(
                ["soffice", "--headless", "--norestore", f"-env:UserInstallation={url}",
                 "vnd.sun.star.script:Standard.Module1.RecalculateAndSave"
                 "?language=Basic&location=application", str(Path(caminho).absolute())],
                capture_output=True, timeout=900, env=env)
            print("    valores preenchidos pelo LibreOffice")
        except Exception as e:
            print(f"    (recálculo pulado: {type(e).__name__} — a planilha recalcula ao abrir)")


def main():
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    saida = Path(argumentos[0]) if argumentos else SAIDA_PADRAO
    wb = montar()
    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)

    n_formulas = 0
    for ws in wb.worksheets:
        for linha in ws.iter_rows():
            for c in linha:
                if isinstance(c.value, str) and c.value.startswith("="):
                    n_formulas += 1
    print(f"OK  {saida}")
    print(f"    {len(wb.sheetnames)} abas · {n_formulas:,} fórmulas · "
          f"{len(wb.defined_names)} nomes definidos")
    if "--sem-recalculo" not in sys.argv:
        recalcular(saida)


if __name__ == "__main__":
    main()
