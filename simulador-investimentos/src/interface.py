"""
CAMADA DE INTERFACE — o que o cliente e o consultor enxergam.

Duas leituras da mesma simulação:
  MODO CLIENTE   (abas Início, Cliente, Comparar, Relatório) — linguagem simples,
                 poucos números, nenhum jargão.
  MODO CONSULTOR (abas Consultor, MesAMes, Imóvel, Previdência) — premissas,
                 taxas, tributação, origem e data de cada dado.

Nenhum cálculo financeiro acontece aqui: estas abas só leem o Motor.
"""

from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.formatting.rule import FormulaRule
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.comments import Comment

from .estilo import *          # noqa: F403
from .refs import *            # noqa: F403
from . import dados_seed as D

N_ALT = N_SLOTS + 1            # 6 alternativas financeiras + imóvel
COMP_INI = 7                   # primeira linha da tabela de comparação
COMP_FIM = COMP_INI + N_ALT - 1
ANO_CAB = 16
ANO_INI = 17
ANOS = 20
ANO_FIM = ANO_INI + ANOS

DISCLAIMER = ("Simulação baseada nas informações e premissas registradas nesta planilha. "
              "Os resultados reais podem ser diferentes. Rentabilidade passada não é garantia "
              "de rentabilidade futura e nenhum número aqui representa promessa de retorno.")
NAO_OFICIAL = ("Ferramenta de apoio à conversa, de uso do profissional. Não é peça oficial de "
               "oferta e não substitui a lâmina, o regulamento, o prospecto do produto nem o "
               "questionário oficial de perfil (suitability).")


# --------------------------------------------------------------------------
# Leitura do motor
# --------------------------------------------------------------------------
def _nome_alt(i):
    if i < N_SLOTS:
        return f"{AB_MOTOR}!${get_column_letter(2 + i)}${MOT_P['Produto selecionado']}"
    return None                                     # imóvel: rótulo fixo


def _ativo_alt(i):
    if i < N_SLOTS:
        return f"{AB_MOTOR}!${get_column_letter(2 + i)}${MOT_P['Alternativa em uso (1/0)']}"
    return f"{AB_MOTOR_IMOVEL}!$B${MIM_P['Entra na comparação (1/0)']}"


def _res(i, rotulo):
    if i < N_SLOTS:
        return f"{AB_MOTOR}!${get_column_letter(2 + i)}${MOT_R[rotulo]}"
    return f"{AB_MOTOR_IMOVEL}!$B${MIM_R[rotulo]}"


def _par(i, rotulo):
    if i < N_SLOTS:
        return f"{AB_MOTOR}!${get_column_letter(2 + i)}${MOT_P[rotulo]}"
    return None


def _destaque(rotulo, alvo="IN_DESTAQUE"):
    """Valor do resumo para a alternativa em destaque (slot A-F ou Imóvel)."""
    return (f'IF({alvo}="Imóvel",{AB_MOTOR_IMOVEL}!$B${MIM_R[rotulo]},'
            f'IFERROR(INDEX({AB_MOTOR}!$B${MOT_R[rotulo]}:$G${MOT_R[rotulo]},'
            f'MATCH("ALTERNATIVA "&{alvo},'
            f'{AB_MOTOR}!$B${MOT_PAR_CAB}:$G${MOT_PAR_CAB},0)),0))')


def _dv(ws, formula1, celulas, titulo="", mensagem=""):
    dv = DataValidation(type="list", formula1=formula1, allow_blank=True,
                        showDropDown=False, showErrorMessage=False)
    if mensagem:
        dv.promptTitle, dv.prompt, dv.showInputMessage = titulo, mensagem, True
    ws.add_data_validation(dv)
    for c in celulas:
        dv.add(c)


def _lista(v):
    return '"' + ",".join(v) + '"'


def _pergunta(ws, linha, texto, dica=None, altura=26):
    ws.merge_cells(f"B{linha}:E{linha}")
    escreve(ws, f"B{linha}", texto, tam=11, negrito=True, cor=AZUL_ESCURO,
            alinha=AL_ESQ_WRAP)
    ws.merge_cells(f"F{linha}:G{linha}")
    ws.row_dimensions[linha].height = altura
    if dica:
        ws.merge_cells(f"B{linha + 1}:G{linha + 1}")
        escreve(ws, f"B{linha + 1}", dica, tam=8.5, cor=CINZA_SUAVE, italico=True,
                alinha=AL_ESQ_WRAP)
        ws.row_dimensions[linha + 1].height = 14


def _derivado(ws, linha, texto, formula, fmt=None):
    ws.merge_cells(f"B{linha}:E{linha}")
    escreve(ws, f"B{linha}", texto, tam=10, negrito=True, cor=VERDE, alinha=AL_ESQ_WRAP)
    ws.merge_cells(f"F{linha}:G{linha}")
    escreve(ws, f"F{linha}", formula, tam=11, negrito=True, cor=VERDE, bg=VERDE_CLARO,
            fmt=fmt, alinha=AL_CENTRO, borda=BORDA_CAIXA)
    ws.row_dimensions[linha].height = 22


def _botoes(ws, linha, itens, col_ini="B", largura=2):
    """Barra de navegação: cada botão é um hyperlink interno."""
    col = ord(col_ini) - 65 + 1
    for aba, rotulo in itens:
        c1 = get_column_letter(col)
        c2 = get_column_letter(col + largura - 1)
        if largura > 1:
            ws.merge_cells(f"{c1}{linha}:{c2}{linha}")
        link_aba(ws, f"{c1}{linha}", aba, rotulo)
        col += largura
    ws.row_dimensions[linha].height = 26


# ==========================================================================
# ABA INÍCIO
# ==========================================================================
def construir_inicio(wb):
    ws = wb[AB_INICIO]
    esconde_grade(ws)
    larguras(ws, {"A": 3, "B": 26, "C": 26, "D": 26, "E": 26, "F": 26, "G": 26, "H": 3})

    ws.merge_cells("A1:H3")
    escreve(ws, "A1", "   SIMULADOR DE INVESTIMENTOS\n   Ferramenta de apoio à conversa com o cliente",
            tam=20, negrito=True, cor=BRANCO, bg=AZUL_ESCURO, alinha=AL_ESQ_WRAP)
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 26
    ws.row_dimensions[3].height = 20

    nota(ws, 5,
         "O motor faz contas sofisticadas — mês a mês, com imposto, come-cotas, custos e inflação. "
         "O painel mostra pouca coisa: quanto entra, por quanto tempo, quanto pode virar, quando dá "
         "para retirar e qual o risco. A profundidade fica a um clique de distância, na aba Consultor.",
         ate_col="H", altura=34, cor=CINZA_TEXTO, tam=10)

    secao(ws, 7, "COMEÇAR O ATENDIMENTO", ate_col="H")
    passos = [
        (AB_CLIENTE, "1 · CLIENTE",
         "As cinco perguntas e o resultado em linguagem simples. É a tela para virar o monitor para o cliente."),
        (AB_COMPARAR, "2 · COMPARAR",
         "As alternativas lado a lado e os gráficos de evolução, composição e renda."),
        (AB_RELATORIO, "3 · RELATÓRIO",
         "Resumo de uma página, pronto para imprimir ou salvar em PDF e entregar ao cliente."),
    ]
    lin = 8
    for aba, rotulo, desc in passos:
        ws.merge_cells(f"B{lin}:C{lin}")
        link_aba(ws, f"B{lin}", aba, rotulo, bg=AZUL, tam=12)
        ws.merge_cells(f"D{lin}:H{lin}")
        escreve(ws, f"D{lin}", desc, tam=9.5, cor=CINZA_TEXTO, alinha=AL_ESQ_WRAP)
        ws.row_dimensions[lin].height = 30
        lin += 1

    secao(ws, 12, "APROFUNDAR (MODO CONSULTOR)", ate_col="H")
    consultor = [
        (AB_CONSULTOR, "CONSULTOR", "Premissas, taxas, tributação, alertas e o painel técnico completo."),
        (AB_MESAMES, "MÊS A MÊS", "A projeção linha a linha: saldo, rendimento, aporte, custos e imposto."),
        (AB_IMOVEL, "IMÓVEL", "Comprar para alugar: aluguel, vacância, IPTU, manutenção, compra e venda."),
        (AB_PREV, "PREVIDÊNCIA", "PGBL x VGBL, progressivo x regressivo e o valor real do benefício fiscal."),
        (AB_ADEQUACAO, "ADERÊNCIA", "Como a planilha decide o que sugerir — e por que não é um ranking de rentabilidade."),
    ]
    lin = 13
    for aba, rotulo, desc in consultor:
        ws.merge_cells(f"B{lin}:C{lin}")
        link_aba(ws, f"B{lin}", aba, rotulo, bg=AZUL_MEDIO, tam=11)
        ws.merge_cells(f"D{lin}:H{lin}")
        escreve(ws, f"D{lin}", desc, tam=9.5, cor=CINZA_TEXTO, alinha=AL_ESQ_WRAP)
        ws.row_dimensions[lin].height = 26
        lin += 1

    secao(ws, 19, "MANUTENÇÃO DA FERRAMENTA", ate_col="H")
    manut = [
        (AB_PRODUTOS, "PRODUTOS", "Base de produtos: cadastrar, alterar taxa, ativar ou desativar."),
        (AB_PREMISSAS, "PREMISSAS", "Indicadores, cenários e todas as tabelas de tributação."),
        (AB_FONTES, "FONTES", "De onde vem cada dado, com que atraso, e o registro de atualizações."),
        (AB_GLOSSARIO, "GLOSSÁRIO", "Explicações curtas para usar na conversa com o cliente."),
    ]
    lin = 20
    for aba, rotulo, desc in manut:
        ws.merge_cells(f"B{lin}:C{lin}")
        link_aba(ws, f"B{lin}", aba, rotulo, bg=LARANJA, tam=11)
        ws.merge_cells(f"D{lin}:H{lin}")
        escreve(ws, f"D{lin}", desc, tam=9.5, cor=CINZA_TEXTO, alinha=AL_ESQ_WRAP)
        ws.row_dimensions[lin].height = 26
        lin += 1

    secao(ws, 25, "SITUAÇÃO DOS DADOS AGORA", ate_col="H")
    painel = [
        ("Cenário em uso", "=CENARIO", None),
        ("Data de atualização dos dados", "=DATA_DADOS", None),
        ("Produtos ativos na base",
         f'=COUNTIF({AB_PRODUTOS}!${get_column_letter(PROD_COL["ativo"])}${PROD_LIN_INI}:'
         f'${get_column_letter(PROD_COL["ativo"])}${PROD_LIN_FIM},"SIM")', FMT_INT),
        ("Produtos ainda não conferidos",
         f'=COUNTIF({AB_PRODUTOS}!${get_column_letter(PROD_COL["status"])}${PROD_LIN_INI}:'
         f'${get_column_letter(PROD_COL["status"])}${PROD_LIN_FIM},"EXEMPLO*")', FMT_INT),
    ]
    for i, (rotulo, formula, fmt) in enumerate(painel):
        lin = 26 + i
        ws.merge_cells(f"B{lin}:D{lin}")
        escreve(ws, f"B{lin}", rotulo, tam=10, negrito=True, alinha=AL_ESQ)
        ws.merge_cells(f"E{lin}:F{lin}")
        escreve(ws, f"E{lin}", formula, tam=11, negrito=True, cor=AZUL_ESCURO,
                bg=AZUL_CLARO, fmt=fmt, alinha=AL_CENTRO, borda=BORDA_CAIXA)
        ws.row_dimensions[lin].height = 20

    escreve(ws, "G26",
            '=IF(E29>0,"⚠ Há produtos com taxa de exemplo. Confira antes de usar com cliente.",'
            '"Todos os produtos da base estão marcados como conferidos.")',
            tam=9, negrito=True, cor=AMBAR, alinha=AL_ESQ_WRAP)
    ws.merge_cells("G26:H29")

    aviso(ws, 31, NAO_OFICIAL, ate_col="H")
    aviso(ws, 32, DISCLAIMER, ate_col="H")

    ws.sheet_properties.tabColor = AZUL_ESCURO


