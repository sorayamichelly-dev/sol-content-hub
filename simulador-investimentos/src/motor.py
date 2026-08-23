"""
CAMADA DE CÁLCULO — abas Motor, MotorImovel e Adequação.

Regra de ouro desta camada: nada é digitado aqui. Tudo é fórmula que lê a
camada de DADOS (Produtos / Premissas) e as entradas da camada de INTERFACE
(Cliente / Consultor / Imóvel). Por isso a alteração de uma taxa nunca exige
reconstruir fórmula alguma.

Sequência de cálculo de cada mês t (aba Motor):
    saldo inicial      = saldo final do mês anterior
    aporte             = aporte do cliente (+ restituição do PGBL, se reinvestida)
    custo de entrada   = aporte × carregamento
    rendimento bruto   = saldo inicial × taxa mensal bruta
    taxa de adm.       = saldo inicial × (adm + custódia) / 12
    taxa de performance= % sobre o que o rendimento excedeu o benchmark
    come-cotas         = em maio e novembro, alíquota × ganho ainda não tributado
    saldo final        = saldo inicial + rendimento − custos + aporte líquido − come-cotas
    IR no resgate      = alíquota(prazo) × base tributável − come-cotas já pago
    valor líquido      = saldo final − IR no resgate − carregamento de saída
"""

from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

from .estilo import *          # noqa: F403
from .refs import *            # noqa: F403
from . import dados_seed as D


# --------------------------------------------------------------------------
# Atalhos
# --------------------------------------------------------------------------
def _pcol(campo):
    """Letra da coluna de um campo na aba Produtos."""
    return get_column_letter(PROD_COL[campo])


def _pfaixa(campo):
    c = _pcol(campo)
    return f"{AB_PRODUTOS}!${c}${PROD_LIN_INI}:${c}${PROD_LIN_FIM}"


def _slot_col(k):
    return get_column_letter(MOT_COL_SLOT0 + k)


def _p(k, rotulo):
    """Referência absoluta a uma linha do slot k — bloco de parâmetros ou de resumo.

    Os dois blocos usam as mesmas colunas (B..G) e não têm rótulos repetidos,
    então um único atalho serve para os dois.
    """
    linha = MOT_P.get(rotulo, MOT_R.get(rotulo))
    if linha is None:
        raise KeyError(f"rótulo desconhecido no Motor: {rotulo!r}")
    return f"${_slot_col(k)}${linha}"


def _gc(k, campo):
    """Letra da coluna de um campo da grade mensal, para o slot k."""
    return get_column_letter(MOT_SLOT_COL0 + k * MOT_SLOT_PASSO + MOT_G[campo])


