"""
MAPA DE REFERÊNCIAS — contrato único entre as camadas.

Todas as abas conversam por NOMES DEFINIDOS (named ranges), nunca por
coordenadas soltas espalhadas nas fórmulas. Se uma célula de entrada precisar
mudar de lugar, muda-se o endereço aqui e o nome continua valendo em toda a
planilha — nenhuma fórmula quebra.
"""

# --------------------------------------------------------------------------
# ABAS
# --------------------------------------------------------------------------
AB_INICIO = "Inicio"
AB_CLIENTE = "Cliente"
AB_COMPARAR = "Comparar"
AB_CONSULTOR = "Consultor"
AB_MESAMES = "MesAMes"
AB_IMOVEL = "Imovel"
AB_PREV = "Previdencia"
AB_RELATORIO = "Relatorio"
AB_ADEQUACAO = "Adequacao"
AB_MOTOR = "Motor"
AB_MOTOR_IMOVEL = "MotorImovel"
AB_PRODUTOS = "Produtos"
AB_PREMISSAS = "Premissas"
AB_FONTES = "Fontes"
AB_GLOSSARIO = "Glossario"

ORDEM_ABAS = [
    AB_INICIO, AB_CLIENTE, AB_COMPARAR, AB_CONSULTOR, AB_MESAMES,
    AB_IMOVEL, AB_PREV, AB_RELATORIO, AB_ADEQUACAO, AB_MOTOR,
    AB_MOTOR_IMOVEL, AB_PRODUTOS, AB_PREMISSAS, AB_FONTES, AB_GLOSSARIO,
]

# --------------------------------------------------------------------------
# HORIZONTE DO MOTOR
# --------------------------------------------------------------------------
MESES_MAX = 240              # projeção mês a mês de 0 a 240 (20 anos)
N_SLOTS = 6                  # alternativas comparadas simultaneamente
SLOT_LETRAS = ["A", "B", "C", "D", "E", "F"]

# --------------------------------------------------------------------------
# ABA PRODUTOS — geometria da base
# --------------------------------------------------------------------------
PROD_LIN_CAB = 8             # linha do cabeçalho
PROD_LIN_INI = 9             # primeira linha de dados
PROD_LIN_FIM = 78            # última linha reservada (70 produtos)
# Índices de coluna (1 = A)
PROD_COL = {
    "id": 1, "nome": 2, "categoria": 3, "emissor": 4, "benchmark": 5,
    "pct_bench": 6, "spread": 7, "composicao": 8, "taxa_adm": 9,
    "taxa_perf": 10, "carreg_ent": 11, "carreg_sai": 12, "custodia": 13,
    "regime": 14, "base_trib": 15, "carencia": 16, "liquidez": 17,
    "aplic_min": 18, "aporte_min": 19, "risco": 20, "volatilidade": 21,
    "garantia": 22, "rent12": 23, "rent36": 24, "atualizado": 25,
    "fonte": 26, "tipo_dado": 27, "status": 28, "obs": 29, "ativo": 30,
}
PROD_FAIXA_NOMES = f"{AB_PRODUTOS}!$B${PROD_LIN_INI}:$B${PROD_LIN_FIM}"

# --------------------------------------------------------------------------
# ABA PREMISSAS — geometria dos blocos
# --------------------------------------------------------------------------
PRE_MACRO_CAB = 8
PRE_MACRO_INI = 9                     # 10 indicadores -> 9..18
PRE_MACRO_FIM = 18
PRE_COL_CONS, PRE_COL_BASE, PRE_COL_OTI = "C", "D", "E"
PRE_COL_RESOLVIDO = "F"               # valor do cenário selecionado
PRE_COL_COMP = "G"                    # SOMA / MULT

PRE_IR_CAB = 22                       # cabeçalho da matriz de IR
PRE_IR_INI = 23
PRE_IR_FIM = 30                       # 8 faixas de dias
PRE_IR_COL_INI, PRE_IR_COL_FIM = "B", "H"

PRE_CC_CAB = 33                       # come-cotas
PRE_CC_INI = 34
PRE_CC_FIM = 40

PRE_IOF_CAB = 43                      # tabela de IOF (30 dias)
PRE_IOF_INI = 44
PRE_IOF_FIM = 73

PRE_IRPF_CAB = 76                     # tabela progressiva mensal
PRE_IRPF_INI = 77
PRE_IRPF_FIM = 81