# ==========================================================================
# ABA CLIENTE
# ==========================================================================
def construir_cliente(wb):
    ws = wb[AB_CLIENTE]
    esconde_grade(ws)
    titulo_pagina(ws, "SUA SIMULAÇÃO",
                  "Poucas perguntas, e você vê o que pode acontecer com o seu dinheiro",
                  ate_col="K")
    larguras(ws, {"A": 2, "B": 34, "C": 16, "D": 16, "E": 16, "F": 18, "G": 16,
                  "H": 18, "I": 16, "J": 32, "K": 32, "L": 2})

    # ---------------- passo 1 ----------------
    secao(ws, 4, "PASSO 1 · QUEM ESTAMOS ATENDENDO", ate_col="K")
    _pergunta(ws, 5, "Nome do cliente")
    celula_input(ws, "F5", "(preencher)", alinha=AL_CENTRO)
    _pergunta(ws, 6, "Data desta simulação")
    celula_input(ws, "F6", "=TODAY()", fmt=FMT_DATA, alinha=AL_CENTRO)

    # ---------------- passo 2 ----------------
    secao(ws, 8, "PASSO 2 · CINCO PERGUNTAS", ate_col="K")
    nota(ws, 9, "Só o que está em amarelo precisa ser preenchido. O resto a planilha calcula sozinha.",
         ate_col="K")

    _pergunta(ws, 10, "Quanto você pretende investir agora?",
              "Se ainda não tem certeza, use um valor aproximado — dá para mudar durante a conversa.")
    celula_input(ws, "F10", 150000, fmt=FMT_MOEDA, alinha=AL_CENTRO)

    _pergunta(ws, 12, "Você pretende guardar mais alguma coisa por mês?",
              "Se não pretende, deixe zero.")
    celula_input(ws, "F12", 0, fmt=FMT_MOEDA, alinha=AL_CENTRO)

    _pergunta(ws, 14, "Por quanto tempo você pode deixar esse dinheiro investido?")
    celula_input(ws, "F14", "5 a 10 anos", alinha=AL_CENTRO)
    _dv(ws, _lista([h[0] for h in D.HORIZONTES]), ["F14"])

    _pergunta(ws, 15, "Se escolheu “Prazo personalizado”, quantos meses?", altura=20)
    celula_input(ws, "F15", 120, fmt=FMT_INT, alinha=AL_CENTRO)

    _derivado(ws, 16, "➜ Prazo usado na simulação (meses)",
              f'=IF(IN_HORIZONTE="Prazo personalizado",MAX(1,MIN({MESES_MAX},IN_PRAZO_CUSTOM)),'
              f"IFERROR(INDEX({AB_PREMISSAS}!$B${PRE_HOR_INI}:$B${PRE_HOR_FIM},"
              f"MATCH(IN_HORIZONTE,{AB_PREMISSAS}!$A${PRE_HOR_INI}:$A${PRE_HOR_FIM},0)),120))",
              fmt=FMT_INT)
    ws.merge_cells("H16:K16")
    escreve(ws, "H16", f'="Isso equivale a cerca de "&ROUND(IN_PRAZO/12,1)&" anos."',
            tam=9, cor=CINZA_SUAVE, italico=True, alinha=AL_ESQ)

    _pergunta(ws, 18, "Você pode precisar desse dinheiro antes do prazo?",
              "Essa resposta pesa muito: ela define se vale a pena travar o dinheiro por uma taxa melhor.")
    celula_input(ws, "F18", "Talvez", alinha=AL_CENTRO)
    _dv(ws, _lista(D.RESGATE_ANTES), ["F18"])

    _pergunta(ws, 20, "O que é mais importante para você?",
              "Não existe resposta certa. Existe a resposta que combina com o seu momento.")
    celula_input(ws, "F20", "Equilíbrio entre segurança e rentabilidade", alinha=AL_CENTRO)
    _dv(ws, _lista(D.PRIORIDADES), ["F20"])

    _pergunta(ws, 22, "Perfil de investidor (do questionário oficial)",
              "Este campo repete o perfil já apurado no sistema da instituição. A planilha não substitui esse processo.")
    celula_input(ws, "F22", "Moderado", alinha=AL_CENTRO)
    _dv(ws, _lista(D.PERFIS), ["F22"])

    ws.merge_cells("B24:K24")
    escreve(ws, "B24",
            '=IF(IN_CAPITAL<=0,"⚠ Informe quanto o cliente pretende investir para a simulação começar.",'
            f'IF(COUNTIF({AB_MOTOR}!$B${MOT_P["Alternativa em uso (1/0)"]}:'
            f'$G${MOT_P["Alternativa em uso (1/0)"]},1)=0,'
            '"⚠ Nenhuma alternativa escolhida ainda. Vá até a aba Consultor ou ligue a sugestão automática.",'
            '"Tudo certo. Os resultados abaixo já refletem estas respostas."))',
            tam=10, negrito=True, cor=AMBAR, bg=AMBAR_CLARO, alinha=AL_ESQ_WRAP)
    ws.row_dimensions[24].height = 24

    # ---------------- passo 3 ----------------
    secao(ws, 26, "PASSO 3 · COMO SEU DINHEIRO PODE EVOLUIR", ate_col="K")
    nota(ws, 27, "Escolha uma alternativa para olhar de perto. A comparação completa está logo abaixo.",
         ate_col="K")
    _pergunta(ws, 28, "Vamos olhar esta alternativa:", altura=22)
    celula_input(ws, "F28", "A", alinha=AL_CENTRO)
    _dv(ws, _lista(SLOT_LETRAS + ["Imóvel"]), ["F28"])
    ws.merge_cells("H28:K28")
    escreve(ws, "H28",
            f'=IF(IN_DESTAQUE="Imóvel","Imóvel para aluguel",'
            f'IFERROR(INDEX({AB_MOTOR}!$B${MOT_P["Produto selecionado"]}:'
            f'$G${MOT_P["Produto selecionado"]},'
            f'MATCH("ALTERNATIVA "&IN_DESTAQUE,'
            f'{AB_MOTOR}!$B${MOT_PAR_CAB}:$G${MOT_PAR_CAB},0)),"(não escolhida)"))',
            tam=12, negrito=True, cor=AZUL_ESCURO, alinha=AL_ESQ)

    cards = [
        ("B", "C", "HOJE VOCÊ COLOCA", "=IN_CAPITAL",
         '="Mais "&TEXT(IN_APORTE,"R$ #,##0")&" por mês"'),
        ("D", "E", '="EM "&ROUND(INT(IN_PRAZO/2)/12,0)&" ANOS"',
         f"={_destaque('Patrimônio líquido na metade do prazo')}",
         '="Metade do caminho"'),
        ("F", "G", '="EM "&ROUND(IN_PRAZO/12,0)&" ANOS"',
         f"={_destaque('Patrimônio líquido no prazo')}",
         '="Já com imposto e custos descontados"'),
        ("H", "I", "GANHO ESTIMADO",
         f"={_destaque('Ganho líquido')}",
         f'="Equivale a "&TEXT({_destaque("Rentabilidade líquida acumulada")},"0.0%")&" sobre o investido"'),
    ]
    for c1, c2, rotulo, valor, sub in cards:
        ws.merge_cells(f"{c1}30:{c2}30")
        escreve(ws, f"{c1}30", rotulo, tam=9, negrito=True, cor=BRANCO, bg=AZUL,
                alinha=AL_CENTRO)
        ws.merge_cells(f"{c1}31:{c2}31")
        escreve(ws, f"{c1}31", valor, tam=18, negrito=True, cor=AZUL_ESCURO,
                bg=AZUL_MUITO_CLARO, fmt=FMT_MOEDA, alinha=AL_CENTRO, borda=BORDA_CAIXA)
        ws.merge_cells(f"{c1}32:{c2}32")
        escreve(ws, f"{c1}32", sub, tam=8.5, cor=CINZA_SUAVE, bg=AZUL_MUITO_CLARO,
                alinha=AL_CENTRO_WRAP)
    ws.row_dimensions[30].height = 18
    ws.row_dimensions[31].height = 34
    ws.row_dimensions[32].height = 22

    # ---------------- passo 4 ----------------
    secao(ws, 34, "PASSO 4 · O QUE MAIS IMPORTA SABER SOBRE ESSA ALTERNATIVA", ate_col="K")
    detalhes = [
        ("B", "C", "PARA RETIRAR", f"={_destaque('Para retirar (linguagem de cliente)')}", None),
        ("D", "E", "OSCILAÇÃO", f"={_destaque('Oscilação (linguagem de cliente)')}", None),
        ("F", "G", "RENDA MENSAL POSSÍVEL",
         f"={_destaque('Renda mensal potencial (nominal)')}", FMT_MOEDA),
        ("H", "I", "IMPOSTO ESTIMADO", f"={_destaque('Imposto total pago')}", FMT_MOEDA),
    ]
    for c1, c2, rotulo, valor, fmt in detalhes:
        ws.merge_cells(f"{c1}35:{c2}35")
        escreve(ws, f"{c1}35", rotulo, tam=8.5, negrito=True, cor=BRANCO, bg=AZUL_MEDIO,
                alinha=AL_CENTRO)
        ws.merge_cells(f"{c1}36:{c2}36")
        escreve(ws, f"{c1}36", valor, tam=12, negrito=True, cor=AZUL_ESCURO,
                bg=BRANCO, fmt=fmt, alinha=AL_CENTRO_WRAP, borda=BORDA_CAIXA)
    ws.row_dimensions[35].height = 16
    ws.row_dimensions[36].height = 28
    ws.merge_cells("J35:K36")
    escreve(ws, "J35",
            f'="O valor acima já está descontado de imposto e de custos. '
            f'Em poder de compra de hoje, equivale a "&TEXT({_destaque("Patrimônio líquido em R$ de hoje")},"R$ #,##0")&"."',
            tam=9, cor=CINZA_TEXTO, alinha=AL_ESQ_WRAP, bg=AZUL_MUITO_CLARO,
            borda=BORDA_CAIXA)

    # ---------------- passo 5 ----------------
    secao(ws, 38, "PASSO 5 · OPÇÕES QUE PODEM FAZER SENTIDO PARA O SEU OBJETIVO", ate_col="K")
    nota(ws, 39,
         "Esta não é uma lista do que rende mais. É uma lista do que combina com o seu prazo, com a sua "
         "necessidade de retirar e com o que você disse ser mais importante. A escolha final é sua.",
         ate_col="K", altura=24)

    cabecalho_tabela(ws, 40, 2,
                     ["Alternativa", "Você teria cerca de", "Ganho estimado",
                      "Renda mensal possível", "Para retirar", "Oscilação",
                      "Em R$ de hoje", "Aderência ao seu objetivo",
                      "Ponto forte", "Ponto de atenção"], altura=30)
    for i in range(N_ALT):
        r = 41 + i
        nome = (f"={_nome_alt(i)}" if i < N_SLOTS else '="Imóvel para aluguel"')
        ativo = _ativo_alt(i)
        bg = BRANCO if i % 2 == 0 else CINZA_FUNDO
        campos = [
            ("B", f'=IF({ativo}=0,"—",{nome[1:]})', None, AL_ESQ),
            ("C", f'=IF({ativo}=0,"",{_res(i,"Patrimônio líquido no prazo")})', FMT_MOEDA, AL_CENTRO),
            ("D", f'=IF({ativo}=0,"",{_res(i,"Ganho líquido")})', FMT_MOEDA, AL_CENTRO),
            ("E", f'=IF({ativo}=0,"",{_res(i,"Renda mensal potencial (nominal)")})', FMT_MOEDA, AL_CENTRO),
            ("F", f'=IF({ativo}=0,"",{_res(i,"Para retirar (linguagem de cliente)")})', None, AL_CENTRO_WRAP),
            ("G", f'=IF({ativo}=0,"",{_res(i,"Oscilação (linguagem de cliente)")})', None, AL_CENTRO),
            ("H", f'=IF({ativo}=0,"",{_res(i,"Patrimônio líquido em R$ de hoje")})', FMT_MOEDA, AL_CENTRO),
            ("I", f'=IF({ativo}=0,"",IFERROR(INDEX({AB_ADEQUACAO}!$S${ADE_INI}:$S${ADE_FIM},'
                  f'MATCH({nome[1:] if i < N_SLOTS else chr(34) + "Imóvel para aluguel" + chr(34)},'
                  f'{AB_ADEQUACAO}!$B${ADE_INI}:$B${ADE_FIM},0)),"—"))', None, AL_CENTRO_WRAP),
            ("J", f'=IF({ativo}=0,"",IFERROR(INDEX({AB_ADEQUACAO}!$T${ADE_INI}:$T${ADE_FIM},'
                  f'MATCH({nome[1:] if i < N_SLOTS else chr(34) + "Imóvel para aluguel" + chr(34)},'
                  f'{AB_ADEQUACAO}!$B${ADE_INI}:$B${ADE_FIM},0)),""))', None, AL_ESQ_WRAP),
            ("K", f'=IF({ativo}=0,"",IFERROR(INDEX({AB_ADEQUACAO}!$U${ADE_INI}:$U${ADE_FIM},'
                  f'MATCH({nome[1:] if i < N_SLOTS else chr(34) + "Imóvel para aluguel" + chr(34)},'
                  f'{AB_ADEQUACAO}!$B${ADE_INI}:$B${ADE_FIM},0)),""))', None, AL_ESQ_WRAP),
        ]
        for col, formula, fmt, alin in campos:
            escreve(ws, f"{col}{r}", formula, tam=9, bg=bg, fmt=fmt, alinha=alin,
                    borda=BORDA_GRADE, negrito=col in ("B", "C"),
                    cor=AZUL_ESCURO if col == "C" else CINZA_TEXTO)
        ws.row_dimensions[r].height = 30

    aviso(ws, 49, DISCLAIMER, ate_col="K")
    _botoes(ws, 51, [(AB_INICIO, "◀ INÍCIO"), (AB_COMPARAR, "VER GRÁFICOS ▶"),
                     (AB_MESAMES, "VER MÊS A MÊS"), (AB_GLOSSARIO, "O QUE SIGNIFICA?"),
                     (AB_RELATORIO, "GERAR RELATÓRIO"), (AB_CONSULTOR, "MODO CONSULTOR")])

    ws.sheet_properties.tabColor = AZUL
    ws.sheet_view.zoomScale = 90