# ==========================================================================
# ABA MOTOR
# ==========================================================================
def construir_motor(wb):
    ws = wb[AB_MOTOR]
    esconde_grade(ws)
    titulo_pagina(ws, "MOTOR DE SIMULAÇÃO",
                  "Camada de cálculo — nenhuma célula desta aba é digitada; tudo vem de Produtos, "
                  "Premissas e das respostas do cliente", ate_col="J")
    larguras(ws, {"A": 40, "B": 17, "C": 17, "D": 17, "E": 17, "F": 17, "G": 17})

    # ------------------------------ parâmetros ------------------------------
    secao(ws, 4, "BLOCO 1 · PARÂMETROS RESOLVIDOS DE CADA ALTERNATIVA", ate_col="J")
    escreve(ws, f"A{MOT_PAR_CAB}", "Parâmetro", tam=9, negrito=True, cor=BRANCO,
            bg=AZUL, alinha=AL_ESQ, borda=BORDA_GRADE)
    for k, L in enumerate(SLOT_LETRAS):
        escreve(ws, f"{_slot_col(k)}{MOT_PAR_CAB}", f"ALTERNATIVA {L}", tam=9,
                negrito=True, cor=BRANCO, bg=AZUL, alinha=AL_CENTRO, borda=BORDA_GRADE)

    fmts = {
        "% do benchmark": FMT_PCT, "Spread a.a.": FMT_PCT2,
        "Retorno a.a. do benchmark puro": FMT_PCT2,
        "Retorno BRUTO a.a. (cenário)": FMT_PCT2,
        "Taxa mensal do benchmark": FMT_PCT2, "Taxa mensal bruta": FMT_PCT2,
        "Taxa de administração a.a.": FMT_PCT2, "Custódia a.a.": FMT_PCT2,
        "Custos mensais (adm + custódia)": FMT_PCT2, "Taxa de performance": FMT_PCT,
        "Carregamento de entrada": FMT_PCT2, "Carregamento de saída": FMT_PCT2,
        "Alíquota do come-cotas": FMT_PCT, "Aplicação mínima": FMT_MOEDA,
        "Volatilidade a.a.": FMT_PCT2, "Retorno LÍQUIDO a.a. estimado": FMT_PCT2,
        "Carência (dias)": FMT_INT, "Liquidez (dias)": FMT_INT, "Risco (1-5)": FMT_INT,
        "Linha na base de produtos": FMT_INT, "Alternativa em uso (1/0)": FMT_INT,
        "Base tributável (1=rend. / 2=total)": FMT_INT, "Tem come-cotas (1/0)": FMT_INT,
        "É PGBL (aporte dedutível)": FMT_INT,
    }
    for rotulo, lin in MOT_P.items():
        escreve(ws, f"A{lin}", rotulo, tam=8.5, borda=BORDA_GRADE,
                negrito=rotulo in ("Produto selecionado", "Retorno BRUTO a.a. (cenário)",
                                   "Retorno LÍQUIDO a.a. estimado"))
        ws.row_dimensions[lin].height = 13

    # Lookups diretos na base de produtos (texto -> "", número -> 0)
    lookup_texto = {
        "Categoria": "categoria", "Emissor / Gestor": "emissor",
        "Benchmark": "benchmark", "Composição": "composicao", "Garantia": "garantia",
    }
    lookup_num = {
        "% do benchmark": "pct_bench", "Spread a.a.": "spread",
        "Taxa de administração a.a.": "taxa_adm", "Custódia a.a.": "custodia",
        "Taxa de performance": "taxa_perf", "Carregamento de entrada": "carreg_ent",
        "Carregamento de saída": "carreg_sai",
        "Base tributável (1=rend. / 2=total)": "base_trib",
        "Carência (dias)": "carencia", "Liquidez (dias)": "liquidez",
        "Aplicação mínima": "aplic_min", "Risco (1-5)": "risco",
        "Volatilidade a.a.": "volatilidade",
    }

    for k, L in enumerate(SLOT_LETRAS):
        c = _slot_col(k)
        F = {}

        F["Produto selecionado"] = f"=SLOT_{L}"
        F["Linha na base de produtos"] = f"=IFERROR(MATCH({c}${MOT_P['Produto selecionado']},BASE_PRODUTOS,0),0)"
        F["Regime tributário"] = (
            f"=IF({_p(k,'Linha na base de produtos')}=0,\"\","
            f"INDEX({_pfaixa('regime')},{_p(k,'Linha na base de produtos')}))")
        F["Alternativa em uso (1/0)"] = (
            f"=IF(OR({_p(k,'Produto selecionado')}=\"\","
            f"{_p(k,'Linha na base de produtos')}=0,"
            f"{_p(k,'Regime tributário')}=\"IMOVEL\"),0,1)")

        for rotulo, campo in lookup_texto.items():
            F[rotulo] = (f"=IF({_p(k,'Linha na base de produtos')}=0,\"\","
                         f"INDEX({_pfaixa(campo)},{_p(k,'Linha na base de produtos')}))")
        for rotulo, campo in lookup_num.items():
            F[rotulo] = (f"=IF({_p(k,'Linha na base de produtos')}=0,0,"
                         f"IFERROR(INDEX({_pfaixa(campo)},{_p(k,'Linha na base de produtos')}),0))")

        F["Retorno a.a. do benchmark puro"] = (
            f"=IFERROR(INDEX(TAB_MACRO_VAL,MATCH({_p(k,'Benchmark')},TAB_MACRO_COD,0)),0)")
        F["Retorno BRUTO a.a. (cenário)"] = (
            f"=IF({_p(k,'Alternativa em uso (1/0)')}=0,0,"
            f"IF({_p(k,'Composição')}=\"MULT\","
            f"(1+{_p(k,'Retorno a.a. do benchmark puro')}*{_p(k,'% do benchmark')})"
            f"*(1+{_p(k,'Spread a.a.')})-1,"
            f"{_p(k,'Retorno a.a. do benchmark puro')}*{_p(k,'% do benchmark')}"
            f"+{_p(k,'Spread a.a.')}))")
        F["Taxa mensal do benchmark"] = (
            f"=IF({_p(k,'Retorno a.a. do benchmark puro')}<=-1,0,"
            f"(1+{_p(k,'Retorno a.a. do benchmark puro')})^(1/12)-1)")
        F["Taxa mensal bruta"] = (
            f"=IF({_p(k,'Retorno BRUTO a.a. (cenário)')}<=-1,0,"
            f"(1+{_p(k,'Retorno BRUTO a.a. (cenário)')})^(1/12)-1)")
        F["Custos mensais (adm + custódia)"] = (
            f"=({_p(k,'Taxa de administração a.a.')}+{_p(k,'Custódia a.a.')})/12")

        cc_cod = f"{AB_PREMISSAS}!$A${PRE_CC_INI}:$A${PRE_CC_FIM}"
        F["Tem come-cotas (1/0)"] = (
            f"=IFERROR(INDEX({AB_PREMISSAS}!$B${PRE_CC_INI}:$B${PRE_CC_FIM},"
            f"MATCH({_p(k,'Regime tributário')},{cc_cod},0)),0)")
        F["Alíquota do come-cotas"] = (
            f"=IFERROR(INDEX({AB_PREMISSAS}!$C${PRE_CC_INI}:$C${PRE_CC_FIM},"
            f"MATCH({_p(k,'Regime tributário')},{cc_cod},0)),0)")
        F["É PGBL (aporte dedutível)"] = (
            f"=IF({_p(k,'Base tributável (1=rend. / 2=total)')}=2,1,0)")
        F["Retorno LÍQUIDO a.a. estimado"] = (
            f"=IF({_p(k,'Alternativa em uso (1/0)')}=0,0,"
            f"(1+{_p(k,'Taxa mensal bruta')}-{_p(k,'Custos mensais (adm + custódia)')})^12-1)")

        for rotulo, formula in F.items():
            escreve(ws, f"{c}{MOT_P[rotulo]}", formula, tam=8.5,
                    cor=COR_LINK if rotulo in lookup_texto or rotulo in lookup_num
                    else COR_FORMULA,
                    fmt=fmts.get(rotulo), alinha=AL_CENTRO, borda=BORDA_GRADE,
                    negrito=rotulo in ("Produto selecionado",
                                       "Retorno BRUTO a.a. (cenário)",
                                       "Retorno LÍQUIDO a.a. estimado"),
                    bg=AZUL_CLARO if rotulo == "Produto selecionado" else None)

    # ------------------------------ resumo ------------------------------
    _bloco_resumo(ws, "BLOCO 2 · RESULTADOS NO PRAZO ESCOLHIDO PELO CLIENTE")

    for k in range(N_SLOTS):
        c = _slot_col(k)
        g = lambda campo: f"${_gc(k,campo)}${MOT_GRID_INI}:${_gc(k,campo)}${MOT_GRID_FIM}"   # noqa: E731
        no_prazo = lambda campo: f"INDEX({g(campo)},IN_PRAZO+1)"                             # noqa: E731
        soma = lambda campo: (f"SUMIF($A${MOT_GRID_INI}:$A${MOT_GRID_FIM},"                  # noqa: E731
                              f"\"<=\"&IN_PRAZO,{g(campo)})")
        ativo = _p(k, "Alternativa em uso (1/0)")
        R = {}

        R["Patrimônio bruto no prazo"] = f"=IF({ativo}=0,0,{no_prazo('saldo_fim')})"
        R["Patrimônio líquido no prazo"] = f"=IF({ativo}=0,0,{no_prazo('liquido')})"
        R["Patrimônio líquido na metade do prazo"] = (
            f"=IF({ativo}=0,0,INDEX({g('liquido')},INT(IN_PRAZO/2)+1))")
        R["Patrimônio líquido em R$ de hoje"] = f"=IF({ativo}=0,0,{no_prazo('liquido_real')})"
        R["Total investido (capital + aportes)"] = f"=IF({ativo}=0,0,{soma('aporte')})"
        R["Ganho líquido"] = (f"={_p(k,'Patrimônio líquido no prazo')}"
                              f"-{_p(k,'Total investido (capital + aportes)')}")
        R["Imposto total pago"] = (f"=IF({ativo}=0,0,{soma('come_cotas')}+{no_prazo('ir_resgate')})")
        R["Custos totais pagos"] = (
            f"=IF({ativo}=0,0,{soma('carreg_ent')}+{soma('taxa_adm')}+{soma('taxa_perf')}"
            f"+{no_prazo('saldo_fim')}*{_p(k,'Carregamento de saída')})")
        R["Rentabilidade líquida acumulada"] = (
            f"=IF({_p(k,'Total investido (capital + aportes)')}=0,0,"
            f"{_p(k,'Patrimônio líquido no prazo')}"
            f"/{_p(k,'Total investido (capital + aportes)')}-1)")
        R["Taxa líquida equivalente a.a."] = (
            f"=IF(OR({ativo}=0,IN_PRAZO=0),0,"
            f"IFERROR((1+RATE(IN_PRAZO,"
            f"-({_p(k,'Total investido (capital + aportes)')}-IN_CAPITAL)/IN_PRAZO,"
            f"-IN_CAPITAL,{_p(k,'Patrimônio líquido no prazo')}))^12-1,"
            f"(1+{_p(k,'Rentabilidade líquida acumulada')})^(12/IN_PRAZO)-1))")
        R["Ganho real a.a. (acima da inflação)"] = (
            f"=IF({ativo}=0,0,(1+{_p(k,'Taxa líquida equivalente a.a.')})/(1+IPCA_CENARIO)-1)")
        R["Alíquota de IR no prazo escolhido"] = (
            f"=IF({ativo}=0,0,IFERROR(INDEX(TAB_IR,MATCH(IN_PRAZO*30,TAB_IR_DIAS,1),"
            f"MATCH({_p(k,'Regime tributário')},TAB_IR_REGIMES,0)),0))")
        R["Renda mensal potencial (nominal)"] = (
            f"=IF({ativo}=0,0,MAX(0,{_p(k,'Patrimônio líquido no prazo')}"
            f"*({_p(k,'Taxa mensal bruta')}-{_p(k,'Custos mensais (adm + custódia)')})"
            f"*(1-{_p(k,'Alíquota de IR no prazo escolhido')})))")
        R["Renda mensal potencial (poder de compra)"] = (
            f"=IF({ativo}=0,0,MAX(0,{_p(k,'Patrimônio líquido no prazo')}"
            f"*((1+({_p(k,'Taxa mensal bruta')}-{_p(k,'Custos mensais (adm + custódia)')})"
            f"*(1-{_p(k,'Alíquota de IR no prazo escolhido')}))"
            f"/((1+IPCA_CENARIO)^(1/12))-1)))")
        R["Pode retirar a partir de"] = (
            f"=IF({ativo}=0,\"\",DATA_INICIO+{_p(k,'Carência (dias)')}"
            f"+{_p(k,'Liquidez (dias)')})")
        R["Atende à aplicação mínima (1/0)"] = (
            f"=IF({ativo}=0,0,IF(IN_CAPITAL>={_p(k,'Aplicação mínima')},1,0))")
        R["Cabe no perfil declarado (1/0)"] = (
            f"=IF({ativo}=0,0,IF({_p(k,'Risco (1-5)')}<=IFERROR(INDEX("
            f"{AB_PREMISSAS}!$B${PRE_PERFIL_INI}:$B${PRE_PERFIL_FIM},"
            f"MATCH(IN_PERFIL,{AB_PREMISSAS}!$A${PRE_PERFIL_INI}:$A${PRE_PERFIL_FIM},0)),5),1,0))")
        R["Para retirar (linguagem de cliente)"] = (
            f"=IF({ativo}=0,\"\","
            f"IF({_p(k,'Carência (dias)')}>0,"
            f"\"A partir de \"&TEXT(DATA_INICIO+{_p(k,'Carência (dias)')},\"dd/mm/yyyy\"),"
            f"IF({_p(k,'Liquidez (dias)')}<=0,\"No mesmo dia\","
            f"IF({_p(k,'Liquidez (dias)')}=1,\"Em 1 dia útil\","
            f"\"Em até \"&{_p(k,'Liquidez (dias)')}&\" dias\"))))")
        R["Oscilação (linguagem de cliente)"] = (
            f"=IF({ativo}=0,\"\",IFERROR(INDEX("
            f"{AB_PREMISSAS}!$B${PRE_RISCO_INI}:$B${PRE_RISCO_FIM},"
            f"{_p(k,'Risco (1-5)')}),\"\"))")

        for rotulo, formula in R.items():
            escreve(ws, f"{c}{MOT_R[rotulo]}", formula, tam=8.5,
                    fmt=_fmt_resumo(rotulo), alinha=AL_CENTRO, borda=BORDA_GRADE,
                    negrito=rotulo == "Patrimônio líquido no prazo",
                    bg=AZUL_CLARO if rotulo == "Patrimônio líquido no prazo" else None)

    # ------------------------------ grade mensal ------------------------------
    secao(ws, MOT_GRID_BAND - 1, "BLOCO 3 · PROJEÇÃO MÊS A MÊS", ate_col="J")
    _grade_motor(ws)

    ws.freeze_panes = f"F{MOT_GRID_INI}"
    ws.sheet_properties.tabColor = CINZA_SUAVE
    link_aba(ws, "L4", AB_INICIO, "◀ INÍCIO")
    link_aba(ws, "L5", AB_CONSULTOR, "◀ CONSULTOR")