PRE_HOR_CAB = 84                      # horizontes -> meses
PRE_HOR_INI = 85
PRE_HOR_FIM = 90

PRE_RISCO_CAB = 93                    # escala de risco em linguagem simples
PRE_RISCO_INI = 94
PRE_RISCO_FIM = 98

PRE_PERFIL_CAB = 101                  # perfil -> teto de risco
PRE_PERFIL_INI = 102
PRE_PERFIL_FIM = 104

PRE_OUTROS_INI = 107                  # parâmetros avulsos (FGC, PGBL, imóvel)

# --------------------------------------------------------------------------
# ABA MOTOR — geometria
# --------------------------------------------------------------------------
MOT_PAR_CAB = 5                       # cabeçalho do bloco de parâmetros
MOT_PAR_INI = 6                       # primeira linha de parâmetro
MOT_COL_SLOT0 = 2                     # slot A na coluna B do bloco de parâmetros

# Linhas do bloco de parâmetros (rótulo -> linha)
MOT_P = {}
_labels_motor = [
    "Produto selecionado", "Linha na base de produtos", "Regime tributário",
    "Alternativa em uso (1/0)", "Categoria", "Emissor / Gestor", "Benchmark",
    "% do benchmark", "Spread a.a.", "Composição",
    "Retorno a.a. do benchmark puro", "Retorno BRUTO a.a. (cenário)",
    "Taxa mensal do benchmark", "Taxa mensal bruta",
    "Taxa de administração a.a.", "Custódia a.a.",
    "Custos mensais (adm + custódia)", "Taxa de performance",
    "Carregamento de entrada", "Carregamento de saída",
    "Base tributável (1=rend. / 2=total)", "Tem come-cotas (1/0)",
    "Alíquota do come-cotas", "Carência (dias)", "Liquidez (dias)",
    "Aplicação mínima", "Risco (1-5)", "Volatilidade a.a.", "Garantia",
    "É PGBL (aporte dedutível)", "Retorno LÍQUIDO a.a. estimado",
]
for _i, _l in enumerate(_labels_motor):
    MOT_P[_l] = MOT_PAR_INI + _i
MOT_PAR_FIM = MOT_PAR_INI + len(_labels_motor) - 1     # 36

# Bloco de resumo: os números que as abas de interface leem
MOT_RES_CAB = MOT_PAR_FIM + 2                          # 38
MOT_RES_INI = MOT_RES_CAB + 1                          # 39
MOT_RES_ROTULOS = [
    "Patrimônio bruto no prazo",
    "Patrimônio líquido no prazo",
    "Patrimônio líquido na metade do prazo",
    "Patrimônio líquido em R$ de hoje",
    "Total investido (capital + aportes)",
    "Ganho líquido",
    "Imposto total pago",
    "Custos totais pagos",
    "Rentabilidade líquida acumulada",
    "Taxa líquida equivalente a.a.",
    "Ganho real a.a. (acima da inflação)",
    "Alíquota de IR no prazo escolhido",
    "Renda mensal potencial (nominal)",
    "Renda mensal potencial (poder de compra)",
    "Pode retirar a partir de",
    "Atende à aplicação mínima (1/0)",
    "Cabe no perfil declarado (1/0)",
    "Para retirar (linguagem de cliente)",
    "Oscilação (linguagem de cliente)",
]
MOT_R = {r: MOT_RES_INI + i for i, r in enumerate(MOT_RES_ROTULOS)}
MOT_RES_FIM = MOT_RES_INI + len(MOT_RES_ROTULOS) - 1   # 56

MOT_GRID_BAND = MOT_RES_FIM + 2                        # 58
MOT_GRID_CAB = MOT_GRID_BAND + 1                       # 59
MOT_GRID_INI = MOT_GRID_CAB + 1                        # 60 (mês 0)
MOT_GRID_FIM = MOT_GRID_INI + MESES_MAX                # 300 (mês 240)
MOT_SLOT_COL0 = 6                     # coluna F = primeira coluna do slot A
MOT_SLOT_LARGURA = 14                 # colunas por slot
MOT_SLOT_PASSO = 15                   # 14 colunas + 1 de respiro