# ==========================================================================
# ABA COMPARAR
# ==========================================================================
def construir_comparar(wb):
    ws = wb[AB_COMPARAR]
    esconde_grade(ws)
    titulo_pagina(ws, "COMPARANDO AS ALTERNATIVAS",
                  "As mesmas premissas, o mesmo prazo, o mesmo valor — para a comparação ser justa",
                  ate_col="O")
    larguras(ws, {"A": 2, "B": 34, "C": 17, "D": 15, "E": 15, "F": 14, "G": 14,
                  "H": 15, "I": 13, "J": 13, "K": 13, "L": 15, "M": 20, "N": 13, "O": 22})

    secao(ws, 4, "RESULTADO NO PRAZO ESCOLHIDO", ate_col="O")
    nota(ws, 5,
         '="  Cliente: "&IN_NOME&"   ·   Valor: "&TEXT(IN_CAPITAL,"R$ #,##0")'
         '&"   ·   Aporte mensal: "&TEXT(IN_APORTE,"R$ #,##0")'
         '&"   ·   Prazo: "&IN_PRAZO&" meses   ·   Cenário: "&CENARIO'
         '&"   ·   Dados de "&DATA_DADOS', ate_col="O", tam=9.5, cor=AZUL_ESCURO)

    cabecalho_tabela(ws, 6, 2,
                     ["Alternativa", "Patrimônio líquido", "Total investido",
                      "Ganho líquido", "Impostos", "Custos", "Em R$ de hoje",
                      "Rent. acum.", "Taxa a.a.", "Ganho real a.a.",
                      "Renda mensal", "Para retirar", "Oscilação",
                      "Aderência ao objetivo"], altura=34)

    for i in range(N_ALT):
        r = COMP_INI + i
        ativo = _ativo_alt(i)
        nome_expr = (_nome_alt(i) if i < N_SLOTS else '"Imóvel para aluguel"')
        chave = (_nome_alt(i) if i < N_SLOTS else '"Imóvel para aluguel"')
        campos = [
            ("B", f'=IF({ativo}=0,"— alternativa {SLOT_LETRAS[i] if i < N_SLOTS else "imóvel"} não usada",{nome_expr})', None, AL_ESQ),
            ("C", f'=IF({ativo}=0,0,{_res(i,"Patrimônio líquido no prazo")})', FMT_MOEDA, AL_CENTRO),
            ("D", f'=IF({ativo}=0,0,{_res(i,"Total investido (capital + aportes)")})', FMT_MOEDA, AL_CENTRO),
            ("E", f'=IF({ativo}=0,0,{_res(i,"Ganho líquido")})', FMT_MOEDA, AL_CENTRO),
            ("F", f'=IF({ativo}=0,0,{_res(i,"Imposto total pago")})', FMT_MOEDA, AL_CENTRO),
            ("G", f'=IF({ativo}=0,0,{_res(i,"Custos totais pagos")})', FMT_MOEDA, AL_CENTRO),
            ("H", f'=IF({ativo}=0,0,{_res(i,"Patrimônio líquido em R$ de hoje")})', FMT_MOEDA, AL_CENTRO),
            ("I", f'=IF({ativo}=0,0,{_res(i,"Rentabilidade líquida acumulada")})', FMT_PCT, AL_CENTRO),
            ("J", f'=IF({ativo}=0,0,{_res(i,"Taxa líquida equivalente a.a.")})', FMT_PCT, AL_CENTRO),
            ("K", f'=IF({ativo}=0,0,{_res(i,"Ganho real a.a. (acima da inflação)")})', FMT_PCT, AL_CENTRO),
            ("L", f'=IF({ativo}=0,0,{_res(i,"Renda mensal potencial (nominal)")})', FMT_MOEDA, AL_CENTRO),
            ("M", f'=IF({ativo}=0,"",{_res(i,"Para retirar (linguagem de cliente)")})', None, AL_CENTRO_WRAP),
            ("N", f'=IF({ativo}=0,"",{_res(i,"Oscilação (linguagem de cliente)")})', None, AL_CENTRO),
            ("O", f'=IF({ativo}=0,"",IFERROR(INDEX({AB_ADEQUACAO}!$S${ADE_INI}:$S${ADE_FIM},'
                  f'MATCH({chave},{AB_ADEQUACAO}!$B${ADE_INI}:$B${ADE_FIM},0)),"—"))', None, AL_CENTRO_WRAP),
        ]
        bg = BRANCO if i % 2 == 0 else CINZA_FUNDO
        for col, formula, fmt, alin in campos:
            escreve(ws, f"{col}{r}", formula, tam=9, bg=bg, fmt=fmt, alinha=alin,
                    borda=BORDA_GRADE, negrito=col in ("B", "C"),
                    cor=AZUL_ESCURO if col == "C" else CINZA_TEXTO)
        ws.row_dimensions[r].height = 26

    # Coluna auxiliar: patrimônio apenas das alternativas em uso (vazio nas demais).
    # MIN e MAX ignoram texto, então isso dá o maior e o menor SEM contar os lugares vazios.
    escreve(ws, f"Q{6}", "Auxiliar (só as em uso)", tam=7.5, cor=CINZA_SUAVE,
            alinha=AL_CENTRO_WRAP)
    ws.column_dimensions["Q"].width = 16
    for i in range(N_ALT):
        r = COMP_INI + i
        escreve(ws, f"Q{r}", f'=IF({_ativo_alt(i)}=0,"",$C{r})', tam=7.5,
                cor=CINZA_SUAVE, fmt=FMT_MOEDA, alinha=AL_CENTRO)

    ws.conditional_formatting.add(
        f"C{COMP_INI}:C{COMP_FIM}",
        FormulaRule(formula=[f"AND($C{COMP_INI}>0,$C{COMP_INI}=MAX($Q${COMP_INI}:$Q${COMP_FIM}))"],
                    fill=fill(VERDE_CLARO), stopIfTrue=False))
    nota(ws, COMP_FIM + 1,
         "O maior patrimônio aparece destacado apenas como informação. Maior patrimônio não significa "
         "melhor escolha: liquidez, risco e objetivo pesam tanto quanto o número.",
         ate_col="O", altura=18)

    # ---------------- série anual (base dos gráficos) ----------------
    secao(ws, ANO_CAB - 1, "EVOLUÇÃO ANO A ANO (base dos gráficos)", ate_col="O")
    escreve(ws, f"A{ANO_CAB}", "Ano", tam=8, negrito=True, cor=BRANCO, bg=AZUL_ESCURO,
            alinha=AL_CENTRO, borda=BORDA_GRADE)
    for i in range(N_ALT):
        col = get_column_letter(2 + i)
        nome_expr = (f"={_nome_alt(i)}" if i < N_SLOTS else '="Imóvel para aluguel"')
        escreve(ws, f"{col}{ANO_CAB}",
                f'=IF({_ativo_alt(i)}=0,"(não usada {SLOT_LETRAS[i] if i < N_SLOTS else "imóvel"})",{nome_expr[1:]})',
                tam=8, negrito=True, cor=BRANCO, bg=AZUL_MEDIO, alinha=AL_CENTRO_WRAP,
                borda=BORDA_GRADE)
    ws.row_dimensions[ANO_CAB].height = 30

    liq_imovel = get_column_letter(MIM_C["Patrimônio líquido (se vender)"])
    for n in range(ANOS + 1):
        r = ANO_INI + n
        escreve(ws, f"A{r}", n, tam=8, fmt=FMT_INT, alinha=AL_CENTRO, borda=BORDA_GRADE)
        for i in range(N_ALT):
            col = get_column_letter(2 + i)
            if i < N_SLOTS:
                gcol = get_column_letter(MOT_SLOT_COL0 + i * MOT_SLOT_PASSO + MOT_G["liquido"])
                dado = (f"INDEX({AB_MOTOR}!${gcol}${MOT_GRID_INI}:${gcol}${MOT_GRID_FIM},"
                        f"{n * 12}+1)")
            else:
                dado = (f"INDEX({AB_MOTOR_IMOVEL}!${liq_imovel}${MIM_GRID_INI}:"
                        f"${liq_imovel}${MIM_GRID_FIM},{n * 12}+1)")
            escreve(ws, f"{col}{r}",
                    f'=IF(OR({n * 12}>IN_PRAZO,{_ativo_alt(i)}=0),"",{dado})',
                    tam=8, fmt=FMT_MOEDA, alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[r].height = 12

    _graficos_comparar(ws)

    aviso(ws, 92, DISCLAIMER, ate_col="O")
    _botoes(ws, 94, [(AB_INICIO, "◀ INÍCIO"), (AB_CLIENTE, "◀ CLIENTE"),
                     (AB_MESAMES, "MÊS A MÊS"), (AB_CONSULTOR, "VER DETALHES"),
                     (AB_RELATORIO, "GERAR RELATÓRIO")])
    ws.sheet_properties.tabColor = AZUL
    ws.sheet_view.zoomScale = 85


def _estilo_grafico(ch, titulo, largura=22, altura=10.5):
    ch.title = titulo
    ch.width, ch.height = largura, altura
    ch.style = 2
    ch.y_axis.numFmt = "#,##0"
    return ch


def _graficos_comparar(ws):
    # 1) Evolução do patrimônio
    g1 = LineChart()
    _estilo_grafico(g1, "Como o patrimônio pode evoluir (R$)", 24, 11)
    dados = Reference(ws, min_col=2, min_row=ANO_CAB, max_col=1 + N_ALT, max_row=ANO_FIM)
    cats = Reference(ws, min_col=1, min_row=ANO_INI, max_row=ANO_FIM)
    g1.add_data(dados, titles_from_data=True)
    g1.set_categories(cats)
    g1.x_axis.title = "Anos"
    g1.y_axis.title = "Patrimônio líquido"
    g1.dispBlanksAs = "gap"
    for s in g1.series:
        s.smooth = False
    ws.add_chart(g1, f"B{ANO_FIM + 3}")

    # 2) Patrimônio final por alternativa
    g2 = BarChart()
    g2.type = "col"
    _estilo_grafico(g2, "Patrimônio líquido no fim do prazo (R$)", 15, 11)
    g2.add_data(Reference(ws, min_col=3, min_row=6, max_row=COMP_FIM), titles_from_data=True)
    g2.set_categories(Reference(ws, min_col=2, min_row=COMP_INI, max_row=COMP_FIM))
    g2.legend = None
    g2.dataLabels = DataLabelList()
    g2.dataLabels.showVal = True
    ws.add_chart(g2, f"J{ANO_FIM + 3}")

    # 3) Composição do resultado
    g3 = BarChart()
    g3.type = "col"
    g3.grouping = "stacked"
    g3.overlap = 100
    _estilo_grafico(g3, "De onde vem o resultado (R$)", 24, 10)
    g3.add_data(Reference(ws, min_col=4, min_row=6, max_col=5, max_row=COMP_FIM),
                titles_from_data=True)
    g3.set_categories(Reference(ws, min_col=2, min_row=COMP_INI, max_row=COMP_FIM))
    ws.add_chart(g3, f"B{ANO_FIM + 26}")

    # 4) Renda mensal potencial
    g4 = BarChart()
    g4.type = "col"
    _estilo_grafico(g4, "Renda mensal que o patrimônio poderia gerar (R$)", 15, 10)
    g4.add_data(Reference(ws, min_col=12, min_row=6, max_row=COMP_FIM), titles_from_data=True)
    g4.set_categories(Reference(ws, min_col=2, min_row=COMP_INI, max_row=COMP_FIM))
    g4.legend = None
    g4.dataLabels = DataLabelList()
    g4.dataLabels.showVal = True
    ws.add_chart(g4, f"J{ANO_FIM + 26}")


# ==========================================================================
# ABA CONSULTOR
# ==========================================================================
_PAINEL = [
    ("Produto", "Produto selecionado", None, None),
    ("Categoria", "Categoria", None, None),
    ("Emissor / gestor", "Emissor / Gestor", None, None),
    ("Indexador", "Benchmark", None, None),
    ("% do indexador", "% do benchmark", FMT_PCT, None),
    ("Spread contratado a.a.", "Spread a.a.", FMT_PCT2, None),
    ("Retorno BRUTO a.a. no cenário", "Retorno BRUTO a.a. (cenário)", FMT_PCT2, None),
    ("Taxa de administração a.a.", "Taxa de administração a.a.", FMT_PCT2, None),
    ("Custódia a.a.", "Custódia a.a.", FMT_PCT2, None),
    ("Taxa de performance", "Taxa de performance", FMT_PCT, None),
    ("Carregamento entrada / saída", "Carregamento de entrada", FMT_PCT2, None),
    ("Retorno LÍQUIDO a.a. estimado", "Retorno LÍQUIDO a.a. estimado", FMT_PCT2, None),
    ("Regime tributário", "Regime tributário", None, None),
    ("Come-cotas", "Tem come-cotas (1/0)", FMT_INT, None),
    ("Carência (dias)", "Carência (dias)", FMT_INT, None),
    ("Liquidez após carência (dias)", "Liquidez (dias)", FMT_INT, None),
    ("Aplicação mínima", "Aplicação mínima", FMT_MOEDA, None),
    ("Risco (1-5)", "Risco (1-5)", FMT_INT, None),
    ("Volatilidade a.a.", "Volatilidade a.a.", FMT_PCT2, None),
    ("Garantia", "Garantia", None, None),
]


def construir_consultor(wb):
    ws = wb[AB_CONSULTOR]
    esconde_grade(ws)
    titulo_pagina(ws, "MODO CONSULTOR",
                  "Premissas, taxas, tributação e a origem de cada número",
                  ate_col="K")
    larguras(ws, {"A": 2, "B": 12, "C": 32, "D": 24, "E": 22, "F": 22, "G": 12,
                  "H": 22, "I": 22, "J": 22, "K": 22, "L": 2})

    # ---------------- parâmetros ----------------
    secao(ws, 4, "PARÂMETROS DA SIMULAÇÃO", ate_col="K")
    params = [
        (5, "Cenário de premissas", "Base", None, D.CENARIOS,
         "Cenário não é promessa. É um conjunto de premissas escolhido por você."),
        (6, "Data de início da simulação", "=TODAY()", FMT_DATA, None,
         "Define o mês do come-cotas e as datas de carência."),
        (7, "Corrigir o aporte mensal pela inflação?", "Não", None, D.SIM_NAO,
         "Se Sim, o aporte cresce junto com o IPCA do cenário."),
        (8, "Preencher as alternativas com a sugestão automática?", "Sim", None, D.SIM_NAO,
         "Se Sim, os seis lugares usam a ordem de aderência da aba Adequação."),
        (9, "Reinvestir a restituição do PGBL?", "Sim", None, D.SIM_NAO,
         "Se Sim, o benefício fiscal volta como aporte extra em maio de cada ano."),
        (10, "Renda bruta anual tributável do cliente", 0, FMT_MOEDA, None,
         "Base do limite de 12% de dedução do PGBL."),
        (11, "Alíquota marginal do IRPF do cliente", 0.275, FMT_PCT, None,
         "Quanto o cliente deixa de pagar sobre cada real deduzido."),
        (12, "O cliente declara IR no modelo completo?", "Não", None, D.SIM_NAO,
         "Sem isso, o PGBL perde a razão de existir e o VGBL costuma ser o caminho."),
    ]
    for lin, rotulo, valor, fmt, lista, dica in params:
        ws.merge_cells(f"B{lin}:C{lin}")
        escreve(ws, f"B{lin}", rotulo, tam=10, negrito=True, alinha=AL_ESQ_WRAP)
        celula_input(ws, f"D{lin}", valor, fmt=fmt, tam=10, alinha=AL_CENTRO)
        if lista:
            _dv(ws, _lista(lista), [f"D{lin}"])
        ws.merge_cells(f"E{lin}:K{lin}")
        escreve(ws, f"E{lin}", dica, tam=8.5, cor=CINZA_SUAVE, italico=True,
                alinha=AL_ESQ_WRAP)
        ws.row_dimensions[lin].height = 20

    ws.merge_cells("B13:C13")
    escreve(ws, "B13", "➜ Benefício fiscal anual do PGBL", tam=10, negrito=True, cor=VERDE)
    escreve(ws, "D13",
            '=IF(PGBL_COMPLETA<>"Sim",0,MIN(IN_APORTE*12,PGBL_RENDA*LIMITE_PGBL)*PGBL_ALIQ)',
            tam=10, negrito=True, cor=VERDE, bg=VERDE_CLARO, fmt=FMT_MOEDA,
            alinha=AL_CENTRO, borda=BORDA_CAIXA)
    ws.merge_cells("E13:K13")
    escreve(ws, "E13",
            '=IF(PGBL_COMPLETA<>"Sim","O cliente não declara no modelo completo: o PGBL não gera benefício e o VGBL tende a ser o caminho.",'
            '"Valor recorrente por ano. No primeiro ano o aporte inicial também é dedutível, gerando um benefício adicional de "'
            '&TEXT(MIN(IN_CAPITAL,MAX(0,PGBL_RENDA*LIMITE_PGBL-IN_APORTE*12))*PGBL_ALIQ,"R$ #,##0")&".")',
            tam=8.5, cor=VERDE, italico=True, alinha=AL_ESQ_WRAP)
    ws.row_dimensions[13].height = 22

    # ---------------- escolha das alternativas ----------------
    secao(ws, 15, "ALTERNATIVAS EM COMPARAÇÃO", ate_col="K")
    cab = CONS_SLOT_CAB
    for col, rotulo in (("B", "Lugar"), ("C", "Escolha manual"),
                        ("D", "Aderência da escolha"), ("E", "Sugestão automática"),
                        ("G", "Nota"), ("H", "EM USO NA SIMULAÇÃO")):
        escreve(ws, f"{col}{cab}", rotulo, tam=8.5, negrito=True, cor=BRANCO, bg=AZUL,
                alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
    ws.merge_cells(f"E{cab}:F{cab}")
    ws.merge_cells(f"H{cab}:I{cab}")
    ws.row_dimensions[cab].height = 26

    for i, L in enumerate(SLOT_LETRAS):
        r = CONS_SLOT_INI + i
        escreve(ws, f"B{r}", L, tam=11, negrito=True, cor=AZUL_ESCURO, bg=AZUL_CLARO,
                alinha=AL_CENTRO, borda=BORDA_GRADE)
        celula_input(ws, f"C{r}", None, tam=9, alinha=AL_ESQ)
        _dv(ws, BASE_PRODUTOS_REF, [f"C{r}"], "Produto",
            "Escolha um produto da base. Deixe em branco para não usar este lugar.")
        escreve(ws, f"D{r}",
                f'=IFERROR(IF($C{r}="","",INDEX({AB_ADEQUACAO}!$S${ADE_INI}:$S${ADE_FIM},'
                f'MATCH($C{r},{AB_ADEQUACAO}!$B${ADE_INI}:$B${ADE_FIM},0))),"")',
                tam=8.5, cor=COR_LINK, alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        ws.merge_cells(f"E{r}:F{r}")
        escreve(ws, f"E{r}", f"={AB_ADEQUACAO}!$B${ADE_TOP_INI + i}", tam=9,
                cor=COR_LINK, alinha=AL_ESQ, borda=BORDA_GRADE)
        escreve(ws, f"G{r}", f"={AB_ADEQUACAO}!$C${ADE_TOP_INI + i}", tam=9,
                cor=COR_LINK, fmt="0.0", alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.merge_cells(f"H{r}:I{r}")
        escreve(ws, f"H{r}",
                f'=IF(AUTO_SUGESTAO="Sim",{AB_ADEQUACAO}!$B${ADE_TOP_INI + i},$C{r})',
                tam=9.5, negrito=True, cor=AZUL_ESCURO, bg=AZUL_CLARO,
                alinha=AL_ESQ, borda=BORDA_CAIXA)
        ws.row_dimensions[r].height = 24
    ws.merge_cells("J17:K22")
    escreve(ws, "J17",
            '=IF(AUTO_SUGESTAO="Sim",'
            '"A sugestão automática está LIGADA: a coluna EM USO segue a ordem de aderência. '
            'Para escolher à mão, mude o parâmetro para Não e preencha a coluna Escolha manual.",'
            '"A sugestão automática está DESLIGADA: vale o que você escolher na coluna Escolha manual. '
            'A coluna Sugestão automática continua visível só para comparação.")',
            tam=9, cor=CINZA_TEXTO, bg=AZUL_MUITO_CLARO, alinha=AL_ESQ_WRAP,
            borda=BORDA_CAIXA)

    # ---------------- painel técnico ----------------
    secao(ws, 24, "PAINEL TÉCNICO — DE ONDE VEM CADA NÚMERO", ate_col="K")
    ws.merge_cells("B25:C25")
    escreve(ws, "B25", "Parâmetro", tam=8.5, negrito=True, cor=BRANCO, bg=AZUL_ESCURO,
            alinha=AL_ESQ, borda=BORDA_GRADE)
    for i in range(N_ALT):
        col = get_column_letter(4 + i)
        rotulo = (f'=IF({_ativo_alt(i)}=0,"({SLOT_LETRAS[i]}) não usada",{_nome_alt(i)})'
                  if i < N_SLOTS else
                  f'=IF({_ativo_alt(i)}=0,"(imóvel fora)","Imóvel para aluguel")')
        escreve(ws, f"{col}25", rotulo, tam=8, negrito=True, cor=BRANCO, bg=AZUL_ESCURO,
                alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
    ws.row_dimensions[25].height = 32

    lin = 26
    for rotulo, chave, fmt, _ in _PAINEL:
        ws.merge_cells(f"B{lin}:C{lin}")
        escreve(ws, f"B{lin}", rotulo, tam=8.5, alinha=AL_ESQ, borda=BORDA_GRADE)
        for i in range(N_ALT):
            col = get_column_letter(4 + i)
            if i < N_SLOTS:
                if chave == "Carregamento de entrada":
                    f = (f'=TEXT({_par(i,"Carregamento de entrada")},"0.00%")&" / "'
                         f'&TEXT({_par(i,"Carregamento de saída")},"0.00%")')
                    escreve(ws, f"{col}{lin}", f, tam=8, cor=COR_LINK,
                            alinha=AL_CENTRO, borda=BORDA_GRADE)
                    continue
                escreve(ws, f"{col}{lin}", f"={_par(i, chave)}", tam=8, cor=COR_LINK,
                        fmt=fmt, alinha=AL_CENTRO, borda=BORDA_GRADE)
            else:
                escreve(ws, f"{col}{lin}", _painel_imovel(chave), tam=8, cor=COR_LINK,
                        fmt=fmt if chave not in ("Regime tributário", "Garantia",
                                                 "Produto selecionado", "Categoria",
                                                 "Emissor / Gestor", "Benchmark") else None,
                        alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 14
        lin += 1

    for rotulo, formula, fmt in (
        ("Alíquota de IR no prazo escolhido", "Alíquota de IR no prazo escolhido", FMT_PCT),
        ("Imposto total pago no período", "Imposto total pago", FMT_MOEDA),
        ("Custos totais pagos no período", "Custos totais pagos", FMT_MOEDA),
        ("Patrimônio líquido no prazo", "Patrimônio líquido no prazo", FMT_MOEDA),
    ):
        ws.merge_cells(f"B{lin}:C{lin}")
        escreve(ws, f"B{lin}", rotulo, tam=8.5, negrito=True, alinha=AL_ESQ,
                borda=BORDA_GRADE, bg=AZUL_MUITO_CLARO)
        for i in range(N_ALT):
            col = get_column_letter(4 + i)
            escreve(ws, f"{col}{lin}", f"={_res(i, formula)}", tam=8, negrito=True,
                    cor=AZUL_ESCURO, fmt=fmt, alinha=AL_CENTRO, borda=BORDA_GRADE,
                    bg=AZUL_MUITO_CLARO)
        ws.row_dimensions[lin].height = 14
        lin += 1

    # procedência do dado
    for rotulo, campo in (("Status do dado", "status"), ("Atualizado em", "atualizado"),
                          ("Tipo de dado", "tipo_dado"), ("Fonte", "fonte")):
        ws.merge_cells(f"B{lin}:C{lin}")
        escreve(ws, f"B{lin}", rotulo, tam=8.5, italico=True, cor=CINZA_SUAVE,
                alinha=AL_ESQ, borda=BORDA_GRADE)
        col_prod = get_column_letter(PROD_COL[campo])
        for i in range(N_ALT):
            col = get_column_letter(4 + i)
            if i < N_SLOTS:
                f = (f'=IFERROR(INDEX({AB_PRODUTOS}!${col_prod}${PROD_LIN_INI}:'
                     f'${col_prod}${PROD_LIN_FIM},'
                     f'{AB_MOTOR}!${get_column_letter(2+i)}${MOT_P["Linha na base de produtos"]}),"—")')
            else:
                f = ('="ver aba Imóvel"' if campo != "atualizado" else "=DATA_DADOS")
            escreve(ws, f"{col}{lin}", f, tam=7.5, italico=True, cor=CINZA_SUAVE,
                    alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 16
        lin += 1

    # ---------------- alertas ----------------
    lin += 1
    secao(ws, lin, "CONFERÊNCIAS ANTES DE OFERECER", ate_col="K")
    lin += 1
    g_row = MOT_P["Garantia"]
    p_row = MOT_R["Patrimônio líquido no prazo"]
    alertas = [
        ('=IF(SUMIF(' + AB_MOTOR + f'!$B${g_row}:$G${g_row},"FGC*",'
         + AB_MOTOR + f'!$B${p_row}:$G${p_row})>LIMITE_FGC,'
         '"⚠ FGC: a soma projetada em produtos cobertos ultrapassa o limite por CPF e instituição ("'
         '&TEXT(LIMITE_FGC,"R$ #,##0")&"). Avalie distribuir entre emissores.",'
         '"✓ FGC: a soma projetada em produtos cobertos está dentro do limite.")'),
        (f'=IF(COUNTIF({AB_MOTOR}!$B${MOT_R["Atende à aplicação mínima (1/0)"]}:'
         f'$G${MOT_R["Atende à aplicação mínima (1/0)"]},0)'
         f'-COUNTIF({AB_MOTOR}!$B${MOT_P["Alternativa em uso (1/0)"]}:'
         f'$G${MOT_P["Alternativa em uso (1/0)"]},0)>0,'
         '"⚠ Aplicação mínima: alguma alternativa em uso exige mais do que o cliente tem disponível.",'
         '"✓ Aplicação mínima: todas as alternativas em uso cabem no valor disponível.")'),
        (f'=IF(COUNTIF({AB_MOTOR}!$B${MOT_R["Cabe no perfil declarado (1/0)"]}:'
         f'$G${MOT_R["Cabe no perfil declarado (1/0)"]},0)'
         f'-COUNTIF({AB_MOTOR}!$B${MOT_P["Alternativa em uso (1/0)"]}:'
         f'$G${MOT_P["Alternativa em uso (1/0)"]},0)>0,'
         '"⚠ Perfil: há alternativa em uso com risco acima do perfil declarado. '
         'Isso precisa ser tratado no processo oficial de suitability.",'
         '"✓ Perfil: nenhuma alternativa em uso ultrapassa o perfil declarado.")'),
        (f'=IF(COUNTIF({AB_PRODUTOS}!${get_column_letter(PROD_COL["status"])}${PROD_LIN_INI}:'
         f'${get_column_letter(PROD_COL["status"])}${PROD_LIN_FIM},"EXEMPLO*")>0,'
         '"⚠ Dados: há produtos na base com taxa de exemplo, ainda não conferida. '
         'Atualize antes de apresentar números ao cliente.",'
         '"✓ Dados: todos os produtos da base estão marcados como conferidos.")'),
        (f'=IF(AND(IMOV_INCLUIR="Sim",{AB_MOTOR_IMOVEL}!$B${MIM_P["Sobra (+) ou falta (−) de caixa"]}<0),'
         f'"⚠ Imóvel: faltam "&TEXT(-{AB_MOTOR_IMOVEL}!$B${MIM_P["Sobra (+) ou falta (−) de caixa"]},"R$ #,##0")'
         '&" para fechar a compra com os custos de aquisição. A comparação fica desigual enquanto isso.",'
         '"✓ Imóvel: o capital disponível cobre o valor do imóvel e os custos de aquisição.")'),
        ('=IF(AND(PGBL_COMPLETA<>"Sim",COUNTIF(' + AB_MOTOR
         + f'!$B${MOT_P["É PGBL (aporte dedutível)"]}:$G${MOT_P["É PGBL (aporte dedutível)"]},1)>0),'
         '"⚠ PGBL: há PGBL na comparação, mas o cliente não declara no modelo completo. '
         'Sem a dedução, o PGBL costuma perder para o VGBL.",'
         '"✓ PGBL: a escolha entre PGBL e VGBL está coerente com a forma de declaração informada.")'),
        (f'=IF(AND(IN_RESGATE="Sim",MAX({AB_MOTOR}!$B${MOT_P["Carência (dias)"]}:'
         f'$G${MOT_P["Carência (dias)"]})>0),'
         '"⚠ Liquidez: o cliente disse que pode precisar do dinheiro antes, mas há alternativa com carência.",'
         '"✓ Liquidez: as alternativas em uso são compatíveis com a resposta sobre resgate antecipado.")'),
    ]
    for texto in alertas:
        ws.merge_cells(f"B{lin}:K{lin}")
        escreve(ws, f"B{lin}", texto, tam=9, alinha=AL_ESQ_WRAP, borda=BORDA_GRADE)
        ws.conditional_formatting.add(
            f"B{lin}:K{lin}",
            FormulaRule(formula=[f'LEFT($B{lin},1)="⚠"'], fill=fill(AMBAR_CLARO),
                        stopIfTrue=False))
        ws.conditional_formatting.add(
            f"B{lin}:K{lin}",
            FormulaRule(formula=[f'LEFT($B{lin},1)="✓"'], fill=fill(VERDE_CLARO),
                        stopIfTrue=False))
        ws.row_dimensions[lin].height = 22
        lin += 1

    # ---------------- calculadora de curto prazo ----------------
    lin += 1
    secao(ws, lin, "RESGATE ANTES DE 30 DIAS — IOF (a projeção mensal não cobre esse caso)",
          ate_col="K")
    base = lin + 1
    curto = [
        ("Valor aplicado", 10000, FMT_MOEDA, None),
        ("Dias de aplicação", 10, FMT_INT, None),
        ("Taxa do produto (% do CDI)", 1.0, FMT_PCT, None),
    ]
    for j, (rot, val, fmt, _x) in enumerate(curto):
        ws.merge_cells(f"B{base + j}:C{base + j}")
        escreve(ws, f"B{base + j}", rot, tam=9, negrito=True, alinha=AL_ESQ)
        celula_input(ws, f"D{base + j}", val, fmt=fmt, tam=9, alinha=AL_CENTRO)
    saidas = [
        ("Rendimento bruto no período",
         f"=$D${base}*((1+CDI_CENARIO*$D${base+2})^($D${base+1}/365)-1)", FMT_MOEDA_C),
        ("IOF (% do rendimento)",
         f'=IF($D${base+1}>=30,0,IFERROR(INDEX({AB_PREMISSAS}!$B${PRE_IOF_INI}:$B${PRE_IOF_FIM},'
         f"MAX(1,$D${base+1})),0))", FMT_PCT),
        ("IOF em reais", f"=$E${base}*$E${base+1}", FMT_MOEDA_C),
        ("IR (22,5% sobre o rendimento após IOF)",
         f"=($E${base}-$E${base+2})*0.225", FMT_MOEDA_C),
        ("Valor líquido resgatado",
         f"=$D${base}+$E${base}-$E${base+2}-$E${base+3}", FMT_MOEDA_C),
    ]
    for j, (rot, f, fmt) in enumerate(saidas):
        escreve(ws, f"F{base + j}", rot, tam=9, alinha=AL_ESQ)
        ws.merge_cells(f"F{base + j}:H{base + j}")
        escreve(ws, f"E{base + j}", f, tam=9, negrito=(j == 4),
                cor=AZUL_ESCURO if j == 4 else CINZA_TEXTO,
                bg=AZUL_CLARO if j == 4 else None, fmt=fmt, alinha=AL_CENTRO,
                borda=BORDA_GRADE)
    lin = base + 6
    nota(ws, lin, "O IOF some a partir do 30º dia. O IR mostrado usa a alíquota máxima da tabela "
                  "regressiva (22,5%), que é a que vale nos primeiros 180 dias.", ate_col="K")

    lin += 2
    aviso(ws, lin, NAO_OFICIAL, ate_col="K")
    _botoes(ws, lin + 2, [(AB_INICIO, "◀ INÍCIO"), (AB_CLIENTE, "◀ CLIENTE"),
                          (AB_MESAMES, "MÊS A MÊS"), (AB_PREMISSAS, "PREMISSAS"),
                          (AB_PRODUTOS, "PRODUTOS"), (AB_FONTES, "FONTES")])
    ws.sheet_properties.tabColor = AZUL_MEDIO
    ws.sheet_view.zoomScale = 85


def _painel_imovel(chave):
    mapa = {
        "Produto selecionado": '="Imóvel para aluguel"',
        "Categoria": '="Imobiliário"',
        "Emissor / Gestor": '="Mercado"',
        "Benchmark": '="Valorização + aluguel"',
        "% do benchmark": "=1",
        "Spread a.a.": f"={AB_MOTOR_IMOVEL}!$B${MIM_P['Valorização anual do imóvel']}",
        "Retorno BRUTO a.a. (cenário)":
            f"={AB_MOTOR_IMOVEL}!$B${MIM_P['Valorização anual do imóvel']}",
        "Taxa de administração a.a.":
            f"={AB_MOTOR_IMOVEL}!$B${MIM_P['Administração imobiliária (% do aluguel)']}",
        "Custódia a.a.": f"={AB_MOTOR_IMOVEL}!$B${MIM_P['IPTU (% a.a. do valor)']}",
        "Taxa de performance": "=0",
        "Retorno LÍQUIDO a.a. estimado":
            f"={AB_MOTOR_IMOVEL}!$B${MIM_R['Taxa líquida equivalente a.a.']}",
        "Regime tributário": '="Carnê-leão + ganho de capital"',
        "Tem come-cotas (1/0)": "=0",
        "Carência (dias)": '="—"',
        "Liquidez (dias)": '="meses"',
        "Aplicação mínima": f"={AB_MOTOR_IMOVEL}!$B${MIM_P['Desembolso total na compra']}",
        "Risco (1-5)": "=3",
        "Volatilidade a.a.": "=0.07",
        "Garantia": '="Nenhuma"',
    }
    return mapa.get(chave, '="—"')


BASE_PRODUTOS_REF = f"{AB_PRODUTOS}!$B${PROD_LIN_INI}:$B${PROD_LIN_FIM}"


# ==========================================================================
# ABA MÊS A MÊS
# ==========================================================================
_MESAMES_COLS = [
    ("Mês", 7, FMT_INT), ("Data", 12, FMT_DATA), ("Saldo inicial", 16, FMT_MOEDA_C),
    ("Rendimento bruto", 16, FMT_MOEDA_C), ("Aporte", 14, FMT_MOEDA_C),
    ("Custos", 14, FMT_MOEDA_C), ("Imposto no mês", 14, FMT_MOEDA_C),
    ("Saldo final", 17, FMT_MOEDA_C), ("IR se resgatar agora", 16, FMT_MOEDA_C),
    ("Valor líquido no resgate", 18, FMT_MOEDA_C),
    ("Valor líquido em R$ de hoje", 18, FMT_MOEDA_C),
]


def construir_mesames(wb):
    ws = wb[AB_MESAMES]
    esconde_grade(ws)
    titulo_pagina(ws, "PROJEÇÃO MÊS A MÊS",
                  "Cada linha mostra exatamente de onde veio cada número", ate_col="K")

    escreve(ws, "B4", "Alternativa em exibição", tam=10, negrito=True, alinha=AL_ESQ)
    ws.merge_cells("B4:C4")
    celula_input(ws, "D4", "A", tam=11, alinha=AL_CENTRO)
    _dv(ws, _lista(SLOT_LETRAS), ["D4"])
    escreve(ws, "E4",
            f'=IFERROR(INDEX({AB_MOTOR}!$B${MOT_P["Produto selecionado"]}:'
            f'$G${MOT_P["Produto selecionado"]},$D$5),"(não escolhida)")',
            tam=12, negrito=True, cor=AZUL_ESCURO, alinha=AL_ESQ)
    ws.merge_cells("E4:H4")
    escreve(ws, "D5",
            f'=IFERROR(MATCH("ALTERNATIVA "&MES_DETALHE,'
            f'{AB_MOTOR}!$B${MOT_PAR_CAB}:$G${MOT_PAR_CAB},0),1)',
            tam=8, cor=CINZA_SUAVE, fmt=FMT_INT, alinha=AL_CENTRO)
    escreve(ws, "B5", "(número do lugar escolhido — calculado)", tam=8, cor=CINZA_SUAVE)
    ws.merge_cells("B5:C5")
    escreve(ws, "E5",
            '="O imóvel tem mecânica própria e é detalhado na aba MotorImovel, a partir da aba Imóvel."',
            tam=8.5, cor=CINZA_SUAVE, italico=True)
    ws.merge_cells("E5:K5")

    nota(ws, 6,
         "As linhas depois do prazo escolhido aparecem esmaecidas: elas mostram o que aconteceria se o "
         "cliente deixasse o dinheiro por mais tempo.", ate_col="K")

    cab = 8
    for j, (nome, larg, _f) in enumerate(_MESAMES_COLS):
        col = get_column_letter(1 + j)
        escreve(ws, f"{col}{cab}", nome, tam=8.5, negrito=True, cor=BRANCO, bg=AZUL,
                alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        ws.column_dimensions[col].width = larg
    ws.row_dimensions[cab].height = 32

    grade = (f"{AB_MOTOR}!${get_column_letter(MOT_SLOT_COL0)}${MOT_GRID_INI}:"
             f"${get_column_letter(MOT_SLOT_COL0 + (N_SLOTS - 1) * MOT_SLOT_PASSO + MOT_SLOT_LARGURA - 1)}"
             f"${MOT_GRID_FIM}")

    def ix(r, off):
        return f"INDEX({grade},$A{r}+1,($D$5-1)*{MOT_SLOT_PASSO}+{off + 1})"

    ini = cab + 1
    for m in range(MESES_MAX + 1):
        r = ini + m
        escreve(ws, f"A{r}", m, tam=8, fmt=FMT_INT, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"B{r}", f"=EDATE(DATA_INICIO,$A{r})", tam=8, fmt=FMT_DATA,
                alinha=AL_CENTRO, borda=BORDA_GRADE)
        celulas = [
            ("C", ix(r, MOT_G["saldo_ini"])),
            ("D", ix(r, MOT_G["rend_bruto"])),
            ("E", ix(r, MOT_G["aporte"])),
            ("F", f"{ix(r, MOT_G['carreg_ent'])}+{ix(r, MOT_G['taxa_adm'])}"
                  f"+{ix(r, MOT_G['taxa_perf'])}"),
            ("G", ix(r, MOT_G["come_cotas"])),
            ("H", ix(r, MOT_G["saldo_fim"])),
            ("I", ix(r, MOT_G["ir_resgate"])),
            ("J", ix(r, MOT_G["liquido"])),
            ("K", ix(r, MOT_G["liquido_real"])),
        ]
        for col, expr in celulas:
            escreve(ws, f"{col}{r}", f"=IFERROR({expr},0)", tam=8, fmt=FMT_MOEDA_C,
                    alinha=AL_DIR, borda=BORDA_GRADE,
                    negrito=col in ("H", "J"),
                    cor=AZUL_ESCURO if col == "J" else CINZA_TEXTO)
        ws.row_dimensions[r].height = 12

    fim = ini + MESES_MAX
    ws.conditional_formatting.add(
        f"A{ini}:K{fim}",
        FormulaRule(formula=[f"$A{ini}>IN_PRAZO"], font=fonte(8, cor="BFBFBF"),
                    stopIfTrue=False))
    ws.conditional_formatting.add(
        f"A{ini}:K{fim}",
        FormulaRule(formula=[f"$A{ini}=IN_PRAZO"], fill=fill(VERDE_CLARO),
                    font=fonte(8, negrito=True, cor=AZUL_ESCURO), stopIfTrue=False))
    ws.conditional_formatting.add(
        f"A{ini}:K{fim}",
        FormulaRule(formula=[f"AND($A{ini}>0,$G{ini}>0)"], fill=fill(AMBAR_CLARO),
                    stopIfTrue=False))

    escreve(ws, "M8", "Legenda", tam=9, negrito=True, cor=AZUL_ESCURO)
    for j, (cor, txt) in enumerate([
            (VERDE_CLARO, "Linha verde: o mês do prazo escolhido pelo cliente."),
            (AMBAR_CLARO, "Linha âmbar: mês em que houve come-cotas (maio e novembro)."),
            ("EFEFEF", "Linha cinza: já passou do prazo escolhido.")]):
        escreve(ws, f"M{9 + j}", txt, tam=8.5, bg=cor, alinha=AL_ESQ)
        ws.merge_cells(f"M{9 + j}:R{9 + j}")
    ws.column_dimensions["M"].width = 18

    ws.freeze_panes = f"C{ini}"
    _botoes(ws, 4, [(AB_INICIO, "◀ INÍCIO"), (AB_CLIENTE, "◀ CLIENTE"),
                    (AB_COMPARAR, "COMPARAR")], col_ini="I", largura=1)
    ws.sheet_properties.tabColor = AZUL_MEDIO


# ==========================================================================
# ABA IMÓVEL
# ==========================================================================
def construir_imovel(wb):
    ws = wb[AB_IMOVEL]
    esconde_grade(ws)
    titulo_pagina(ws, "COMPRAR UM IMÓVEL PARA ALUGAR",
                  "A estratégia do Seu João: comparar aplicação financeira com casa para alugar",
                  ate_col="K")
    larguras(ws, {"A": 2, "B": 34, "C": 16, "D": 16, "E": 16, "F": 18, "G": 16,
                  "H": 20, "I": 18, "J": 30, "K": 30, "L": 2})

    secao(ws, 4, "1 · A COMPRA", ate_col="K")
    _pergunta(ws, 5, "Incluir o imóvel na comparação?", altura=20)
    celula_input(ws, "F5", "Sim", alinha=AL_CENTRO)
    _dv(ws, _lista(D.SIM_NAO), ["F5"])
    _pergunta(ws, 6, "Valor do imóvel", altura=20)
    celula_input(ws, "F6", 150000, fmt=FMT_MOEDA, alinha=AL_CENTRO)
    _pergunta(ws, 7, "ITBI (% do valor)", altura=18)
    celula_input(ws, "F7", 0.02, fmt=FMT_PCT, alinha=AL_CENTRO)
    _pergunta(ws, 8, "Escritura e registro (% do valor)", altura=18)
    celula_input(ws, "F8", 0.015, fmt=FMT_PCT, alinha=AL_CENTRO)
    _derivado(ws, 9, "➜ Desembolso total para fechar a compra",
              "=IMOV_VALOR*(1+IMOV_ITBI+IMOV_CARTORIO)", fmt=FMT_MOEDA)
    ws.merge_cells("B10:K10")
    escreve(ws, "B10",
            f'=IF({AB_MOTOR_IMOVEL}!$B${MIM_P["Sobra (+) ou falta (−) de caixa"]}<0,'
            f'"⚠ O cliente tem "&TEXT(IN_CAPITAL,"R$ #,##0")&" e a compra exige "'
            f'&TEXT(IMOV_DESEMBOLSO,"R$ #,##0")&". Faltam "'
            f'&TEXT(-{AB_MOTOR_IMOVEL}!$B${MIM_P["Sobra (+) ou falta (−) de caixa"]},"R$ #,##0")'
            f'&" — quase ninguém lembra dos custos de aquisição, e eles mudam a conta.",'
            f'"✓ O capital disponível cobre o imóvel e os custos de aquisição. A sobra de "'
            f'&TEXT({AB_MOTOR_IMOVEL}!$B${MIM_P["Sobra (+) ou falta (−) de caixa"]},"R$ #,##0")'
            f'&" entra na simulação como caixa aplicado.")',
            tam=9.5, negrito=True, alinha=AL_ESQ_WRAP, borda=BORDA_GRADE)
    ws.row_dimensions[10].height = 30
    ws.conditional_formatting.add("B10:K10", FormulaRule(
        formula=['LEFT($B$10,1)="⚠"'], fill=fill(AMBAR_CLARO), stopIfTrue=False))
    ws.conditional_formatting.add("B10:K10", FormulaRule(
        formula=['LEFT($B$10,1)="✓"'], fill=fill(VERDE_CLARO), stopIfTrue=False))

    secao(ws, 11, "2 · O ALUGUEL", ate_col="K")
    _pergunta(ws, 12, "Como definir o aluguel?", altura=20)
    celula_input(ws, "F12", "Informar o valor do aluguel", alinha=AL_CENTRO)
    _dv(ws, _lista(["Informar o valor do aluguel", "Usar o yield da aba Premissas"]), ["F12"])
    _pergunta(ws, 13, "Aluguel mensal, se você informar o valor", altura=18)
    celula_input(ws, "F13", 900, fmt=FMT_MOEDA, alinha=AL_CENTRO)
    _derivado(ws, 14, "➜ Aluguel usado na simulação",
              f"={AB_MOTOR_IMOVEL}!$B${MIM_P['Aluguel mensal inicial']}", fmt=FMT_MOEDA)
    _pergunta(ws, 15, "Vacância — quanto do ano o imóvel fica sem inquilino", altura=20)
    celula_input(ws, "F15", 0.08, fmt=FMT_PCT, alinha=AL_CENTRO)
    ws.merge_cells("H15:K15")
    escreve(ws, "H15",
            "8% equivale a cerca de um mês por ano vazio. Ignorar a vacância é o erro mais comum.",
            tam=8.5, cor=CINZA_SUAVE, italico=True, alinha=AL_ESQ_WRAP)
    _pergunta(ws, 16, "Reajuste anual do aluguel", altura=18)
    celula_input(ws, "F16", "=IPCA_CENARIO", fmt=FMT_PCT, alinha=AL_CENTRO)
    escreve(ws, "H16", '="Padrão: o IPCA do cenário ("&TEXT(IPCA_CENARIO,"0.0%")&" a.a.)."',
            tam=8.5, cor=CINZA_SUAVE, italico=True)
    ws.merge_cells("H16:K16")

    secao(ws, 18, "3 · O CUSTO DE MANTER", ate_col="K")
    _pergunta(ws, 19, "IPTU (% do valor do imóvel por ano)", altura=18)
    celula_input(ws, "F19", 0.006, fmt=FMT_PCT, alinha=AL_CENTRO)
    _pergunta(ws, 20, "Manutenção e seguro (% do valor por ano)", altura=18)
    celula_input(ws, "F20", 0.010, fmt=FMT_PCT, alinha=AL_CENTRO)
    _pergunta(ws, 21, "Administração imobiliária (% do aluguel)", altura=18)
    celula_input(ws, "F21", 0.08, fmt=FMT_PCT, alinha=AL_CENTRO)
    escreve(ws, "H19",
            "IPTU e taxa de administração são dedutíveis no carnê-leão; manutenção não é. "
            "A planilha já trata os três de forma diferente.",
            tam=8.5, cor=CINZA_SUAVE, italico=True, alinha=AL_ESQ_WRAP)
    ws.merge_cells("H19:K21")

    secao(ws, 23, "4 · A VENDA NO FIM DO PRAZO", ate_col="K")
    _pergunta(ws, 24, "Valorização anual do imóvel", altura=18)
    celula_input(ws, "F24",
                 '=IFERROR(INDEX(TAB_MACRO_VAL,MATCH("IMOB_VAL",TAB_MACRO_COD,0)),0.04)',
                 fmt=FMT_PCT, alinha=AL_CENTRO)
    _pergunta(ws, 25, "Corretagem na venda (%)", altura=18)
    celula_input(ws, "F25", 0.06, fmt=FMT_PCT, alinha=AL_CENTRO)
    _pergunta(ws, 26, "Tem isenção de imposto sobre o ganho na venda?", altura=20)
    celula_input(ws, "F26", "Não", alinha=AL_CENTRO)
    _dv(ws, _lista(D.SIM_NAO), ["F26"])
    escreve(ws, "H24",
            "Há regras específicas de isenção — imóvel único de menor valor vendido a cada cinco anos, "
            "e compra de outro imóvel residencial em até 180 dias. Confirme o enquadramento antes de "
            "marcar Sim: essa escolha muda bastante o resultado final.",
            tam=8.5, cor=CINZA_SUAVE, italico=True, alinha=AL_ESQ_WRAP)
    ws.merge_cells("H24:K26")

    secao(ws, 28, "5 · O QUE O CLIENTE FAZ COM O ALUGUEL", ate_col="K")
    _pergunta(ws, 29, "O aluguel vai ser reinvestido ou gasto?", altura=22)
    celula_input(ws, "F29", "Reinvestir", alinha=AL_CENTRO)
    _dv(ws, _lista(D.DESTINO_ALUGUEL), ["F29"])
    _pergunta(ws, 30, "Se reinvestir, a que taxa ao ano?", altura=18)
    celula_input(ws, "F30", "=CDI_CENARIO*0.98", fmt=FMT_PCT, alinha=AL_CENTRO)
    ws.merge_cells("H29:K30")
    escreve(ws, "H29",
            f'=IF(IMOV_DESTINO="Reinvestir",'
            f'"O aluguel líquido é aplicado todo mês e volta a render. O patrimônio final fica maior, '
            f'mas o cliente não usa esse dinheiro no dia a dia.",'
            f'"O aluguel é gasto: hoje isso vira cerca de "'
            f'&TEXT({AB_MOTOR_IMOVEL}!$B${MIM_R["Renda mensal potencial (nominal)"]},"R$ #,##0")'
            f'&" por mês no bolso, e o patrimônio cresce só pela valorização do imóvel.")',
            tam=9, cor=CINZA_TEXTO, bg=AZUL_MUITO_CLARO, alinha=AL_ESQ_WRAP,
            borda=BORDA_CAIXA)

    secao(ws, 32, "RESULTADO DA ESTRATÉGIA IMOBILIÁRIA", ate_col="K")
    resultados = [
        ("Patrimônio líquido no fim do prazo (vendendo o imóvel)", "Patrimônio líquido no prazo", FMT_MOEDA),
        ("Em poder de compra de hoje", "Patrimônio líquido em R$ de hoje", FMT_MOEDA),
        ("Total investido pelo cliente", "Total investido (capital + aportes)", FMT_MOEDA),
        ("Ganho líquido", "Ganho líquido", FMT_MOEDA),
        ("Impostos pagos (aluguel + caixa + ganho de capital)", "Imposto total pago", FMT_MOEDA),
        ("Custos pagos (aquisição, IPTU, manutenção, administração, vacância, corretagem)",
         "Custos totais pagos", FMT_MOEDA),
        ("Rentabilidade líquida acumulada", "Rentabilidade líquida acumulada", FMT_PCT),
        ("Taxa líquida equivalente a.a.", "Taxa líquida equivalente a.a.", FMT_PCT),
        ("Ganho real a.a. (acima da inflação)", "Ganho real a.a. (acima da inflação)", FMT_PCT),
        ("Aluguel líquido no último mês do prazo", "Renda mensal potencial (nominal)", FMT_MOEDA),
    ]
    for j, (rot, chave, fmt) in enumerate(resultados):
        lin = 33 + j
        ws.merge_cells(f"B{lin}:E{lin}")
        escreve(ws, f"B{lin}", rot, tam=9.5, alinha=AL_ESQ_WRAP,
                negrito=j == 0, borda=BORDA_GRADE)
        ws.merge_cells(f"F{lin}:G{lin}")
        escreve(ws, f"F{lin}", f"={AB_MOTOR_IMOVEL}!$B${MIM_R[chave]}", tam=11 if j == 0 else 10,
                negrito=True, cor=AZUL_ESCURO, bg=AZUL_CLARO if j == 0 else None,
                fmt=fmt, alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 18

    ws.merge_cells("H33:K42")
    escreve(ws, "H33",
            f'="Comparando com a melhor alternativa financeira em uso: "'
            f'&TEXT(MAX({AB_MOTOR}!$B${MOT_R["Patrimônio líquido no prazo"]}:'
            f'$G${MOT_R["Patrimônio líquido no prazo"]}),"R$ #,##0")&". "'
            f'&IF({AB_MOTOR_IMOVEL}!$B${MIM_R["Patrimônio líquido no prazo"]}'
            f'>MAX({AB_MOTOR}!$B${MOT_R["Patrimônio líquido no prazo"]}:'
            f'$G${MOT_R["Patrimônio líquido no prazo"]}),'
            f'"Nestas premissas o imóvel termina à frente — mas lembre que ele não tem liquidez, '
            f'depende de inquilino e concentra todo o patrimônio em um único bem.",'
            f'"Nestas premissas a aplicação financeira termina à frente. Ainda assim, o imóvel pode '
            f'fazer sentido por outros motivos: uso próprio, herança, segurança percebida.")',
            tam=9, cor=CINZA_TEXTO, bg=AZUL_MUITO_CLARO, alinha=AL_ESQ_WRAP,
            borda=BORDA_CAIXA)

    aviso(ws, 44,
          "O imóvel é o único item da comparação que não é dinheiro. Ele não se divide, não se resgata em "
          "parte e depende de achar comprador. Isso não aparece em nenhum número — mas precisa aparecer na conversa.",
          ate_col="K")
    _botoes(ws, 46, [(AB_INICIO, "◀ INÍCIO"), (AB_CLIENTE, "◀ CLIENTE"),
                     (AB_COMPARAR, "COMPARAR"),
                     (AB_MOTOR_IMOVEL, "VER MÊS A MÊS DO IMÓVEL"),
                     (AB_PREMISSAS, "PREMISSAS")])
    ws.sheet_properties.tabColor = AZUL_MEDIO


# ==========================================================================
# ABA PREVIDÊNCIA
# ==========================================================================
def construir_previdencia(wb):
    ws = wb[AB_PREV]
    esconde_grade(ws)
    titulo_pagina(ws, "PREVIDÊNCIA PRIVADA",
                  "PGBL ou VGBL, progressivo ou regressivo — e quanto vale, em reais, o benefício fiscal",
                  ate_col="K")
    larguras(ws, {"A": 2, "B": 40, "C": 18, "D": 18, "E": 18, "F": 18, "G": 18,
                  "H": 18, "I": 18, "J": 26, "K": 26, "L": 2})

    secao(ws, 4, "1 · ESTE CLIENTE PODE APROVEITAR O PGBL?", ate_col="K")
    checks = [
        ("Declara o Imposto de Renda no modelo completo?", "=PGBL_COMPLETA"),
        ("Tem renda bruta anual tributável informada?",
         '=IF(PGBL_RENDA>0,"Sim","Não informada")'),
        ("Limite de dedução (12% da renda bruta anual)", "=PGBL_RENDA*LIMITE_PGBL"),
        ("Aporte anual previsto em previdência", "=IN_APORTE*12"),
        ("Parcela do aporte que pode ser deduzida",
         "=MIN(IN_APORTE*12,PGBL_RENDA*LIMITE_PGBL)"),
    ]
    for j, (rot, f) in enumerate(checks):
        lin = 5 + j
        ws.merge_cells(f"B{lin}:D{lin}")
        escreve(ws, f"B{lin}", rot, tam=9.5, alinha=AL_ESQ_WRAP, borda=BORDA_GRADE)
        escreve(ws, f"E{lin}", f, tam=10, negrito=True, cor=AZUL_ESCURO,
                fmt=FMT_MOEDA if j >= 2 else None, alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 18
    ws.merge_cells("F5:K9")
    escreve(ws, "F5",
            '=IF(PGBL_COMPLETA<>"Sim",'
            '"VEREDITO: o PGBL não faz sentido aqui. Ele só entrega vantagem para quem declara no modelo '
            'completo e tem imposto a deduzir. Para quem declara simplificado ou é isento, o VGBL é o caminho, '
            'porque cobra imposto apenas sobre o rendimento.",'
            'IF(PGBL_RENDA<=0,'
            '"VEREDITO: informe a renda bruta anual tributável na aba Consultor para calcular o benefício.",'
            '"VEREDITO: o PGBL faz sentido. O cliente pode deduzir "'
            '&TEXT(MIN(IN_APORTE*12,PGBL_RENDA*LIMITE_PGBL),"R$ #,##0")&" por ano, o que devolve cerca de "'
            '&TEXT(PGBL_BENEFICIO,"R$ #,##0")&" na declaração. Atenção: na saída o imposto incide sobre o '
            'VALOR TOTAL resgatado, não só sobre o rendimento — o benefício é um adiantamento, não um perdão."))',
            tam=9.5, negrito=True, cor=AZUL_ESCURO, bg=AZUL_MUITO_CLARO,
            alinha=AL_ESQ_WRAP, borda=BORDA_CAIXA)

    secao(ws, 11, "2 · QUANTO VALE O BENEFÍCIO FISCAL AO LONGO DO TEMPO", ate_col="K")
    beneficios = [
        ("Benefício fiscal por ano", "=PGBL_BENEFICIO", FMT_MOEDA),
        ("Benefício ao longo de todo o prazo", "=PGBL_BENEFICIO*IN_PRAZO/12", FMT_MOEDA),
        ("Se reinvestido a cada ano, vira aproximadamente",
         '=IF(PGBL_REINVESTE<>"Sim",0,IF(CDI_CENARIO=0,PGBL_BENEFICIO*IN_PRAZO/12,'
         'PGBL_BENEFICIO*((1+CDI_CENARIO)^(IN_PRAZO/12)-1)/CDI_CENARIO))', FMT_MOEDA),
        ("O benefício está sendo reinvestido na simulação?", "=PGBL_REINVESTE", None),
    ]
    for j, (rot, f, fmt) in enumerate(beneficios):
        lin = 12 + j
        ws.merge_cells(f"B{lin}:D{lin}")
        escreve(ws, f"B{lin}", rot, tam=9.5, alinha=AL_ESQ_WRAP, borda=BORDA_GRADE)
        escreve(ws, f"E{lin}", f, tam=10, negrito=True, cor=VERDE, bg=VERDE_CLARO,
                fmt=fmt, alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 18
    ws.merge_cells("F12:K15")
    escreve(ws, "F12",
            "A maior parte das simulações de previdência ignora o benefício fiscal ou finge que ele "
            "some. Aqui ele tem dois caminhos, escolhidos na aba Consultor: consumido (aparece como "
            "dinheiro no bolso) ou reinvestido (volta como aporte extra em maio de cada ano e passa "
            "a compor). A diferença entre os dois caminhos costuma ser a parte mais convincente da conversa.",
            tam=9, cor=CINZA_TEXTO, bg=AZUL_MUITO_CLARO, alinha=AL_ESQ_WRAP, borda=BORDA_CAIXA)

    secao(ws, 17, "3 · REGIME PROGRESSIVO OU REGRESSIVO?", ate_col="K")
    cabecalho_tabela(ws, 18, 2,
                     ["Tempo de aplicação", "Regressivo", "Progressivo (retido na fonte)",
                      "Qual tende a ser melhor", "Observação"],
                     larguras=[40, 18, 18, 18, 40], altura=26)
    faixas = [("Até 2 anos", 0), ("De 2 a 4 anos", 721), ("De 4 a 6 anos", 1441),
              ("De 6 a 8 anos", 2161), ("De 8 a 10 anos", 2881), ("Acima de 10 anos", 3601)]
    for j, (rot, dias) in enumerate(faixas):
        lin = 19 + j
        escreve(ws, f"B{lin}", rot, tam=9, borda=BORDA_GRADE)
        escreve(ws, f"C{lin}",
                f'=INDEX(TAB_IR,MATCH({dias},TAB_IR_DIAS,1),MATCH("PREV_REGR",TAB_IR_REGIMES,0))',
                tam=9, negrito=True, fmt=FMT_PCT, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"D{lin}",
                f'=INDEX(TAB_IR,MATCH({dias},TAB_IR_DIAS,1),MATCH("PREV_PROG",TAB_IR_REGIMES,0))',
                tam=9, fmt=FMT_PCT, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"E{lin}", f'=IF($C{lin}<$D{lin},"Regressivo",IF($C{lin}=$D{lin},"Empate","Progressivo"))',
                tam=9, negrito=True, cor=AZUL_ESCURO, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"F{lin}",
                ("Resgate cedo no regressivo é caro: 35%." if j == 0 else
                 "O progressivo faz o acerto na declaração: pode sobrar ou faltar imposto." if j == 1 else
                 "A partir daqui o regressivo vai ficando mais barato." if j < 5 else
                 "Alíquota mínima de 10%: é aqui que a previdência de longo prazo brilha."),
                tam=8.5, cor=CINZA_SUAVE, alinha=AL_ESQ_WRAP, borda=BORDA_GRADE)
        ws.merge_cells(f"F{lin}:K{lin}")
        ws.row_dimensions[lin].height = 16
    ws.merge_cells("B26:K26")
    escreve(ws, "B26",
            '="No prazo escolhido ("&IN_PRAZO&" meses), o regime regressivo cobraria "'
            '&TEXT(INDEX(TAB_IR,MATCH(IN_PRAZO*30,TAB_IR_DIAS,1),MATCH("PREV_REGR",TAB_IR_REGIMES,0)),"0.0%")'
            '&" e o progressivo, "'
            '&TEXT(INDEX(TAB_IR,MATCH(IN_PRAZO*30,TAB_IR_DIAS,1),MATCH("PREV_PROG",TAB_IR_REGIMES,0)),"0.0%")'
            '&" na fonte. O progressivo só ganha quando a renda futura do cliente for baixa ou isenta — '
            'porque aí o acerto na declaração devolve imposto."',
            tam=9.5, negrito=True, cor=AZUL_ESCURO, bg=AZUL_MUITO_CLARO,
            alinha=AL_ESQ_WRAP, borda=BORDA_CAIXA)
    ws.row_dimensions[26].height = 32

    secao(ws, 28, "4 · OS PLANOS QUE ESTÃO NA COMPARAÇÃO", ate_col="K")
    nota(ws, 29,
         "Para comparar PGBL e VGBL lado a lado, coloque um em cada lugar na aba Consultor "
         "(com a sugestão automática desligada). As colunas abaixo mostram só os lugares ocupados por previdência.",
         ate_col="K", altura=22)
    cabecalho_tabela(ws, 30, 2,
                     ["Plano", "Tipo", "Regime", "Taxa adm.", "Carregamento",
                      "Patrimônio líquido", "IR no resgate", "Renda mensal"],
                     larguras=[40, 18, 18, 18, 18, 18, 18, 18], altura=26)
    for i in range(N_SLOTS):
        lin = 31 + i
        col = get_column_letter(2 + i)
        eh_prev = f'ISNUMBER(SEARCH("PREV",{_par(i,"Regime tributário")}))'
        escreve(ws, f"B{lin}", f'=IF({eh_prev},{_par(i,"Produto selecionado")},"—")',
                tam=9, negrito=True, borda=BORDA_GRADE)
        escreve(ws, f"C{lin}",
                f'=IF({eh_prev},IF({_par(i,"Base tributável (1=rend. / 2=total)")}=2,'
                '"PGBL (IR sobre o total)","VGBL (IR só sobre o rendimento)"),"")',
                tam=8.5, alinha=AL_CENTRO_WRAP, borda=BORDA_GRADE)
        escreve(ws, f"D{lin}", f'=IF({eh_prev},{_par(i,"Regime tributário")},"")',
                tam=8.5, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"E{lin}", f'=IF({eh_prev},{_par(i,"Taxa de administração a.a.")},"")',
                tam=8.5, fmt=FMT_PCT2, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"F{lin}", f'=IF({eh_prev},{_par(i,"Carregamento de entrada")},"")',
                tam=8.5, fmt=FMT_PCT2, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"G{lin}", f'=IF({eh_prev},{_res(i,"Patrimônio líquido no prazo")},"")',
                tam=9, negrito=True, cor=AZUL_ESCURO, fmt=FMT_MOEDA, alinha=AL_CENTRO,
                borda=BORDA_GRADE)
        escreve(ws, f"H{lin}", f'=IF({eh_prev},{_res(i,"Imposto total pago")},"")',
                tam=8.5, fmt=FMT_MOEDA, alinha=AL_CENTRO, borda=BORDA_GRADE)
        escreve(ws, f"I{lin}", f'=IF({eh_prev},{_res(i,"Renda mensal potencial (nominal)")},"")',
                tam=8.5, fmt=FMT_MOEDA, alinha=AL_CENTRO, borda=BORDA_GRADE)
        ws.row_dimensions[lin].height = 20

    secao(ws, 38, "5 · A RENDA QUE ESSE PATRIMÔNIO PODE GERAR", ate_col="K")
    nota(ws, 39,
         "Renda mensal estimada mantendo o patrimônio de pé — ou seja, vivendo do rendimento, sem consumir "
         "o principal. A segunda linha desconta a inflação: é o que o cliente realmente conseguirá comprar.",
         ate_col="K", altura=22)
    for j, (rot, chave) in enumerate([
            ("Renda mensal em reais do futuro", "Renda mensal potencial (nominal)"),
            ("Renda mensal em poder de compra de hoje", "Renda mensal potencial (poder de compra)")]):
        lin = 40 + j
        ws.merge_cells(f"B{lin}:C{lin}")
        escreve(ws, f"B{lin}", rot, tam=9.5, negrito=j == 1, alinha=AL_ESQ_WRAP,
                borda=BORDA_GRADE)
        for i in range(N_SLOTS):
            escreve(ws, f"{get_column_letter(4 + i)}{lin}",
                    f'=IF({_ativo_alt(i)}=0,"",{_res(i, chave)})',
                    tam=9, fmt=FMT_MOEDA, alinha=AL_CENTRO, borda=BORDA_GRADE,
                    negrito=j == 1, cor=AZUL_ESCURO if j == 1 else CINZA_TEXTO)
        ws.row_dimensions[lin].height = 18

    aviso(ws, 43,
          "Previdência não tem cobertura do FGC: quem responde é a seguradora. Em compensação, o saldo não "
          "entra em inventário e vai direto para os beneficiários indicados — para muita gente esse é o "
          "motivo principal, e não a rentabilidade.", ate_col="K")
    _botoes(ws, 45, [(AB_INICIO, "◀ INÍCIO"), (AB_CONSULTOR, "◀ CONSULTOR"),
                     (AB_COMPARAR, "COMPARAR"), (AB_GLOSSARIO, "GLOSSÁRIO")])
    ws.sheet_properties.tabColor = AZUL_MEDIO


# ==========================================================================
# ABA RELATÓRIO
# ==========================================================================
def construir_relatorio(wb):
    ws = wb[AB_RELATORIO]
    esconde_grade(ws)
    larguras(ws, {"A": 2, "B": 30, "C": 17, "D": 17, "E": 15, "F": 15, "G": 17,
                  "H": 20, "I": 2})

    ws.merge_cells("A1:H2")
    escreve(ws, "A1", "   RESUMO DA SUA SIMULAÇÃO", tam=18, negrito=True, cor=BRANCO,
            bg=AZUL_ESCURO, alinha=AL_ESQ)
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 12

    ws.merge_cells("A3:H3")
    escreve(ws, "A3",
            '="  Cliente: "&IN_NOME&"          Simulação feita em: "&TEXT(IN_DATA_SIM,"dd/mm/yyyy")'
            '&"          Dados de: "&DATA_DADOS',
            tam=9.5, cor=BRANCO, bg=AZUL, alinha=AL_ESQ)
    ws.row_dimensions[3].height = 18

    secao(ws, 5, "O QUE FOI CONSIDERADO", ate_col="H")
    premissas = [
        ("Valor investido hoje", "=IN_CAPITAL", FMT_MOEDA),
        ("Aporte mensal", "=IN_APORTE", FMT_MOEDA),
        ("Prazo", '=IN_PRAZO&" meses ("&ROUND(IN_PRAZO/12,1)&" anos)"', None),
        ("Pode precisar retirar antes", "=IN_RESGATE", None),
        ("O que é mais importante", "=IN_PRIORIDADE", None),
        ("Perfil de investidor", "=IN_PERFIL", None),
        ("Cenário de premissas", "=CENARIO", None),
        ("Inflação considerada (a.a.)", "=IPCA_CENARIO", FMT_PCT),
    ]
    for j, (rot, f, fmt) in enumerate(premissas):
        lin = 6 + j // 2
        col_r, col_v = ("B", "C") if j % 2 == 0 else ("E", "G")
        if j % 2 == 0:
            ws.merge_cells(f"C{lin}:D{lin}")
        else:
            ws.merge_cells(f"E{lin}:F{lin}")
            ws.merge_cells(f"G{lin}:H{lin}")
        escreve(ws, f"{col_r}{lin}", rot, tam=9, alinha=AL_ESQ, borda=BORDA_BASE)
        escreve(ws, f"{col_v}{lin}", f, tam=9.5, negrito=True, cor=AZUL_ESCURO,
                fmt=fmt, alinha=AL_ESQ, borda=BORDA_BASE)
        ws.row_dimensions[lin].height = 16

    secao(ws, 11, "AS ALTERNATIVAS ANALISADAS", ate_col="H")
    cabecalho_tabela(ws, 12, 2,
                     ["Alternativa", "Você teria cerca de", "Em R$ de hoje",
                      "Ganho estimado", "Renda mensal", "Para retirar", "Oscilação"],
                     larguras=[30, 17, 17, 15, 15, 17, 20], altura=28)
    for i in range(N_ALT):
        lin = 13 + i
        ativo = _ativo_alt(i)
        nome = (_nome_alt(i) if i < N_SLOTS else '"Imóvel para aluguel"')
        campos = [
            ("B", f'=IF({ativo}=0,"",{nome})', None, AL_ESQ),
            ("C", f'=IF({ativo}=0,"",{_res(i,"Patrimônio líquido no prazo")})', FMT_MOEDA, AL_CENTRO),
            ("D", f'=IF({ativo}=0,"",{_res(i,"Patrimônio líquido em R$ de hoje")})', FMT_MOEDA, AL_CENTRO),
            ("E", f'=IF({ativo}=0,"",{_res(i,"Ganho líquido")})', FMT_MOEDA, AL_CENTRO),
            ("F", f'=IF({ativo}=0,"",{_res(i,"Renda mensal potencial (nominal)")})', FMT_MOEDA, AL_CENTRO),
            ("G", f'=IF({ativo}=0,"",{_res(i,"Para retirar (linguagem de cliente)")})', None, AL_CENTRO_WRAP),
            ("H", f'=IF({ativo}=0,"",{_res(i,"Oscilação (linguagem de cliente)")})', None, AL_CENTRO),
        ]
        bg = BRANCO if i % 2 == 0 else CINZA_FUNDO
        for col, f, fmt, alin in campos:
            escreve(ws, f"{col}{lin}", f, tam=9, bg=bg, fmt=fmt, alinha=alin,
                    borda=BORDA_GRADE, negrito=col in ("B", "C"),
                    cor=AZUL_ESCURO if col == "C" else CINZA_TEXTO)
        ws.row_dimensions[lin].height = 22

    secao(ws, 21, "O QUE MUDA DE UMA PARA A OUTRA", ate_col="H")
    aux = f"{AB_COMPARAR}!$Q${COMP_INI}:$Q${COMP_FIM}"
    ws.merge_cells("B22:H24")
    escreve(ws, "B22",
            f'=IF(COUNT({aux})<2,'
            '"Há apenas uma alternativa na comparação. Coloque outras na aba Consultor para o cliente '
            'enxergar a diferença entre os caminhos possíveis.",'
            '"Entre a alternativa que termina com mais patrimônio e a que termina com menos há uma diferença de "'
            f'&TEXT(MAX({aux})-MIN({aux}),"R$ #,##0")'
            '&". Esse número, sozinho, não decide nada: uma alternativa que rende um pouco menos, mas permite '
            'retirar o dinheiro quando for preciso, pode ser a escolha certa. O contrário também vale — '
            'travar o dinheiro por mais tempo costuma vir junto com uma taxa melhor e menos imposto.")',
            tam=9.5, cor=CINZA_TEXTO, bg=AZUL_MUITO_CLARO, alinha=AL_ESQ_WRAP,
            borda=BORDA_CAIXA)

    secao(ws, 26, "COMO O PATRIMÔNIO PODE EVOLUIR", ate_col="H")

    secao(ws, 46, "AVISOS IMPORTANTES", ate_col="H")
    textos = [
        DISCLAIMER,
        NAO_OFICIAL,
        "Rentabilidade passada não é garantia de rentabilidade futura. Os cenários são premissas escolhidas "
        "pelo profissional para mostrar uma faixa de resultados possíveis — não são previsão nem promessa.",
        "Os valores de imposto e de custos são estimativas calculadas com as regras registradas na planilha "
        "na data indicada. Mudanças de legislação alteram o resultado.",
        "Produtos de renda variável e fundos podem apresentar rentabilidade negativa. A oscilação indicada "
        "descreve o comportamento esperado, não um limite de perda.",
    ]
    for j, t in enumerate(textos):
        lin = 47 + j
        ws.merge_cells(f"B{lin}:H{lin}")
        escreve(ws, f"B{lin}", "•  " + t, tam=8, cor=CINZA_SUAVE, alinha=AL_ESQ_WRAP)
        ws.row_dimensions[lin].height = 22

    ws.merge_cells("B53:H53")
    escreve(ws, "B53",
            '="Documento gerado em "&TEXT(TODAY(),"dd/mm/yyyy")&" a partir das premissas registradas nesta '
            'planilha. Fontes e datas de atualização de cada dado estão registradas na aba Fontes."',
            tam=8, italico=True, cor=CINZA_SUAVE, alinha=AL_ESQ_WRAP)

    # gráfico do relatório
    ws_comp = wb[AB_COMPARAR]
    g = LineChart()
    g.title = "Evolução estimada do patrimônio (R$)"
    g.width, g.height = 19, 9
    g.style = 2
    g.add_data(Reference(ws_comp, min_col=2, min_row=ANO_CAB, max_col=1 + N_ALT,
                         max_row=ANO_FIM), titles_from_data=True)
    g.set_categories(Reference(ws_comp, min_col=1, min_row=ANO_INI, max_row=ANO_FIM))
    g.x_axis.title = "Anos"
    g.y_axis.numFmt = "#,##0"
    g.dispBlanksAs = "gap"
    for s in g.series:
        s.smooth = False
    ws.add_chart(g, "B27")

    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.4
    ws.print_area = "A1:H54"

    _botoes(ws, 56, [(AB_INICIO, "◀ INÍCIO"), (AB_CLIENTE, "◀ CLIENTE"),
                     (AB_COMPARAR, "COMPARAR")])
    nota(ws, 57,
         "Para entregar ao cliente: Arquivo ▸ Exportar / Salvar como PDF. A área de impressão já está "
         "configurada em uma página A4.", ate_col="H")
    ws.sheet_properties.tabColor = AZUL