def _fmt_resumo(rotulo):
    if rotulo in ("Rentabilidade líquida acumulada", "Taxa líquida equivalente a.a.",
                  "Ganho real a.a. (acima da inflação)", "Alíquota de IR no prazo escolhido"):
        return FMT_PCT
    if rotulo == "Pode retirar a partir de":
        return FMT_DATA
    if rotulo in ("Atende à aplicação mínima (1/0)", "Cabe no perfil declarado (1/0)"):
        return FMT_INT
    if rotulo in ("Para retirar (linguagem de cliente)", "Oscilação (linguagem de cliente)"):
        return None
    return FMT_MOEDA


def _bloco_resumo(ws, titulo, cab=None, ini=None, rotulos=None, col_ini=None):
    cab = cab or MOT_RES_CAB
    ini = ini or MOT_RES_INI
    rotulos = rotulos or MOT_RES_ROTULOS
    secao(ws, cab - 1, titulo, ate_col="J")
    escreve(ws, f"A{cab}", "Resultado", tam=9, negrito=True, cor=BRANCO, bg=AZUL_ESCURO,
            alinha=AL_ESQ, borda=BORDA_GRADE)
    if col_ini is None:
        for k, L in enumerate(SLOT_LETRAS):
            escreve(ws, f"{_slot_col(k)}{cab}", f"ALTERNATIVA {L}", tam=9, negrito=True,
                    cor=BRANCO, bg=AZUL_ESCURO, alinha=AL_CENTRO, borda=BORDA_GRADE)
    for i, rotulo in enumerate(rotulos):
        escreve(ws, f"A{ini + i}", rotulo, tam=8.5, borda=BORDA_GRADE,
                negrito=rotulo == "Patrimônio líquido no prazo")
        ws.row_dimensions[ini + i].height = 13