# Colunas da grade mensal, dentro de cada slot (deslocamento a partir de 0)
MOT_G = {
    "saldo_ini": 0, "aporte": 1, "carreg_ent": 2, "rend_bruto": 3,
    "taxa_adm": 4, "taxa_perf": 5, "come_cotas": 6, "saldo_fim": 7,
    "aportado": 8, "cc_acum": 9, "ganho_trib": 10, "ir_resgate": 11,
    "liquido": 12, "liquido_real": 13,
}
MOT_G_TITULOS = [
    "Saldo inicial", "Aporte do mês", "Custo de entrada", "Rendimento bruto",
    "Taxa de administração", "Taxa de performance", "Come-cotas (IR)",
    "Saldo final", "Total aportado (base fiscal)", "Come-cotas acumulado",
    "Ganho tributável", "IR no resgate", "Valor líquido se resgatar",
    "Valor líquido em R$ de hoje",
]

# --------------------------------------------------------------------------
# ABA MOTOR IMÓVEL — geometria
# --------------------------------------------------------------------------
MIM_PAR_INI = 5
MIM_PAR_ROTULOS = [
    "Entra na comparação (1/0)", "Valor do imóvel", "ITBI (%)",
    "Escritura e registro (%)", "Custos de aquisição (R$)",
    "Desembolso total na compra", "Capital disponível do cliente",
    "Sobra (+) ou falta (−) de caixa", "Aluguel mensal inicial",
    "Vacância (% do ano)", "Reajuste anual do aluguel",
    "Reajuste mensal do aluguel", "IPTU (% a.a. do valor)",
    "Manutenção e seguro (% a.a. do valor)", "Administração imobiliária (% do aluguel)",
    "Valorização anual do imóvel", "Valorização mensal do imóvel",
    "Corretagem na venda (%)", "Isenção de ganho de capital (1/0)",
    "Destino do aluguel", "Reinveste o aluguel (1/0)",
    "Rendimento do caixa a.a.", "Rendimento do caixa mensal",
    "IPCA do cenário (a.a.)", "IPCA mensal",
    "Custo de aquisição para ganho de capital",
]
MIM_P = {r: MIM_PAR_INI + i for i, r in enumerate(MIM_PAR_ROTULOS)}
MIM_PAR_FIM = MIM_PAR_INI + len(MIM_PAR_ROTULOS) - 1   # 30

MIM_RES_CAB = MIM_PAR_FIM + 2                          # 32
MIM_RES_INI = MIM_RES_CAB + 1                          # 33
MIM_R = {r: MIM_RES_INI + i for i, r in enumerate(MOT_RES_ROTULOS)}
MIM_RES_FIM = MIM_RES_INI + len(MOT_RES_ROTULOS) - 1   # 50

MIM_GRID_CAB = MIM_RES_FIM + 3                         # 53
MIM_GRID_INI = MIM_GRID_CAB + 1                        # 54
MIM_GRID_FIM = MIM_GRID_INI + MESES_MAX                # 294
MIM_COLS = [
    ("Mês", 7), ("Data", 11), ("Dias", 8), ("Fator inflação", 11),
    ("Valor de mercado do imóvel", 16), ("Aluguel contratado", 13),
    ("Perda por vacância", 12), ("Aluguel recebido", 13), ("IPTU", 10),
    ("Administração imobiliária", 13), ("Manutenção e seguro", 13),
    ("Base do carnê-leão", 12), ("IR sobre o aluguel", 12),
    ("Aluguel líquido", 12), ("Aporte do cliente", 12),
    ("Aluguel reinvestido", 12), ("Rendimento do caixa", 12),
    ("Saldo do caixa", 14), ("Total aportado no caixa", 13),
    ("IR sobre o caixa", 12), ("Custo de venda", 12),
    ("IR sobre ganho de capital", 13),
    ("Patrimônio líquido (se vender)", 17),
    ("Patrimônio em R$ de hoje", 16), ("Renda mensal disponível", 14),
    ("Total investido pelo cliente", 15),
]
MIM_C = {nome: i + 1 for i, (nome, _) in enumerate(MIM_COLS)}  # 1 = coluna A

