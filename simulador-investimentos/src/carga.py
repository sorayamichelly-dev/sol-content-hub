"""
CARGA DE DADOS EXTERNOS — o que faz a atualização automática funcionar sem
quebrar a planilha.

Por que existe: openpyxl não sabe reler gráficos. Se um script abrisse a
planilha pronta para trocar uma taxa e salvasse por cima, os quatro gráficos
sumiriam. Então o caminho é o contrário — os dados vivem em arquivos, e a
planilha é sempre REGERADA a partir deles:

    dados/mercado.json    indicadores buscados no Banco Central
    dados/produtos.csv    a base de produtos, como você a deixou no Excel

Ciclo de manutenção:
    1. python3 scripts/atualizar_dados.py            (BCB -> dados/mercado.json)
    2. python3 scripts/exportar_produtos.py X.xlsx   (Excel -> dados/produtos.csv)
    3. python3 build.py                              (regera com tudo dentro)

Se nenhum dos dois arquivos existir, valem os valores de referência de
dados_seed.py e nada quebra.
"""

import csv
import json
from pathlib import Path

from . import dados_seed as D

RAIZ = Path(__file__).resolve().parent.parent
DIR_DADOS = RAIZ / "dados"
ARQ_MERCADO = DIR_DADOS / "mercado.json"
ARQ_PRODUTOS = DIR_DADOS / "produtos.csv"

# Campos numéricos da base de produtos (o CSV guarda tudo como texto)
_NUM = {
    "% do benchmark", "Spread a.a.", "Taxa adm. a.a.", "Taxa perf. (%)",
    "Carreg. entrada", "Carreg. saída", "Custódia a.a.", "Base tributável",
    "Carência (dias)", "Liquidez (dias)", "Aplicação mínima",
    "Aporte mín. mensal", "Risco (1-5)", "Volatilidade a.a.",
    "Rent. 12m (obs.)", "Rent. 36m a.a. (obs.)",
}


def _num(valor):
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return valor


def carregar_mercado(macro=None, verboso=True):
    """Sobrescreve os indicadores macro com o que o script de atualização buscou.

    Devolve (macro_atualizado, data_referencia).
    """
    macro = list(macro if macro is not None else D.MACRO)
    if not ARQ_MERCADO.exists():
        if verboso:
            print("    dados/mercado.json não encontrado — usando valores de referência.")
        return macro, D.DATA_REFERENCIA

    dados = json.loads(ARQ_MERCADO.read_text(encoding="utf-8"))
    cenarios = dados.get("cenarios", {})
    data = dados.get("data_referencia", D.DATA_REFERENCIA)

    atualizados = []
    for linha in macro:
        cod = linha[0]
        if cod in cenarios:
            c = cenarios[cod]
            linha = (cod, linha[1], c.get("conservador"), c.get("base"),
                     c.get("otimista"), linha[5],
                     c.get("fonte", linha[6]), c.get("tipo", linha[7]))
        atualizados.append(linha)

    if verboso:
        print(f"    dados/mercado.json de {data}: "
              f"{len(cenarios)} indicadores atualizados.")
    return atualizados, data


def carregar_produtos(produtos=None, verboso=True):
    """Substitui a base de produtos pelo CSV exportado da planilha, se existir."""
    if not ARQ_PRODUTOS.exists():
        if verboso:
            print("    dados/produtos.csv não encontrado — usando a base de referência.")
        return list(produtos if produtos is not None else D.PRODUTOS)

    colunas = [c[0] for c in D.COLUNAS_PRODUTOS]
    linhas = []
    with ARQ_PRODUTOS.open(encoding="utf-8-sig", newline="") as f:
        for reg in csv.DictReader(f):
            if not (reg.get("Nome do produto") or "").strip():
                continue
            linhas.append(tuple(
                _num(reg.get(c)) if c in _NUM else (reg.get(c) or None)
                for c in colunas))

    if verboso:
        print(f"    dados/produtos.csv: {len(linhas)} produtos carregados.")
    return linhas


def aplicar(verboso=True):
    """Aplica todos os dados externos disponíveis sobre o módulo de sementes."""
    if verboso:
        print("Carregando dados externos:")
    D.MACRO, D.DATA_REFERENCIA = carregar_mercado(verboso=verboso)
    D.PRODUTOS = carregar_produtos(verboso=verboso)