def _grade_motor(ws):
    """Escreve a projeção mês a mês das 6 alternativas."""
    ini, fim = MOT_GRID_INI, MOT_GRID_FIM

    # Colunas comuns
    for col, tit, larg in (("A", "Mês", 6), ("B", "Data", 11),
                           ("C", "Dias", 7), ("D", "Fator inflação", 11)):
        escreve(ws, f"{col}{MOT_GRID_CAB}", tit, tam=8, negrito=True, cor=BRANCO,
                bg=AZUL_ESCURO, alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        ws.column_dimensions[col].width = larg
    ws.row_dimensions[MOT_GRID_CAB].height = 40

    for r in range(ini, fim + 1):
        mes = r - ini
        escreve(ws, f"A{r}", mes, tam=8, fmt=FMT_INT, alinha=AL_CENTRO)
        escreve(ws, f"B{r}", f"=EDATE(DATA_INICIO,$A{r})", tam=8, fmt=FMT_DATA,
                alinha=AL_CENTRO)
        escreve(ws, f"C{r}", f"=$A{r}*30", tam=8, fmt=FMT_INT, alinha=AL_CENTRO)
        escreve(ws, f"D{r}", f"=(1+IPCA_CENARIO)^($A{r}/12)", tam=8, fmt="0.0000",
                alinha=AL_CENTRO)
        ws.row_dimensions[r].height = 12

    fmt_col = {c: FMT_MOEDA_C for c in MOT_G}

    for k, L in enumerate(SLOT_LETRAS):
        c0 = MOT_SLOT_COL0 + k * MOT_SLOT_PASSO
        col_ini = get_column_letter(c0)
        col_fim = get_column_letter(c0 + MOT_SLOT_LARGURA - 1)

        # Faixa com o nome da alternativa
        ws.merge_cells(f"{col_ini}{MOT_GRID_BAND}:{col_fim}{MOT_GRID_BAND}")
        escreve(ws, f"{col_ini}{MOT_GRID_BAND}",
                f'=IF({_p(k,"Alternativa em uso (1/0)")}=0,"ALTERNATIVA {L} — não utilizada",'
                f'"ALTERNATIVA {L} — "&{_p(k,"Produto selecionado")})',
                tam=9, negrito=True, cor=BRANCO, bg=AZUL if k % 2 == 0 else AZUL_MEDIO,
                alinha=AL_CENTRO)

        for j, titulo in enumerate(MOT_G_TITULOS):
            col = get_column_letter(c0 + j)
            escreve(ws, f"{col}{MOT_GRID_CAB}", titulo, tam=7.5, negrito=True,
                    cor=BRANCO, bg=AZUL_MEDIO, alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
            ws.column_dimensions[col].width = 13
        ws.column_dimensions[get_column_letter(c0 + MOT_SLOT_LARGURA)].width = 2

        C = {campo: _gc(k, campo) for campo in MOT_G}
        ativo = _p(k, "Alternativa em uso (1/0)")

        # ---------------- mês 0 ----------------
        r = ini
        m0 = {
            "saldo_ini": "=0",
            "aporte": f"=IF({ativo}=0,0,IN_CAPITAL)",
            "carreg_ent": f"={C['aporte']}{r}*{_p(k,'Carregamento de entrada')}",
            "rend_bruto": "=0",
            "taxa_adm": "=0",
            "taxa_perf": "=0",
            "come_cotas": "=0",
        }
        for campo, f in m0.items():
            escreve(ws, f"{C[campo]}{r}", f, tam=8, fmt=fmt_col[campo], alinha=AL_DIR)
        _linha_fechamento(ws, k, C, r, ativo, primeiro=True)

        # ---------------- meses 1 .. N ----------------
        for r in range(ini + 1, fim + 1):
            p = r - 1
            escreve(ws, f"{C['saldo_ini']}{r}", f"={C['saldo_fim']}{p}", tam=8,
                    fmt=FMT_MOEDA_C, alinha=AL_DIR)
            escreve(ws, f"{C['aporte']}{r}",
                    f"=IF({ativo}=0,0,"
                    f"IF($A{r}>IN_PRAZO,0,"
                    f"IF(APORTE_CORRIGIDO=\"Sim\",IN_APORTE*$D{r},IN_APORTE))"
                    f"+IF(AND({_p(k,'É PGBL (aporte dedutível)')}=1,"
                    f"PGBL_REINVESTE=\"Sim\",$A{r}>=13,$A{r}<=IN_PRAZO,MONTH($B{r})=5),"
                    f"PGBL_BENEFICIO,0))",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            escreve(ws, f"{C['carreg_ent']}{r}",
                    f"={C['aporte']}{r}*{_p(k,'Carregamento de entrada')}",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            escreve(ws, f"{C['rend_bruto']}{r}",
                    f"={C['saldo_ini']}{r}*{_p(k,'Taxa mensal bruta')}",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            escreve(ws, f"{C['taxa_adm']}{r}",
                    f"={C['saldo_ini']}{r}*{_p(k,'Custos mensais (adm + custódia)')}",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            escreve(ws, f"{C['taxa_perf']}{r}",
                    f"={_p(k,'Taxa de performance')}*MAX(0,{C['rend_bruto']}{r}"
                    f"-{C['saldo_ini']}{r}*{_p(k,'Taxa mensal do benchmark')})",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            # Come-cotas incide sobre o ganho AINDA NÃO TRIBUTADO, não sobre o
            # ganho acumulado inteiro. Por isso o desconto do que já foi pago
            # vem DEPOIS da alíquota: aliq × ganho_total − come-cotas_já_pago.
            # Sem esse desconto, cada semestre retributaria tudo de novo.
            escreve(ws, f"{C['come_cotas']}{r}",
                    f"=IF(AND({_p(k,'Tem come-cotas (1/0)')}=1,"
                    f"OR(MONTH($B{r})=5,MONTH($B{r})=11)),"
                    f"MAX(0,{_p(k,'Alíquota do come-cotas')}*MAX(0,"
                    f"({C['saldo_ini']}{r}+{C['rend_bruto']}{r}-{C['taxa_adm']}{r}"
                    f"-{C['taxa_perf']}{r}+{C['aporte']}{r}-{C['carreg_ent']}{r})"
                    f"+{C['cc_acum']}{p}-{C['aportado']}{r})"
                    f"-{C['cc_acum']}{p}),0)",
                    tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
            _linha_fechamento(ws, k, C, r, ativo, primeiro=False)


def _linha_fechamento(ws, k, C, r, ativo, primeiro):
    """Colunas de fechamento do mês: saldo final, base fiscal, IR e líquido."""
    p = r - 1
    escreve(ws, f"{C['saldo_fim']}{r}",
            f"={C['saldo_ini']}{r}+{C['rend_bruto']}{r}-{C['taxa_adm']}{r}"
            f"-{C['taxa_perf']}{r}+{C['aporte']}{r}-{C['carreg_ent']}{r}"
            f"-{C['come_cotas']}{r}",
            tam=8, negrito=True, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['aportado']}{r}",
            (f"={C['aporte']}{r}-{C['carreg_ent']}{r}" if primeiro
             else f"={C['aportado']}{p}+{C['aporte']}{r}-{C['carreg_ent']}{r}"),
            tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['cc_acum']}{r}",
            (f"={C['come_cotas']}{r}" if primeiro
             else f"={C['cc_acum']}{p}+{C['come_cotas']}{r}"),
            tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['ganho_trib']}{r}",
            f"={C['saldo_fim']}{r}+{C['cc_acum']}{r}-{C['aportado']}{r}",
            tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['ir_resgate']}{r}",
            f"=MAX(0,IFERROR(INDEX(TAB_IR,MATCH($C{r},TAB_IR_DIAS,1),"
            f"MATCH({_p(k,'Regime tributário')},TAB_IR_REGIMES,0)),0)"
            f"*IF({_p(k,'Base tributável (1=rend. / 2=total)')}=2,{C['saldo_fim']}{r},"
            f"MAX(0,{C['ganho_trib']}{r}))-{C['cc_acum']}{r})",
            tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['liquido']}{r}",
            f"=MAX(0,{C['saldo_fim']}{r}-{C['ir_resgate']}{r}"
            f"-{C['saldo_fim']}{r}*{_p(k,'Carregamento de saída')})",
            tam=8, negrito=True, fmt=FMT_MOEDA_C, alinha=AL_DIR)
    escreve(ws, f"{C['liquido_real']}{r}",
            f"={C['liquido']}{r}/$D{r}",
            tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR)


# ==========================================================================
# ABA MOTOR IMÓVEL
# ==========================================================================
def construir_motor_imovel(wb):
    ws = wb[AB_MOTOR_IMOVEL]
    esconde_grade(ws)
    titulo_pagina(ws, "MOTOR — IMÓVEL PARA ALUGUEL",
                  "Camada de cálculo. O imóvel tem mecânica própria (aluguel, vacância, IPTU, "
                  "manutenção, custos de compra e de venda), por isso não usa o motor financeiro.",
                  ate_col="H")
    larguras(ws, {"A": 44, "B": 18, "C": 4, "D": 64})

    P = MIM_P
    secao(ws, 4, "BLOCO 1 · PARÂMETROS RESOLVIDOS", ate_col="H")
    formulas = {
        "Entra na comparação (1/0)": '=IF(IMOV_INCLUIR="Sim",1,0)',
        "Valor do imóvel": "=IMOV_VALOR",
        "ITBI (%)": "=IMOV_ITBI",
        "Escritura e registro (%)": "=IMOV_CARTORIO",
        "Custos de aquisição (R$)": f"=$B${P['Valor do imóvel']}*($B${P['ITBI (%)']}+$B${P['Escritura e registro (%)']})",
        "Desembolso total na compra": f"=$B${P['Valor do imóvel']}+$B${P['Custos de aquisição (R$)']}",
        "Capital disponível do cliente": "=IN_CAPITAL",
        "Sobra (+) ou falta (−) de caixa": f"=$B${P['Capital disponível do cliente']}-$B${P['Desembolso total na compra']}",
        "Aluguel mensal inicial": (
            '=IF(IMOV_MODO_ALUGUEL="Informar o valor do aluguel",IMOV_ALUGUEL,'
            f"$B${P['Valor do imóvel']}*IFERROR(INDEX(TAB_MACRO_VAL,"
            'MATCH("IMOB_YLD",TAB_MACRO_COD,0)),0)/12)'),
        "Vacância (% do ano)": "=IMOV_VACANCIA",
        "Reajuste anual do aluguel": "=IMOV_REAJUSTE",
        "Reajuste mensal do aluguel": f"=(1+$B${P['Reajuste anual do aluguel']})^(1/12)-1",
        "IPTU (% a.a. do valor)": "=IMOV_IPTU",
        "Manutenção e seguro (% a.a. do valor)": "=IMOV_MANUT",
        "Administração imobiliária (% do aluguel)": "=IMOV_ADM",
        "Valorização anual do imóvel": "=IMOV_VALORIZACAO",
        "Valorização mensal do imóvel": f"=(1+$B${P['Valorização anual do imóvel']})^(1/12)-1",
        "Corretagem na venda (%)": "=IMOV_CORRETAGEM",
        "Isenção de ganho de capital (1/0)": '=IF(IMOV_ISENCAO_GC="Sim",1,0)',
        "Destino do aluguel": "=IMOV_DESTINO",
        "Reinveste o aluguel (1/0)": '=IF(IMOV_DESTINO="Reinvestir",1,0)',
        "Rendimento do caixa a.a.": "=IMOV_TAXA_REINV",
        "Rendimento do caixa mensal": f"=(1+$B${P['Rendimento do caixa a.a.']})^(1/12)-1",
        "IPCA do cenário (a.a.)": "=IPCA_CENARIO",
        "IPCA mensal": f"=(1+$B${P['IPCA do cenário (a.a.)']})^(1/12)-1",
        "Custo de aquisição para ganho de capital": f"=$B${P['Desembolso total na compra']}",
    }
    fmt_par = {
        "Entra na comparação (1/0)": FMT_INT, "Isenção de ganho de capital (1/0)": FMT_INT,
        "Reinveste o aluguel (1/0)": FMT_INT, "Destino do aluguel": None,
    }
    for rotulo, lin in P.items():
        pct = "%" in rotulo or "anual" in rotulo or "mensal" in rotulo or "a.a." in rotulo
        escreve(ws, f"A{lin}", rotulo, tam=9, borda=BORDA_GRADE)
        escreve(ws, f"B{lin}", formulas[rotulo], tam=9, negrito=True,
                fmt=fmt_par.get(rotulo, FMT_PCT2 if pct else FMT_MOEDA_C),
                alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 13

    escreve(ws, f"D{P['Sobra (+) ou falta (−) de caixa']}",
            "Negativo = o cliente precisa de mais dinheiro do que tem para fechar a compra. "
            "A comparação só é justa quando esse valor é maior ou igual a zero.",
            tam=8, cor=VERMELHO, alinha=AL_ESQ_WRAP)
    escreve(ws, f"D{P['Aluguel mensal inicial']}",
            "Vem do valor informado na aba Imóvel ou do yield de aluguel da aba Premissas.",
            tam=8, cor=CINZA_SUAVE, alinha=AL_ESQ_WRAP)

    # ------------------------------ resumo ------------------------------
    _bloco_resumo(ws, "BLOCO 2 · RESULTADOS NO PRAZO ESCOLHIDO",
                  cab=MIM_RES_CAB, ini=MIM_RES_INI, col_ini=1)
    escreve(ws, f"B{MIM_RES_CAB}", "IMÓVEL PARA ALUGUEL", tam=9, negrito=True,
            cor=BRANCO, bg=AZUL_ESCURO, alinha=AL_CENTRO, borda=BORDA_GRADE)

    c = {n: get_column_letter(i) for n, i in MIM_C.items()}
    ini, fim = MIM_GRID_INI, MIM_GRID_FIM
    faixa = lambda n: f"${c[n]}${ini}:${c[n]}${fim}"                    # noqa: E731
    no_prazo = lambda n: f"INDEX({faixa(n)},IN_PRAZO+1)"                # noqa: E731
    soma = lambda n: f"SUMIF($A${ini}:$A${fim},\"<=\"&IN_PRAZO,{faixa(n)})"   # noqa: E731
    at = f"$B${P['Entra na comparação (1/0)']}"
    r_ = lambda rot: f"$B${MIM_R[rot]}"                                 # noqa: E731

    RES = {
        "Patrimônio bruto no prazo":
            f"=IF({at}=0,0,{no_prazo('Valor de mercado do imóvel')}+{no_prazo('Saldo do caixa')})",
        "Patrimônio líquido no prazo":
            f"=IF({at}=0,0,{no_prazo('Patrimônio líquido (se vender)')})",
        "Patrimônio líquido na metade do prazo":
            f"=IF({at}=0,0,INDEX({faixa('Patrimônio líquido (se vender)')},INT(IN_PRAZO/2)+1))",
        "Patrimônio líquido em R$ de hoje":
            f"=IF({at}=0,0,{no_prazo('Patrimônio em R$ de hoje')})",
        "Total investido (capital + aportes)":
            f"=IF({at}=0,0,{no_prazo('Total investido pelo cliente')})",
        "Ganho líquido":
            f"={r_('Patrimônio líquido no prazo')}-{r_('Total investido (capital + aportes)')}",
        "Imposto total pago":
            f"=IF({at}=0,0,{soma('IR sobre o aluguel')}+{no_prazo('IR sobre o caixa')}"
            f"+{no_prazo('IR sobre ganho de capital')})",
        "Custos totais pagos":
            f"=IF({at}=0,0,$B${P['Custos de aquisição (R$)']}+{soma('IPTU')}"
            f"+{soma('Administração imobiliária')}+{soma('Manutenção e seguro')}"
            f"+{soma('Perda por vacância')}+{no_prazo('Custo de venda')})",
        "Rentabilidade líquida acumulada":
            f"=IF({r_('Total investido (capital + aportes)')}=0,0,"
            f"{r_('Patrimônio líquido no prazo')}/{r_('Total investido (capital + aportes)')}-1)",
        "Taxa líquida equivalente a.a.":
            f"=IF(OR({at}=0,IN_PRAZO=0),0,IFERROR((1+RATE(IN_PRAZO,"
            f"-({r_('Total investido (capital + aportes)')}"
            f"-$B${P['Desembolso total na compra']})/IN_PRAZO,"
            f"-$B${P['Desembolso total na compra']},"
            f"{r_('Patrimônio líquido no prazo')}))^12-1,"
            f"(1+{r_('Rentabilidade líquida acumulada')})^(12/IN_PRAZO)-1))",
        "Ganho real a.a. (acima da inflação)":
            f"=IF({at}=0,0,(1+{r_('Taxa líquida equivalente a.a.')})/(1+IPCA_CENARIO)-1)",
        "Alíquota de IR no prazo escolhido":
            f"=IF({at}=0,0,IF($B${P['Isenção de ganho de capital (1/0)']}=1,0,ALIQ_GANHO_CAP))",
        "Renda mensal potencial (nominal)":
            f"=IF({at}=0,0,{no_prazo('Aluguel líquido')})",
        "Renda mensal potencial (poder de compra)":
            f"=IF({at}=0,0,{no_prazo('Aluguel líquido')}/{no_prazo('Fator inflação')})",
        "Pode retirar a partir de": '=IF(' + at + '=0,"","Depende de vender o imóvel")',
        "Atende à aplicação mínima (1/0)":
            f"=IF({at}=0,0,IF(IN_CAPITAL>=$B${P['Desembolso total na compra']},1,0))",
        "Cabe no perfil declarado (1/0)":
            f"=IF({at}=0,0,IF(3<=IFERROR(INDEX("
            f"{AB_PREMISSAS}!$B${PRE_PERFIL_INI}:$B${PRE_PERFIL_FIM},"
            f"MATCH(IN_PERFIL,{AB_PREMISSAS}!$A${PRE_PERFIL_INI}:$A${PRE_PERFIL_FIM},0)),5),1,0))",
        "Para retirar (linguagem de cliente)":
            f'=IF({at}=0,"","Depende de encontrar comprador — normalmente meses")',
        "Oscilação (linguagem de cliente)":
            f'=IF({at}=0,"",IFERROR(INDEX({AB_PREMISSAS}!$B${PRE_RISCO_INI}:$B${PRE_RISCO_FIM},3),""))',
    }
    for rotulo, formula in RES.items():
        escreve(ws, f"B{MIM_R[rotulo]}", formula, tam=8.5, fmt=_fmt_resumo(rotulo),
                alinha=AL_CENTRO, borda=BORDA_GRADE,
                negrito=rotulo == "Patrimônio líquido no prazo",
                bg=AZUL_CLARO if rotulo == "Patrimônio líquido no prazo" else None)
    for rotulo in ("Pode retirar a partir de",):
        ws[f"B{MIM_R[rotulo]}"].number_format = FMT_TEXTO

    # ------------------------------ grade mensal ------------------------------
    secao(ws, MIM_GRID_CAB - 2, "BLOCO 3 · PROJEÇÃO MÊS A MÊS DO IMÓVEL", ate_col="H")
    for j, (nome, larg) in enumerate(MIM_COLS):
        col = get_column_letter(j + 1)
        escreve(ws, f"{col}{MIM_GRID_CAB}", nome, tam=7.5, negrito=True, cor=BRANCO,
                bg=AZUL_MEDIO, alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        ws.column_dimensions[col].width = larg
    ws.row_dimensions[MIM_GRID_CAB].height = 42

    def pr(rot):
        return f"$B${P[rot]}"

    for r in range(ini, fim + 1):
        p_ = r - 1
        primeiro = (r == ini)
        escreve(ws, f"A{r}", r - ini, tam=8, fmt=FMT_INT, alinha=AL_CENTRO)
        escreve(ws, f"B{r}", f"=EDATE(DATA_INICIO,$A{r})", tam=8, fmt=FMT_DATA, alinha=AL_CENTRO)
        escreve(ws, f"C{r}", f"=$A{r}*30", tam=8, fmt=FMT_INT, alinha=AL_CENTRO)
        escreve(ws, f"D{r}", f"=(1+{pr('IPCA mensal')})^$A{r}", tam=8, fmt="0.0000",
                alinha=AL_CENTRO)

        F = {
            "Valor de mercado do imóvel":
                f"={pr('Valor do imóvel')}*(1+{pr('Valorização mensal do imóvel')})^$A{r}",
            "Aluguel contratado":
                f"=IF($A{r}=0,0,{pr('Aluguel mensal inicial')}"
                f"*(1+{pr('Reajuste mensal do aluguel')})^($A{r}-1))",
            "Perda por vacância": f"={c['Aluguel contratado']}{r}*{pr('Vacância (% do ano)')}",
            "Aluguel recebido":
                f"={c['Aluguel contratado']}{r}-{c['Perda por vacância']}{r}",
            "IPTU":
                f"=IF($A{r}=0,0,{c['Valor de mercado do imóvel']}{r}"
                f"*{pr('IPTU (% a.a. do valor)')}/12)",
            "Administração imobiliária":
                f"={c['Aluguel recebido']}{r}*{pr('Administração imobiliária (% do aluguel)')}",
            "Manutenção e seguro":
                f"=IF($A{r}=0,0,{c['Valor de mercado do imóvel']}{r}"
                f"*{pr('Manutenção e seguro (% a.a. do valor)')}/12)",
            "Base do carnê-leão":
                f"=MAX(0,{c['Aluguel recebido']}{r}-{c['IPTU']}{r}"
                f"-{c['Administração imobiliária']}{r})",
            "IR sobre o aluguel":
                f"=MAX(0,{c['Base do carnê-leão']}{r}"
                f"*IFERROR(INDEX(TAB_IRPF_ALIQ,MATCH({c['Base do carnê-leão']}{r},TAB_IRPF_BASE,1)),0)"
                f"-IFERROR(INDEX(TAB_IRPF_DED,MATCH({c['Base do carnê-leão']}{r},TAB_IRPF_BASE,1)),0))",
            "Aluguel líquido":
                f"={c['Aluguel recebido']}{r}-{c['IPTU']}{r}-{c['Administração imobiliária']}{r}"
                f"-{c['Manutenção e seguro']}{r}-{c['IR sobre o aluguel']}{r}",
            "Aporte do cliente":
                f"=IF(OR($A{r}=0,$A{r}>IN_PRAZO,{pr('Entra na comparação (1/0)')}=0),0,"
                f"IF(APORTE_CORRIGIDO=\"Sim\",IN_APORTE*$D{r},IN_APORTE))",
            "Aluguel reinvestido":
                f"=IF({pr('Reinveste o aluguel (1/0)')}=1,MAX(0,{c['Aluguel líquido']}{r}),0)",
            "Rendimento do caixa":
                ("=0" if primeiro else
                 f"={c['Saldo do caixa']}{p_}*{pr('Rendimento do caixa mensal')}"),
            "Saldo do caixa":
                (f"=MAX(0,{pr('Sobra (+) ou falta (−) de caixa')})" if primeiro else
                 f"={c['Saldo do caixa']}{p_}+{c['Rendimento do caixa']}{r}"
                 f"+{c['Aporte do cliente']}{r}+{c['Aluguel reinvestido']}{r}"),
            "Total aportado no caixa":
                (f"=MAX(0,{pr('Sobra (+) ou falta (−) de caixa')})" if primeiro else
                 f"={c['Total aportado no caixa']}{p_}+{c['Aporte do cliente']}{r}"
                 f"+{c['Aluguel reinvestido']}{r}"),
            "IR sobre o caixa":
                f"=MAX(0,IFERROR(INDEX(TAB_IR,MATCH($C{r},TAB_IR_DIAS,1),"
                f'MATCH("RF_REGR",TAB_IR_REGIMES,0)),0)'
                f"*MAX(0,{c['Saldo do caixa']}{r}-{c['Total aportado no caixa']}{r}))",
            "Custo de venda":
                f"={c['Valor de mercado do imóvel']}{r}*{pr('Corretagem na venda (%)')}",
            "IR sobre ganho de capital":
                f"=IF({pr('Isenção de ganho de capital (1/0)')}=1,0,"
                f"MAX(0,ALIQ_GANHO_CAP*MAX(0,{c['Valor de mercado do imóvel']}{r}"
                f"-{c['Custo de venda']}{r}"
                f"-{pr('Custo de aquisição para ganho de capital')})))",
            "Patrimônio líquido (se vender)":
                f"=IF({pr('Entra na comparação (1/0)')}=0,0,"
                f"{c['Valor de mercado do imóvel']}{r}-{c['Custo de venda']}{r}"
                f"-{c['IR sobre ganho de capital']}{r}+{c['Saldo do caixa']}{r}"
                f"-{c['IR sobre o caixa']}{r})",
            "Patrimônio em R$ de hoje":
                f"={c['Patrimônio líquido (se vender)']}{r}/$D{r}",
            "Renda mensal disponível":
                f"=IF({pr('Reinveste o aluguel (1/0)')}=1,0,MAX(0,{c['Aluguel líquido']}{r}))",
            "Total investido pelo cliente":
                (f"={pr('Desembolso total na compra')}"
                 f"+MAX(0,{pr('Sobra (+) ou falta (−) de caixa')})" if primeiro else
                 f"={c['Total investido pelo cliente']}{p_}+{c['Aporte do cliente']}{r}"),
        }
        for nome, formula in F.items():
            escreve(ws, f"{c[nome]}{r}", formula, tam=8, fmt=FMT_MOEDA_C, alinha=AL_DIR,
                    negrito=nome in ("Patrimônio líquido (se vender)",))
        ws.row_dimensions[r].height = 12

    ws.freeze_panes = f"E{MIM_GRID_INI}"
    ws.sheet_properties.tabColor = CINZA_SUAVE
    link_aba(ws, "J4", AB_IMOVEL, "◀ ABA IMÓVEL")


# ==========================================================================
# ABA ADEQUAÇÃO
# ==========================================================================
_ADE_COLS = [
    ("ID", 7), ("Produto", 36), ("Categoria", 13), ("Risco", 7),
    ("Carência (dias)", 9), ("Liquidez (dias)", 9), ("Aplicação mínima", 13),
    ("Regime", 12), ("Taxa adm.", 9), ("Ativo", 7),
    ("Passa no valor mínimo", 9), ("Passa no perfil", 9),
    ("Nota de prazo", 9), ("Nota de liquidez", 9), ("Nota de prioridade", 9),
    ("Nota de custo e imposto", 9), ("ADERÊNCIA (0-100)", 12),
    ("Chave de ordenação", 11), ("Classificação", 24),
    ("Por que pode fazer sentido", 52), ("Ponto de atenção", 46),
    ("Retorno bruto a.a. estimado", 12), ("Indexador", 10), ("Volatilidade", 10),
]


def construir_adequacao(wb):
    ws = wb[AB_ADEQUACAO]
    esconde_grade(ws)
    titulo_pagina(ws, "ADERÊNCIA AO OBJETIVO DO CLIENTE",
                  "Camada de cálculo — mede ENCAIXE, não rentabilidade", ate_col="V")

    secao(ws, 4, "O QUE ESTA ABA FAZ (E O QUE ELA NÃO FAZ)", ate_col="V")
    nota(ws, 5,
         "Esta aba NÃO responde 'qual investimento rende mais'. Ela responde 'quais alternativas conversam com o "
         "objetivo, o prazo, a necessidade de liquidez, o perfil e a prioridade DESTE cliente'. O retorno estimado "
         "aparece só na última coluna, como informação — ele não entra na nota. Dois produtos com a mesma nota podem "
         "render muito diferente, e isso é proposital: a escolha final é do cliente com o consultor.",
         ate_col="V", altura=34)

    ws.merge_cells("A6:A7")
    escreve(ws, "A6", "Pesos em uso\n(vêm da prioridade escolhida)", tam=8, negrito=True,
            cor=AZUL_ESCURO, alinha=AL_CENTRO_WRAP, bg=AZUL_CLARO, borda=BORDA_GRADE)
    for col, rot, off in (("B", "Prazo", 1), ("C", "Liquidez", 2),
                          ("D", "Prioridade", 3), ("E", "Custo/imposto", 4)):
        escreve(ws, f"{col}6", rot, tam=8, negrito=True, cor=AZUL_ESCURO,
                bg=AZUL_CLARO, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"{col}{ADE_PESOS_USO}",
                f"=IFERROR(INDEX(${get_column_letter(1+off)}${ADE_PESOS_INI}:"
                f"${get_column_letter(1+off)}${ADE_PESOS_FIM},"
                f"MATCH(IN_PRIORIDADE,$A${ADE_PESOS_INI}:$A${ADE_PESOS_FIM},0)),25)",
                tam=9, negrito=True, fmt=FMT_INT, alinha=AL_CENTRO, borda=BORDA_GRADE)

    cabecalho_tabela(ws, ADE_CAB, 1, [c[0] for c in _ADE_COLS],
                     larguras=[c[1] for c in _ADE_COLS], altura=42)

    pr = f"{AB_PRODUTOS}!"
    for r in range(ADE_INI, ADE_FIM + 1):
        vazio = f'{pr}$B{r}=""'
        F = {
            "A": f'=IF({vazio},"",{pr}$A{r})',
            "B": f'=IF({vazio},"",{pr}$B{r})',
            "C": f'=IF({vazio},"",{pr}$C{r})',
            "D": f"=IF({vazio},0,{pr}${_pcol('risco')}{r})",
            "E": f"=IF({vazio},0,{pr}${_pcol('carencia')}{r})",
            "F": f"=IF({vazio},0,{pr}${_pcol('liquidez')}{r})",
            "G": f"=IF({vazio},0,{pr}${_pcol('aplic_min')}{r})",
            "H": f'=IF({vazio},"",{pr}${_pcol("regime")}{r})',
            "I": f"=IF({vazio},0,{pr}${_pcol('taxa_adm')}{r})",
            "J": f'=IF({vazio},"NÃO",{pr}${_pcol("ativo")}{r})',
            "K": f'=IF(AND($B{r}<>"",IN_CAPITAL>=$G{r}),1,0)',
            "L": (f'=IF(AND($B{r}<>"",$D{r}<=IFERROR(INDEX('
                  f"{AB_PREMISSAS}!$B${PRE_PERFIL_INI}:$B${PRE_PERFIL_FIM},"
                  f"MATCH(IN_PERFIL,{AB_PREMISSAS}!$A${PRE_PERFIL_INI}:$A${PRE_PERFIL_FIM},0)),5)),1,0)"),
            # Nota de prazo: carência barra tudo; renda variável precisa de horizonte
            "M": (f"=IF(IN_PRAZO*30<$E{r},0,"
                  f"IF($D{r}>=4,IF(IN_PRAZO>=60,100,IF(IN_PRAZO>=36,60,IF(IN_PRAZO>=24,30,0))),"
                  f"IF($D{r}=3,IF(IN_PRAZO>=24,100,IF(IN_PRAZO>=12,70,40)),100)))"),
            # Nota de liquidez: depende da resposta sobre precisar do dinheiro antes
            # O que importa é o tempo TOTAL até o dinheiro estar na conta:
            # carência (não pode sacar) + liquidação (leva dias para cair).
            "N": (f'=IF(IN_RESGATE="Sim",'
                  f"IF($E{r}+$F{r}<=3,100,IF($E{r}+$F{r}<=31,50,0)),"
                  f'IF(IN_RESGATE="Talvez",'
                  f"IF($E{r}+$F{r}<=90,100,IF($E{r}+$F{r}<=360,50,20)),100))"),
            # Nota de prioridade: matriz prioridade × risco
            "O": (f"=IF($D{r}=0,0,IFERROR(INDEX($B${ADE_MATRIZ_INI}:$F${ADE_MATRIZ_FIM},"
                  f"MATCH(IN_PRIORIDADE,$A${ADE_MATRIZ_INI}:$A${ADE_MATRIZ_FIM},0),$D{r}),0))"),
            # Nota de custo e eficiência tributária
            "P": (f'=MAX(0,MIN(100,60+IF($H{r}="ISENTO",25,0)'
                  f"+IF($I{r}<=0.005,15,IF($I{r}>=0.015,-15,0))"
                  f'+IF(AND($H{r}="PREV_REGR",IN_PRAZO>=120),20,0)'
                  f'+IF(AND($H{r}="FUNDO_LP",IN_PRAZO<=12),-10,0)'
                  f'+IF(AND($H{r}="FUNDO_CP",IN_PRAZO>=24),-15,0)))'),
            "Q": (f'=IF(OR($B{r}="",$J{r}<>"SIM",$K{r}=0,$L{r}=0),0,'
                  f"ROUND(($M{r}*$B${ADE_PESOS_USO}+$N{r}*$C${ADE_PESOS_USO}"
                  f"+$O{r}*$D${ADE_PESOS_USO}+$P{r}*$E${ADE_PESOS_USO})"
                  f"/MAX(1,$B${ADE_PESOS_USO}+$C${ADE_PESOS_USO}"
                  f"+$D${ADE_PESOS_USO}+$E${ADE_PESOS_USO}),1))"),
            # O imóvel entra na comparação por fora (motor próprio), então
            # não pode ocupar um dos seis lugares — se ocupasse, o lugar
            # ficaria silenciosamente vazio. Fica de fora só da ORDENAÇÃO:
            # a nota e o texto de aderência dele continuam disponíveis.
            "R": f'=IF($H{r}="IMOVEL",0,$Q{r}+ROW()/1000000)',
            "S": (f'=IF($B{r}="","",IF($Q{r}=0,"Não indicado agora",'
                  f'IF($Q{r}>=75,"Pode fazer sentido",'
                  f'IF($Q{r}>=50,"Talvez faça sentido","Provavelmente não é o mais indicado"))))'),
            "T": (f'=IF($B{r}="","",IF($Q{r}=0,'
                  f'IF($K{r}=0,"O valor disponível é menor que a aplicação mínima deste produto.",'
                  f'IF($L{r}=0,"O risco deste produto está acima do perfil declarado pelo cliente.",'
                  f'"Produto não está ativo na base.")),'
                  f'IF($Q{r}<50,"Encaixa pouco no que foi pedido — veja o ponto de atenção ao lado.",'
                  f'IF($H{r}="ISENTO","Não paga Imposto de Renda para pessoa física.",'
                  f'IF($W{r}="PRE","A taxa fica travada na contratação: não cai se os juros da economia caírem.",'
                  f'IF($W{r}="IPCA","Protege o poder de compra: rende a inflação mais uma taxa fixa por cima.",'
                  f'IF(AND($E{r}=0,$F{r}<=1),"O dinheiro pode ser retirado praticamente a qualquer momento.",'
                  f'IF(AND($H{r}="PREV_REGR",IN_PRAZO>=120),'
                  f'"No prazo escolhido a previdência alcança a menor alíquota de imposto (10%).",'
                  f'IF($D{r}>=4,"Pode render mais no prazo longo, aceitando oscilação pelo caminho.",'
                  f'"Combina com o prazo, a liquidez e a prioridade informados."))))))))'),
            # Ordem proposital: primeiro o que IMPEDE o resgate, depois o que
            # faz o valor oscilar, e só então detalhe de custo. Cada família de
            # produto tem um alerta próprio — título tem vencimento, fundo não,
            # e previdência responde pela seguradora, não pelo FGC.
            "U": (f'=IF($B{r}="","",'
                  f'IF($E{r}>0,"Carência de "&$E{r}&" dias: não dá para resgatar antes.",'
                  f'IF($F{r}>60,"Não é dinheiro rápido: leva meses para virar caixa.",'
                  f'IF(LEFT($H{r},4)="PREV",'
                  f'IF(IN_PRAZO<24,"Resgate antes de 2 anos paga 35% de imposto.",'
                  f'"Não tem cobertura do FGC: quem responde pelo dinheiro é a seguradora."),'
                  f'IF($D{r}>=4,"Pode cair no caminho e demorar a se recuperar.",'
                  f'IF(AND($H{r}="RF_REGR",$X{r}>=0.03),'
                  f'"Se vender antes do vencimento, o preço pode estar abaixo do que você pagou.",'
                  f'IF($X{r}>=0.03,'
                  f'"O valor oscila mês a mês: em prazo curto pode estar abaixo do que você aplicou.",'
                  f'IF($H{r}="FUNDO_LP","Tem come-cotas em maio e novembro, que antecipam parte do imposto.",'
                  f'IF($F{r}>7,"Para o dinheiro cair na conta leva cerca de "&$F{r}&" dias.",'
                  f'IF($I{r}>=0.015,"Taxa de administração alta em relação ao retorno esperado.",'
                  f'"Confirme prazo, liquidez e tributação antes de contratar."))))))))))'),
            "V": (f'=IF($B{r}="","",IFERROR(IF({pr}${_pcol("composicao")}{r}="MULT",'
                  f"(1+INDEX(TAB_MACRO_VAL,MATCH({pr}${_pcol('benchmark')}{r},TAB_MACRO_COD,0))"
                  f"*{pr}${_pcol('pct_bench')}{r})*(1+{pr}${_pcol('spread')}{r})-1,"
                  f"INDEX(TAB_MACRO_VAL,MATCH({pr}${_pcol('benchmark')}{r},TAB_MACRO_COD,0))"
                  f"*{pr}${_pcol('pct_bench')}{r}+{pr}${_pcol('spread')}{r}),\"\"))"),
            "W": f'=IF({vazio},"",{pr}${_pcol("benchmark")}{r})',
            "X": f"=IF({vazio},0,{pr}${_pcol('volatilidade')}{r})",
        }
        fmt_ade = {"D": FMT_INT, "E": FMT_INT, "F": FMT_INT, "G": FMT_MOEDA,
                   "I": FMT_PCT2, "K": FMT_INT, "L": FMT_INT, "M": FMT_INT,
                   "N": FMT_INT, "O": FMT_INT, "P": FMT_INT, "Q": '0.0',
                   "R": '0.000000', "V": FMT_PCT2, "X": FMT_PCT2}
        for col, formula in F.items():
            escreve(ws, f"{col}{r}", formula, tam=8,
                    cor=COR_LINK if col in ("A","B","C","D","E","F","G","H","I","J","W","X")
                    else COR_FORMULA,
                    fmt=fmt_ade.get(col),
                    alinha=AL_ESQ_WRAP if col in ("T", "U") else
                    (AL_ESQ if col in ("B", "S") else AL_CENTRO),
                    borda=BORDA_GRADE, negrito=col == "Q")
        ws.row_dimensions[r].height = 22

    from openpyxl.formatting.rule import ColorScaleRule
    ws.conditional_formatting.add(
        f"Q{ADE_INI}:Q{ADE_FIM}",
        ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                       mid_type="num", mid_value=50, mid_color=AMBAR_CLARO,
                       end_type="num", end_value=100, end_color="BFE3C8"))

    # ---------------- ordem de aderência ----------------
    secao(ws, ADE_TOP_CAB - 1, "ORDEM DE ADERÊNCIA — o que a planilha sugere colocar na comparação",
          ate_col="V")
    cabecalho_tabela(ws, ADE_TOP_CAB, 1,
                     ["Posição", "Produto sugerido", "Aderência", "Classificação",
                      "Por que", "Ponto de atenção"],
                     larguras=[9, 36, 11, 24, 52, 46], altura=24)
    for i in range(N_SLOTS):
        r = ADE_TOP_INI + i
        chave = f"LARGE($R${ADE_INI}:$R${ADE_FIM},{i+1})"
        pos = f"MATCH({chave},$R${ADE_INI}:$R${ADE_FIM},0)"
        escreve(ws, f"A{r}", i + 1, tam=9, negrito=True, cor=AZUL_ESCURO,
                alinha=AL_CENTRO, borda=BORDA_GRADE)
        for col, origem, fmt in (("B", "B", None), ("C", "Q", '0.0'),
                                 ("D", "S", None), ("E", "T", None), ("F", "U", None)):
            escreve(ws, f"{col}{r}",
                    f'=IFERROR(IF({chave}<1,"",INDEX(${origem}${ADE_INI}:${origem}${ADE_FIM},{pos})),"")',
                    tam=8.5, fmt=fmt, borda=BORDA_GRADE,
                    alinha=AL_ESQ_WRAP if col in ("E", "F") else
                    (AL_CENTRO if col == "C" else AL_ESQ),
                    negrito=col == "B")
        ws.row_dimensions[r].height = 24

    # ---------------- tabelas de parâmetro da aderência ----------------
    secao(ws, ADE_PESOS_CAB - 1,
          "PESOS POR PRIORIDADE DO CLIENTE (edite aqui para calibrar a sugestão)", ate_col="V")
    cabecalho_tabela(ws, ADE_PESOS_CAB, 1,
                     ["Prioridade declarada pelo cliente", "Peso do prazo",
                      "Peso da liquidez", "Peso da prioridade", "Peso do custo/imposto"],
                     larguras=[46, 13, 13, 13, 16], altura=24)
    pesos = {
        "Segurança acima de tudo": (20, 20, 50, 10),
        "Equilíbrio entre segurança e rentabilidade": (25, 25, 35, 15),
        "Rentabilidade, aceitando oscilação": (30, 15, 40, 15),
        "Poder retirar a qualquer momento": (15, 55, 20, 10),
    }
    for i, prioridade in enumerate(D.PRIORIDADES):
        r = ADE_PESOS_INI + i
        escreve(ws, f"A{r}", prioridade, tam=9, borda=BORDA_GRADE)
        for j, v in enumerate(pesos[prioridade]):
            escreve(ws, f"{get_column_letter(2 + j)}{r}", v, tam=9, cor=COR_INPUT,
                    bg=FILL_INPUT, fmt=FMT_INT, alinha=AL_CENTRO, borda=BORDA_GRADE)

    secao(ws, ADE_MATRIZ_CAB - 1,
          "NOTA DE PRIORIDADE POR NÍVEL DE RISCO (0 a 100)", ate_col="V")
    cabecalho_tabela(ws, ADE_MATRIZ_CAB, 1,
                     ["Prioridade declarada pelo cliente", "Risco 1", "Risco 2",
                      "Risco 3", "Risco 4", "Risco 5"],
                     larguras=[46, 11, 11, 11, 11, 11], altura=24)
    matriz = {
        "Segurança acima de tudo": (100, 70, 30, 5, 0),
        "Equilíbrio entre segurança e rentabilidade": (60, 100, 90, 45, 15),
        "Rentabilidade, aceitando oscilação": (30, 50, 80, 100, 95),
        "Poder retirar a qualquer momento": (100, 85, 50, 20, 5),
    }
    for i, prioridade in enumerate(D.PRIORIDADES):
        r = ADE_MATRIZ_INI + i
        escreve(ws, f"A{r}", prioridade, tam=9, borda=BORDA_GRADE)
        for j, v in enumerate(matriz[prioridade]):
            escreve(ws, f"{get_column_letter(2 + j)}{r}", v, tam=9, cor=COR_INPUT,
                    bg=FILL_INPUT, fmt=FMT_INT, alinha=AL_CENTRO, borda=BORDA_GRADE)

    ws.freeze_panes = f"C{ADE_INI}"
    ws.sheet_properties.tabColor = CINZA_SUAVE
    link_aba(ws, "X4", AB_INICIO, "◀ INÍCIO")