# --------------------------------------------------------------------------
# ABA ADEQUAÇÃO — geometria
# --------------------------------------------------------------------------
ADE_CAB = 8
ADE_INI = 9
ADE_FIM = ADE_INI + (PROD_LIN_FIM - PROD_LIN_INI)   # espelha a base de produtos (9..78)
ADE_PESOS_USO = 7                                    # B7:E7 — pesos em uso
ADE_TOP_CAB = 81
ADE_TOP_INI = 82                                     # ordem de aderência (6 primeiros)
ADE_TOP_FIM = 87
ADE_PESOS_CAB = 90
ADE_PESOS_INI = 91                                   # 91..94 (4 prioridades)
ADE_PESOS_FIM = 94
ADE_MATRIZ_CAB = 97
ADE_MATRIZ_INI = 98                                  # 98..101 (4 prioridades × 5 riscos)
ADE_MATRIZ_FIM = 101

# --------------------------------------------------------------------------
# NOMES DEFINIDOS
# --------------------------------------------------------------------------
NOMES = {
    # Entradas do cliente
    "IN_NOME":        f"{AB_CLIENTE}!$F$5",
    "IN_DATA_SIM":    f"{AB_CLIENTE}!$F$6",
    "IN_CAPITAL":     f"{AB_CLIENTE}!$F$10",
    "IN_APORTE":      f"{AB_CLIENTE}!$F$12",
    "IN_HORIZONTE":   f"{AB_CLIENTE}!$F$14",
    "IN_PRAZO_CUSTOM": f"{AB_CLIENTE}!$F$15",
    "IN_PRAZO":       f"{AB_CLIENTE}!$F$16",
    "IN_RESGATE":     f"{AB_CLIENTE}!$F$18",
    "IN_PRIORIDADE":  f"{AB_CLIENTE}!$F$20",
    "IN_PERFIL":      f"{AB_CLIENTE}!$F$22",
    "IN_DESTAQUE":    f"{AB_CLIENTE}!$F$28",

    # Parâmetros do consultor
    "CENARIO":         f"{AB_CONSULTOR}!$D$5",
    "DATA_INICIO":     f"{AB_CONSULTOR}!$D$6",
    "APORTE_CORRIGIDO": f"{AB_CONSULTOR}!$D$7",
    "AUTO_SUGESTAO":   f"{AB_CONSULTOR}!$D$8",
    "PGBL_REINVESTE":  f"{AB_CONSULTOR}!$D$9",
    "PGBL_RENDA":      f"{AB_CONSULTOR}!$D$10",
    "PGBL_ALIQ":       f"{AB_CONSULTOR}!$D$11",
    "PGBL_COMPLETA":   f"{AB_CONSULTOR}!$D$12",
    "PGBL_BENEFICIO":  f"{AB_CONSULTOR}!$D$13",

    # Detalhamento mês a mês
    "MES_DETALHE":     f"{AB_MESAMES}!$D$4",

    # Imóvel
    "IMOV_INCLUIR":     f"{AB_IMOVEL}!$F$5",
    "IMOV_VALOR":       f"{AB_IMOVEL}!$F$6",
    "IMOV_ITBI":        f"{AB_IMOVEL}!$F$7",
    "IMOV_CARTORIO":    f"{AB_IMOVEL}!$F$8",
    "IMOV_DESEMBOLSO":  f"{AB_IMOVEL}!$F$9",
    "IMOV_MODO_ALUGUEL": f"{AB_IMOVEL}!$F$12",
    "IMOV_ALUGUEL":     f"{AB_IMOVEL}!$F$13",
    "IMOV_ALUGUEL_USO": f"{AB_IMOVEL}!$F$14",
    "IMOV_VACANCIA":    f"{AB_IMOVEL}!$F$15",
    "IMOV_REAJUSTE":    f"{AB_IMOVEL}!$F$16",
    "IMOV_IPTU":        f"{AB_IMOVEL}!$F$19",
    "IMOV_MANUT":       f"{AB_IMOVEL}!$F$20",
    "IMOV_ADM":         f"{AB_IMOVEL}!$F$21",
    "IMOV_VALORIZACAO": f"{AB_IMOVEL}!$F$24",
    "IMOV_CORRETAGEM":  f"{AB_IMOVEL}!$F$25",
    "IMOV_ISENCAO_GC":  f"{AB_IMOVEL}!$F$26",
    "IMOV_DESTINO":     f"{AB_IMOVEL}!$F$29",
    "IMOV_TAXA_REINV":  f"{AB_IMOVEL}!$F$30",

    # Faixas usadas com frequência
    "BASE_PRODUTOS":  PROD_FAIXA_NOMES,
    "TAB_IR":         f"{AB_PREMISSAS}!${PRE_IR_COL_INI}${PRE_IR_INI}:${PRE_IR_COL_FIM}${PRE_IR_FIM}",
    "TAB_IR_DIAS":    f"{AB_PREMISSAS}!$A${PRE_IR_INI}:$A${PRE_IR_FIM}",
    "TAB_IR_REGIMES": f"{AB_PREMISSAS}!${PRE_IR_COL_INI}${PRE_IR_CAB}:${PRE_IR_COL_FIM}${PRE_IR_CAB}",
    "TAB_MACRO_COD":  f"{AB_PREMISSAS}!$B${PRE_MACRO_INI}:$B${PRE_MACRO_FIM}",
    "TAB_MACRO_VAL":  f"{AB_PREMISSAS}!${PRE_COL_RESOLVIDO}${PRE_MACRO_INI}:${PRE_COL_RESOLVIDO}${PRE_MACRO_FIM}",
    "IPCA_CENARIO":   f"{AB_PREMISSAS}!${PRE_COL_RESOLVIDO}${PRE_MACRO_INI + 2}",
    "SELIC_CENARIO":  f"{AB_PREMISSAS}!${PRE_COL_RESOLVIDO}${PRE_MACRO_INI}",
    "CDI_CENARIO":    f"{AB_PREMISSAS}!${PRE_COL_RESOLVIDO}${PRE_MACRO_INI + 1}",
    "TAB_IRPF_BASE":  f"{AB_PREMISSAS}!$A${PRE_IRPF_INI}:$A${PRE_IRPF_FIM}",
    "TAB_IRPF_ALIQ":  f"{AB_PREMISSAS}!$B${PRE_IRPF_INI}:$B${PRE_IRPF_FIM}",
    "TAB_IRPF_DED":   f"{AB_PREMISSAS}!$C${PRE_IRPF_INI}:$C${PRE_IRPF_FIM}",
    "LIMITE_FGC":     f"{AB_PREMISSAS}!$B${PRE_OUTROS_INI}",
    "LIMITE_PGBL":    f"{AB_PREMISSAS}!$B${PRE_OUTROS_INI + 1}",
    "ALIQ_GANHO_CAP": f"{AB_PREMISSAS}!$B${PRE_OUTROS_INI + 2}",
    "DATA_DADOS":     f"{AB_PREMISSAS}!$B$4",
}

