#!/usr/bin/env python3
"""
ATUALIZAÇÃO AUTOMÁTICA DE DADOS DE MERCADO.

Busca os indicadores no Banco Central (API pública SGS) e grava
`dados/mercado.json`. Depois é só rodar `python3 build.py` — a planilha nasce
com os números novos e com a data de atualização carimbada.

    python3 scripts/atualizar_dados.py
    python3 scripts/atualizar_dados.py --mostrar        (só exibe, não grava)
    python3 scripts/atualizar_dados.py --fundo 00.000.000/0001-00 --meses 12

O QUE É E O QUE NÃO É TEMPO REAL
--------------------------------
Nada aqui é cotação em tempo real, e a planilha diz isso em toda tela:
  Selic (meta)      série 432    valor vigente, muda em reunião do Copom
  CDI               série 4389   taxa anualizada, divulgada em D+1
  IPCA              série 433    MENSAL, divulgado com defasagem de semanas
  TR                série 226    mensal
  IGP-M             série 189    mensal
  Cota de fundo     CVM          diária, publicada com 2 a 5 dias úteis de atraso

Bolsa, câmbio e imóvel continuam sendo PREMISSA do consultor: são projeções,
não observações, e a planilha não finge o contrário.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:                                   # pragma: no cover
    sys.exit("Instale a biblioteca requests:  pip install requests")

RAIZ = Path(__file__).resolve().parent.parent
DIR_DADOS = RAIZ / "dados"
SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados/ultimos/{n}?formato=json"

SERIES = {
    "SELIC": (432, 1, "anual", "Banco Central — SGS série 432 (meta Selic)", "Vigente (muda no Copom)"),
    "CDI":   (4389, 5, "anual", "Banco Central — SGS série 4389 (CDI anualizado)", "Diário (D+1)"),
    "IPCA":  (433, 12, "mensal", "IBGE via BCB — SGS série 433 (IPCA mensal)", "Mensal (com defasagem)"),
    "TR":    (226, 12, "mensal", "Banco Central — SGS série 226 (TR mensal)", "Mensal"),
}

# Como os cenários se afastam do observado, em pontos percentuais.
# Ajuste aqui se quiser cenários mais ou menos abertos.
DESVIOS = {
    "SELIC":    (-0.030, 0.0, +0.020),
    "CDI":      (-0.030, 0.0, +0.020),
    "IPCA":     (+0.015, 0.0, -0.005),
    "TR":       (-0.005, 0.0, +0.006),
    "IBOV":     (-0.060, 0.0, +0.060),
    "CAMBIO":   (-0.020, 0.0, +0.040),
    "IMOB_VAL": (-0.020, 0.0, +0.030),
    "IMOB_YLD": (-0.010, 0.0, +0.010),
}

# Indicadores que a API não fornece: seguem como premissa do consultor.
PREMISSAS_MANUAIS = {
    "IBOV":     (0.10, "Premissa do consultor — histórico da B3", "Premissa"),
    "CAMBIO":   (0.04, "Premissa do consultor — PTAX histórica", "Premissa"),
    "IMOB_VAL": (0.04, "Premissa do consultor — Índice FipeZAP", "Mensal (com defasagem)"),
    "IMOB_YLD": (0.06, "Premissa do consultor — FipeZAP aluguel", "Mensal (com defasagem)"),
}


def _buscar(cod, n, tempo=30):
    r = requests.get(SGS.format(cod=cod, n=n), timeout=tempo)
    r.raise_for_status()
    return [(d["data"], float(d["valor"].replace(",", "."))) for d in r.json()]


def _anualizar_mensal(valores):
    """Compõe 12 variações mensais (em %) numa taxa anual (fração)."""
    fator = 1.0
    for _data, v in valores[-12:]:
        fator *= (1 + v / 100)
    return fator - 1


def buscar_indicadores():
    """Devolve {codigo: (valor_base, fonte, tipo)} e a data mais recente vista."""
    obtidos, data_max = {}, None
    for cod, (serie, n, modo, fonte, tipo) in SERIES.items():
        try:
            dados = _buscar(serie, n)
        except Exception as e:                          # rede, proxy, indisponibilidade
            print(f"  ! {cod}: falhou ({type(e).__name__}). Mantendo o valor atual.")
            continue
        valor = (_anualizar_mensal(dados) if modo == "mensal"
                 else dados[-1][1] / 100)
        obtidos[cod] = (valor, fonte, tipo)
        data_max = max(data_max or dados[-1][0], dados[-1][0])
        print(f"  ✓ {cod:8s} {valor:8.2%}   ({fonte})")
    return obtidos, data_max


def montar_cenarios(obtidos):
    cenarios = {}
    for cod, (base, fonte, tipo) in obtidos.items():
        d = DESVIOS.get(cod, (0.0, 0.0, 0.0))
        cenarios[cod] = {
            "conservador": round(max(0.0, base + d[0]), 6),
            "base": round(base, 6),
            "otimista": round(base + d[2], 6),
            "fonte": fonte, "tipo": tipo,
        }
    for cod, (base, fonte, tipo) in PREMISSAS_MANUAIS.items():
        d = DESVIOS[cod]
        cenarios.setdefault(cod, {
            "conservador": round(base + d[0], 6),
            "base": round(base, 6),
            "otimista": round(base + d[2], 6),
            "fonte": fonte, "tipo": tipo,
        })
    return cenarios


# --------------------------------------------------------------------------
# Rentabilidade e volatilidade reais de um fundo, pelo Informe Diário da CVM
# --------------------------------------------------------------------------
def historico_fundo(cnpj, meses=12):
    """Baixa o Informe Diário da CVM e devolve retorno do período e volatilidade.

    Atenção: cada arquivo mensal tem dezenas de MB. Use só quando precisar
    atualizar a coluna de rentabilidade observada de um fundo específico.
    """
    import csv
    import io
    import zipfile
    from datetime import datetime
    from statistics import pstdev

    base = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{ym}.zip"
    hoje = date.today()
    cotas = []
    for k in range(meses, -1, -1):
        ano = hoje.year + (hoje.month - 1 - k) // 12
        mes = (hoje.month - 1 - k) % 12 + 1
        url = base.format(ym=f"{ano}{mes:02d}")
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
        except Exception:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for nome in z.namelist():
                with z.open(nome) as fh:
                    leitor = csv.DictReader(io.TextIOWrapper(fh, "latin-1"), delimiter=";")
                    for reg in leitor:
                        if reg.get("CNPJ_FUNDO", "").strip() == cnpj:
                            cotas.append((datetime.strptime(reg["DT_COMPTC"], "%Y-%m-%d"),
                                          float(reg["VL_QUOTA"])))
    if len(cotas) < 30:
        return None
    cotas.sort()
    retornos = [cotas[i][1] / cotas[i - 1][1] - 1 for i in range(1, len(cotas))]
    return {
        "cnpj": cnpj,
        "de": cotas[0][0].isoformat()[:10],
        "ate": cotas[-1][0].isoformat()[:10],
        "retorno_periodo": round(cotas[-1][1] / cotas[0][1] - 1, 6),
        "volatilidade_anual": round(pstdev(retornos) * (252 ** 0.5), 6),
        "observacoes": len(cotas),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mostrar", action="store_true", help="só exibe, não grava o arquivo")
    ap.add_argument("--fundo", metavar="CNPJ", help="também busca o histórico deste fundo na CVM")
    ap.add_argument("--meses", type=int, default=12, help="meses de histórico do fundo")
    args = ap.parse_args()

    print("Buscando indicadores no Banco Central (API pública SGS)…")
    obtidos, data_serie = buscar_indicadores()
    if not obtidos:
        sys.exit("\nNenhum indicador pôde ser buscado. Verifique a conexão ou o proxy da rede.\n"
                 "A planilha continua funcionando com os valores atuais.")

    saida = {
        "data_referencia": date.today().isoformat(),
        "ultima_data_das_series": data_serie,
        "cenarios": montar_cenarios(obtidos),
        "aviso": ("Indicadores observados no Banco Central. Bolsa, câmbio e imóvel são "
                  "PREMISSAS do consultor, não observações. Nada aqui é cotação em tempo real."),
    }

    if args.fundo:
        print(f"\nBuscando o histórico do fundo {args.fundo} na CVM (pode demorar)…")
        h = historico_fundo(args.fundo, args.meses)
        if h:
            saida["fundo"] = h
            print(f"  ✓ retorno do período {h['retorno_periodo']:.2%} · "
                  f"volatilidade {h['volatilidade_anual']:.2%} "
                  f"({h['observacoes']} cotas, de {h['de']} a {h['ate']})")
        else:
            print("  ! não foi possível montar o histórico desse CNPJ.")

    if args.mostrar:
        print("\n" + json.dumps(saida, indent=2, ensure_ascii=False))
        return

    DIR_DADOS.mkdir(exist_ok=True)
    destino = DIR_DADOS / "mercado.json"
    destino.write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGravado em {destino}")
    print("Agora rode:  python3 build.py    (a planilha nasce com os dados novos)")


if __name__ == "__main__":
    main()