# Slots: escolha efetiva usada pelo motor.
# A tabela de escolhas da aba Consultor tem o cabeçalho na linha 16, então a
# primeira alternativa é a 17. Estas linhas e as de interface.py precisam
# andar juntas — por isso a constante mora aqui, e não espalhada nas duas.
CONS_SLOT_CAB = 16
CONS_SLOT_INI = CONS_SLOT_CAB + 1
for _i, _L in enumerate(SLOT_LETRAS):
    NOMES[f"SLOT_{_L}"] = f"{AB_CONSULTOR}!$H${CONS_SLOT_INI + _i}"


def col_slot(indice_slot, chave_coluna):
    """Índice absoluto (1=A) da coluna de um campo da grade, para um slot."""
    return MOT_SLOT_COL0 + indice_slot * MOT_SLOT_PASSO + MOT_G[chave_coluna]


def letra(idx):
    from openpyxl.utils import get_column_letter
    return get_column_letter(idx)


def ref_motor(indice_slot, chave_coluna, linha, absoluto=False):
    """Referência 'Motor!X99' para um campo da grade mensal."""
    c = letra(col_slot(indice_slot, chave_coluna))
    if absoluto:
        return f"{AB_MOTOR}!${c}${linha}"
    return f"{AB_MOTOR}!{c}{linha}"


def linha_mes(mes):
    """Linha da grade do Motor correspondente a um mês."""
    return MOT_GRID_INI + mes


def ref_param(indice_slot, rotulo, absoluto=True):
    """Referência a uma linha do bloco de parâmetros do Motor."""
    c = letra(MOT_COL_SLOT0 + indice_slot)
    lin = MOT_P[rotulo]
    return f"${c}${lin}" if absoluto else f"{c}{lin}"


def ref_param_ext(indice_slot, rotulo):
    return f"{AB_MOTOR}!{ref_param(indice_slot, rotulo)}"
