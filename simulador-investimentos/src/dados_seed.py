"""
SEMENTE DA BASE DE DADOS — camada de DADOS, separada de cálculo e interface.

Tudo aqui é PARÂMETRO, não fórmula. Alterar um número neste arquivo (ou
diretamente na aba `Produtos` / `Premissas` da planilha) NÃO exige mexer em
nenhuma fórmula do motor.

⚠ IMPORTANTE
Os valores abaixo são de REFERÊNCIA / EXEMPLO, para que a ferramenta nasça
funcionando. Nenhum deles é cotação oficial. Antes de usar em atendimento:
  1. rode `scripts/atualizar_dados.py` (busca Selic/CDI/IPCA/TR no Banco Central); e
  2. confira produto a produto nas fontes oficiais (lâmina, regulamento,
     tabela de taxas vigente), marcando a coluna STATUS como VERIFICADO.
"""

DATA_REFERENCIA = "2026-08-23"
_EX = "EXEMPLO — VERIFICAR"

# ==========================================================================
# 1) INDICADORES MACROECONÔMICOS POR CENÁRIO
#    (código, nome, conservador, base, otimista, composição, fonte, tipo)
#    Composição: SOMA  -> taxa = base*%benchmark + spread
#                MULT  -> taxa = (1 + base*%benchmark) * (1 + spread) - 1
# ==========================================================================
MACRO = [
    ("SELIC", "Taxa Selic (meta)", 0.0800, 0.1100, 0.1300, "SOMA",
     "Banco Central — SGS série 432", "Diário (D+1)"),
    ("CDI", "CDI acumulado", None, None, None, "SOMA",
     "Banco Central — SGS série 4389", "Diário (D+1)"),          # fórmula = Selic - 0,10 p.p.
    ("IPCA", "IPCA (inflação)", 0.0550, 0.0400, 0.0350, "MULT",
     "IBGE via BCB — SGS série 433", "Mensal (com defasagem)"),
    ("TR", "Taxa Referencial", 0.0050, 0.0100, 0.0160, "SOMA",
     "Banco Central — SGS série 226", "Mensal"),
    ("POUP", "Poupança (regra vigente)", None, None, None, "SOMA",
     "Lei 12.703/2012 — calculado a partir da Selic e da TR", "Calculado"),
    ("PRE", "Prefixado (base zero)", 0.0, 0.0, 0.0, "SOMA",
     "A taxa do prefixado vem do campo Spread do produto", "Cadastral"),
    ("IBOV", "Bolsa / Ibovespa", 0.0400, 0.1000, 0.1600, "SOMA",
     "Premissa do consultor — B3 (histórico)", "Premissa"),
    ("CAMBIO", "Dólar", 0.0200, 0.0400, 0.0800, "SOMA",
     "Premissa do consultor — BCB PTAX (histórico)", "Premissa"),
    ("IMOB_VAL", "Valorização imobiliária", 0.0200, 0.0400, 0.0700, "SOMA",
     "Premissa do consultor — Índice FipeZAP (histórico)", "Mensal (com defasagem)"),
    ("IMOB_YLD", "Aluguel bruto (% do valor/ano)", 0.0500, 0.0600, 0.0700, "SOMA",
     "Premissa do consultor — FipeZAP aluguel (histórico)", "Mensal (com defasagem)"),
]

# ==========================================================================
# 2) TABELA DE IMPOSTO DE RENDA — alíquota no resgate por regime e prazo
#    Linhas = dias corridos MÍNIMOS da faixa (ordem crescente, obrigatório).
# ==========================================================================
REGIMES = ["ISENTO", "RF_REGR", "FUNDO_CP", "FUNDO_LP",
           "FUNDO_ACOES", "PREV_REGR", "PREV_PROG"]

TABELA_IR = [
    # dias, ISENTO, RF_REGR, FUNDO_CP, FUNDO_LP, FUNDO_ACOES, PREV_REGR, PREV_PROG
    (0,    0.0, 0.225, 0.225, 0.225, 0.15, 0.35, 0.15),
    (181,  0.0, 0.200, 0.200, 0.200, 0.15, 0.35, 0.15),
    (361,  0.0, 0.175, 0.200, 0.175, 0.15, 0.35, 0.15),
    (721,  0.0, 0.150, 0.200, 0.150, 0.15, 0.30, 0.15),
    (1441, 0.0, 0.150, 0.200, 0.150, 0.15, 0.25, 0.15),
    (2161, 0.0, 0.150, 0.200, 0.150, 0.15, 0.20, 0.15),
    (2881, 0.0, 0.150, 0.200, 0.150, 0.15, 0.15, 0.15),
    (3601, 0.0, 0.150, 0.200, 0.150, 0.15, 0.10, 0.15),
]

REGIME_DESCRICAO = {
    "ISENTO": "Isento de IR para pessoa física (LCI, LCA, poupança).",
    "RF_REGR": "Renda fixa — tabela regressiva: 22,5% até 180 dias / 20% até 360 / 17,5% até 720 / 15% acima.",
    "FUNDO_CP": "Fundo de curto prazo — come-cotas 20% semestral; 22,5% até 180 dias, 20% acima.",
    "FUNDO_LP": "Fundo de longo prazo — come-cotas 15% semestral + complemento pela tabela regressiva.",
    "FUNDO_ACOES": "Fundo de ações — 15% só no resgate, sem come-cotas.",
    "PREV_REGR": "Previdência regressiva — 35% até 2 anos, caindo 5 p.p. a cada 2 anos até 10% acima de 10 anos.",
    "PREV_PROG": "Previdência progressiva — 15% retido na fonte, com ajuste na declaração anual.",
}

# Come-cotas por regime: (regime, tem_come_cotas, alíquota)
COME_COTAS = [
    ("ISENTO", 0, 0.0),
    ("RF_REGR", 0, 0.0),
    ("FUNDO_CP", 1, 0.20),
    ("FUNDO_LP", 1, 0.15),
    ("FUNDO_ACOES", 0, 0.0),
    ("PREV_REGR", 0, 0.0),
    ("PREV_PROG", 0, 0.0),
]

# ==========================================================================
# 3) IOF REGRESSIVO — % do RENDIMENTO, por dia corrido de aplicação
# ==========================================================================
TABELA_IOF = [
    0.96, 0.93, 0.90, 0.86, 0.83, 0.80, 0.76, 0.73, 0.70, 0.66,
    0.63, 0.60, 0.56, 0.53, 0.50, 0.46, 0.43, 0.40, 0.36, 0.33,
    0.30, 0.26, 0.23, 0.20, 0.16, 0.13, 0.10, 0.06, 0.03, 0.00,
]  # índice 0 = 1 dia ... índice 29 = 30 dias

# ==========================================================================
# 4) TABELA PROGRESSIVA MENSAL DO IRPF (carnê-leão do aluguel / previdência
#    progressiva). Faixas em R$/mês, ordem crescente.
#    ⚠ Conferir vigência antes de usar — Receita Federal.
# ==========================================================================
TABELA_IRPF_MENSAL = [
    # (base mínima da faixa, alíquota, parcela a deduzir)
    (0.00, 0.000, 0.00),
    (2428.81, 0.075, 182.16),
    (2826.66, 0.150, 394.16),
    (3751.06, 0.225, 675.49),
    (4664.69, 0.275, 908.73),
]

# ==========================================================================
# 5) BASE DE PRODUTOS
# ==========================================================================
COLUNAS_PRODUTOS = [
    ("ID", 7), ("Nome do produto", 38), ("Categoria", 15), ("Emissor / Gestor", 18),
    ("Benchmark", 11), ("% do benchmark", 11), ("Spread a.a.", 10), ("Composição", 11),
    ("Taxa adm. a.a.", 10), ("Taxa perf. (%)", 10), ("Carreg. entrada", 10),
    ("Carreg. saída", 10), ("Custódia a.a.", 10), ("Regime tributário", 14),
    ("Base tributável", 10), ("Carência (dias)", 10), ("Liquidez (dias)", 10),
    ("Aplicação mínima", 13), ("Aporte mín. mensal", 12), ("Risco (1-5)", 9),
    ("Volatilidade a.a.", 11), ("Garantia", 17), ("Rent. 12m (obs.)", 11),
    ("Rent. 36m a.a. (obs.)", 12), ("Atualizado em", 12), ("Fonte", 30),
    ("Tipo de dado", 16), ("Status", 18), ("Observações", 46), ("Ativo", 8),
]

# Base tributável: 1 = só o rendimento | 2 = o valor total resgatado (PGBL)
_P = lambda *a: a  # noqa: E731  (só para leitura em coluna)

PRODUTOS = [
    # ---------------------------------------------------------------- RENDA FIXA
    _P("RF01", "Poupança", "Renda Fixa", "CAIXA",
       "POUP", 1.00, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "ISENTO", 1,
       0, 0, 0.01, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Lei 12.703/2012 — regra de remuneração", "Calculado", "VERIFICADO",
       "Só remunera na data de aniversário mensal: saque antes do aniversário perde o rendimento do mês.", "SIM"),

    _P("RF02", "CDB CAIXA Liquidez Diária", "Renda Fixa", "CAIXA",
       "CDI", 0.98, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "RF_REGR", 1,
       0, 0, 100.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência", "Cadastral", _EX,
       "Resgate no mesmo dia. IOF nos 30 primeiros dias.", "SIM"),

    _P("RF03", "CDB CAIXA 12 meses", "Renda Fixa", "CAIXA",
       "CDI", 1.02, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "RF_REGR", 1,
       360, 0, 1000.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência", "Cadastral", _EX,
       "Sem liquidez antes do vencimento.", "SIM"),

    _P("RF04", "CDB CAIXA 24 meses", "Renda Fixa", "CAIXA",
       "CDI", 1.05, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "RF_REGR", 1,
       720, 0, 5000.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência", "Cadastral", _EX,
       "No vencimento cai na menor alíquota de IR (15%).", "SIM"),

    _P("RF05", "CDB CAIXA 60 meses", "Renda Fixa", "CAIXA",
       "CDI", 1.10, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "RF_REGR", 1,
       1800, 0, 10000.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência", "Cadastral", _EX,
       "Prazo longo em troca de taxa maior. Avaliar necessidade de liquidez.", "SIM"),

    _P("RF06", "LCI CAIXA 12 meses", "Renda Fixa", "CAIXA",
       "CDI", 0.92, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "ISENTO", 1,
       360, 0, 5000.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência + CMN (prazo mínimo)", "Cadastral", _EX,
       "Isenta de IR para pessoa física. Confirmar o prazo mínimo de carência vigente.", "SIM"),

    _P("RF07", "LCA CAIXA 12 meses", "Renda Fixa", "CAIXA",
       "CDI", 0.91, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "ISENTO", 1,
       270, 0, 5000.0, 0.0, 1, 0.001, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Tabela de taxas da agência + CMN (prazo mínimo)", "Cadastral", _EX,
       "Isenta de IR para pessoa física. Confirmar o prazo mínimo de carência vigente.", "SIM"),

    _P("RF08", "Tesouro Selic 2031", "Renda Fixa", "Tesouro Nacional",
       "SELIC", 1.00, 0.0002, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0020, "RF_REGR", 1,
       0, 1, 100.0, 0.0, 1, 0.002, "Tesouro Nacional", None, None,
       DATA_REFERENCIA, "Tesouro Transparente — taxas dos títulos", "Diário (D+1)", _EX,
       "Custódia B3 de 0,20% a.a.; verificar a isenção vigente para saldos menores.", "SIM"),

    _P("RF09", "Tesouro IPCA+ 2035", "Renda Fixa", "Tesouro Nacional",
       "IPCA", 1.00, 0.0600, "MULT", 0.0, 0.0, 0.0, 0.0, 0.0020, "RF_REGR", 1,
       0, 1, 100.0, 0.0, 2, 0.080, "Tesouro Nacional", None, None,
       DATA_REFERENCIA, "Tesouro Transparente — taxas dos títulos", "Diário (D+1)", _EX,
       "Protege da inflação se levado até o vencimento. Antes disso o preço oscila (marcação a mercado).", "SIM"),

    _P("RF10", "Tesouro Prefixado 2031", "Renda Fixa", "Tesouro Nacional",
       "PRE", 1.00, 0.1200, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0020, "RF_REGR", 1,
       0, 1, 100.0, 0.0, 2, 0.060, "Tesouro Nacional", None, None,
       DATA_REFERENCIA, "Tesouro Transparente — taxas dos títulos", "Diário (D+1)", _EX,
       "Taxa travada na contratação: não muda se a Selic subir ou cair.", "SIM"),

    # ------------------------------------------------------------------- FUNDOS
    _P("FU01", "Fundo CAIXA RF Simples", "Fundo", "CAIXA Asset",
       "CDI", 1.00, 0.0, "SOMA", 0.0040, 0.0, 0.0, 0.0, 0.0, "FUNDO_LP", 1,
       0, 0, 100.0, 50.0, 1, 0.002, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Porta de entrada, aplicação mínima baixa.", "SIM"),

    _P("FU02", "Fundo CAIXA RF Referenciado DI LP", "Fundo", "CAIXA Asset",
       "CDI", 1.00, 0.0, "SOMA", 0.0080, 0.0, 0.0, 0.0, 0.0, "FUNDO_LP", 1,
       0, 0, 1000.0, 100.0, 1, 0.002, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Resgate no mesmo dia. Sofre come-cotas em maio e novembro.", "SIM"),

    _P("FU03", "Fundo CAIXA RF Crédito Privado LP", "Fundo", "CAIXA Asset",
       "CDI", 1.04, 0.0, "SOMA", 0.0100, 0.0, 0.0, 0.0, 0.0, "FUNDO_LP", 1,
       0, 30, 5000.0, 200.0, 2, 0.010, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Rende mais que o DI puro, mas assume risco de crédito das empresas.", "SIM"),

    _P("FU04", "Fundo CAIXA RF IPCA Longo Prazo", "Fundo", "CAIXA Asset",
       "IPCA", 1.00, 0.0600, "MULT", 0.0100, 0.0, 0.0, 0.0, 0.0, "FUNDO_LP", 1,
       0, 5, 5000.0, 200.0, 3, 0.080, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Oscila bastante no curto prazo. Indicado para prazos longos.", "SIM"),

    _P("FU05", "Fundo CAIXA Multimercado", "Fundo", "CAIXA Asset",
       "CDI", 1.00, 0.0250, "SOMA", 0.0150, 0.20, 0.0, 0.0, 0.0, "FUNDO_LP", 1,
       0, 30, 5000.0, 200.0, 3, 0.060, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Taxa de performance de 20% sobre o que exceder o CDI. Resgate em cerca de 30 dias.", "SIM"),

    _P("FU06", "Fundo CAIXA Ações Ibovespa", "Fundo", "CAIXA Asset",
       "IBOV", 1.00, 0.0, "SOMA", 0.0150, 0.0, 0.0, 0.0, 0.0, "FUNDO_ACOES", 1,
       0, 4, 1000.0, 100.0, 5, 0.220, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "15% de IR só no resgate, sem come-cotas. Pode ficar anos no negativo.", "SIM"),

    _P("FU07", "Fundo CAIXA Ações Dividendos", "Fundo", "CAIXA Asset",
       "IBOV", 1.00, 0.0150, "SOMA", 0.0200, 0.20, 0.0, 0.0, 0.0, "FUNDO_ACOES", 1,
       0, 30, 5000.0, 200.0, 4, 0.180, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Foco em empresas pagadoras de dividendos. Oscila menos que o Ibovespa, mas ainda é renda variável.", "SIM"),

    _P("FU08", "Fundo CAIXA Cambial Dólar", "Fundo", "CAIXA Asset",
       "CAMBIO", 1.00, 0.0, "SOMA", 0.0150, 0.0, 0.0, 0.0, 0.0, "FUNDO_CP", 1,
       0, 4, 1000.0, 100.0, 5, 0.150, "Sem garantia do FGC", None, None,
       DATA_REFERENCIA, "CAIXA Asset — portfólio de fundos (lâmina)", "Diário (D+1)", _EX,
       "Serve para proteção (viagem, despesa em dólar), não para render mais.", "SIM"),

    # -------------------------------------------------------------- PREVIDÊNCIA
    _P("PR01", "PGBL CAIXA RF — Regressivo", "Previdência", "CAIXA Vida e Previdência",
       "CDI", 0.97, 0.0, "SOMA", 0.0100, 0.0, 0.0, 0.0, 0.0, "PREV_REGR", 2,
       0, 5, 5000.0, 100.0, 1, 0.002, "Seguradora (sem FGC)", None, None,
       DATA_REFERENCIA, "Regulamento do plano + tabela de taxas", "Cadastral", _EX,
       "Só vale para quem declara IR no modelo COMPLETO. Na saída o IR incide sobre o VALOR TOTAL.", "SIM"),

    _P("PR02", "PGBL CAIXA RF — Progressivo", "Previdência", "CAIXA Vida e Previdência",
       "CDI", 0.97, 0.0, "SOMA", 0.0100, 0.0, 0.0, 0.0, 0.0, "PREV_PROG", 2,
       0, 5, 5000.0, 100.0, 1, 0.002, "Seguradora (sem FGC)", None, None,
       DATA_REFERENCIA, "Regulamento do plano + tabela de taxas", "Cadastral", _EX,
       "Indicado quando há previsão de resgate/renda em faixa de IR baixa ou isenta.", "SIM"),

    _P("PR03", "VGBL CAIXA RF — Regressivo", "Previdência", "CAIXA Vida e Previdência",
       "CDI", 0.97, 0.0, "SOMA", 0.0100, 0.0, 0.0, 0.0, 0.0, "PREV_REGR", 1,
       0, 5, 5000.0, 100.0, 1, 0.002, "Seguradora (sem FGC)", None, None,
       DATA_REFERENCIA, "Regulamento do plano + tabela de taxas", "Cadastral", _EX,
       "Para quem declara SIMPLIFICADO ou é isento. IR só sobre o rendimento.", "SIM"),

    _P("PR04", "PGBL CAIXA Composto 30 — Regressivo", "Previdência", "CAIXA Vida e Previdência",
       "CDI", 1.00, 0.0150, "SOMA", 0.0150, 0.0, 0.0, 0.0, 0.0, "PREV_REGR", 2,
       0, 5, 5000.0, 100.0, 3, 0.060, "Seguradora (sem FGC)", None, None,
       DATA_REFERENCIA, "Regulamento do plano + tabela de taxas", "Cadastral", _EX,
       "Até 30% em renda variável. Prazo longo dilui a oscilação.", "SIM"),

    _P("PR05", "VGBL CAIXA Composto 30 — Regressivo", "Previdência", "CAIXA Vida e Previdência",
       "CDI", 1.00, 0.0150, "SOMA", 0.0150, 0.0, 0.0, 0.0, 0.0, "PREV_REGR", 1,
       0, 5, 5000.0, 100.0, 3, 0.060, "Seguradora (sem FGC)", None, None,
       DATA_REFERENCIA, "Regulamento do plano + tabela de taxas", "Cadastral", _EX,
       "Sucessão sem inventário é um diferencial relevante deste produto.", "SIM"),

    # ----------------------------------------------------------- ATIVO REAL
    _P("IM01", "Imóvel para aluguel", "Imobiliário", "Mercado",
       "IMOB_VAL", 1.00, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "IMOVEL", 1,
       0, 180, 50000.0, 0.0, 3, 0.070, "Nenhuma", None, None,
       DATA_REFERENCIA, "Premissas da aba Imóvel — FipeZAP como referência", "Mensal (com defasagem)", _EX,
       "Calculado na aba Imóvel (motor próprio: aluguel, vacância, IPTU, manutenção, custos de compra e venda).", "SIM"),

    # ---------------------------------------- LINHA-EXEMPLO PARA NOVOS PRODUTOS
    _P("ZZ99", "► EXEMPLO — copie esta linha para cadastrar um produto novo",
       "Renda Fixa", "Emissor XYZ",
       "CDI", 1.05, 0.0, "SOMA", 0.0, 0.0, 0.0, 0.0, 0.0, "RF_REGR", 1,
       0, 0, 1000.0, 0.0, 2, 0.005, "FGC até R$ 250 mil", None, None,
       DATA_REFERENCIA, "Onde você conferiu o dado", "Cadastral", _EX,
       "Deixe a coluna Ativo como NÃO enquanto estiver preenchendo.", "NÃO"),
]

# ==========================================================================
# 6) FONTES DE DADOS — governança e atualização
# ==========================================================================
FONTES = [
    ("Selic / CDI / IPCA / TR / IGP-M", "Banco Central do Brasil — API SGS",
     "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json",
     "Selic 432 · CDI 4389 · IPCA 433 · TR 226 · IGP-M 189",
     "Diário / mensal, com defasagem de 1 dia útil", "AUTOMÁTICA",
     "scripts/atualizar_dados.py — grava direto na aba Premissas"),

    ("Taxas dos títulos públicos", "Tesouro Transparente (Tesouro Nacional)",
     "https://www.tesourotransparente.gov.br/ckan/dataset/taxas-dos-titulos-ofertados-pelo-tesouro-direto",
     "Taxa de compra/venda por título e vencimento",
     "Diário, divulgado em D+1", "SEMIAUTOMÁTICA",
     "CSV público — o script baixa e sugere o spread dos produtos Tesouro"),

    ("Fundos CAIXA — taxas e política", "CAIXA Asset — portfólio de fundos",
     "https://www.caixa.gov.br/caixa-asset/portfolio-fundos/Paginas/default.aspx",
     "Taxa de administração, aplicação mínima, cota de resgate, classificação",
     "Cadastral — muda por decisão do gestor, sem periodicidade fixa", "MANUAL",
     "Página sem API pública. Conferir na lâmina do fundo e atualizar a aba Produtos"),

    ("Fundos — cota e patrimônio diários", "CVM — Dados Abertos (Informe Diário)",
     "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/",
     "Cota diária por CNPJ do fundo — permite calcular rentabilidade e volatilidade reais",
     "Diário, publicado com 2 a 5 dias úteis de atraso", "AUTOMÁTICA (por CNPJ)",
     "scripts/atualizar_dados.py --cvm — preenche Rent. 12m / 36m e Volatilidade"),

    ("Índices de mercado (IMA-B, IHFA, IRF-M)", "ANBIMA",
     "https://www.anbima.com.br/pt_br/informar/estatisticas/precos-e-indices/",
     "Índices de referência de renda fixa e multimercado",
     "Diário, com defasagem", "MANUAL",
     "Usar como benchmark alternativo ao CDI em produtos indexados"),

    ("Preço e aluguel de imóveis", "Índice FipeZAP",
     "https://www.fipe.org.br/pt-br/indices/fipezap/",
     "Variação de preço de venda e de locação, e yield por cidade",
     "Mensal, com defasagem", "MANUAL",
     "Alimenta IMOB_VAL e IMOB_YLD na aba Premissas — ajustar por cidade/bairro"),

    ("Tabelas de IR, IOF e carnê-leão", "Receita Federal do Brasil",
     "https://www.gov.br/receitafederal/",
     "Tabela progressiva mensal, tabelas regressivas, limite de dedução do PGBL",
     "Muda por lei/IN — verificar a cada mudança de exercício", "MANUAL",
     "Atualizar os blocos de tributação da aba Premissas e registrar a data"),

    ("Cobertura do FGC", "Fundo Garantidor de Créditos",
     "https://www.fgc.org.br/",
     "Limite por CPF e por instituição, e teto global quadrienal",
     "Cadastral", "MANUAL",
     "Alimenta o alerta de concentração da aba Consultor"),
]

# ==========================================================================
# 7) GLOSSÁRIO — linguagem simples (aba Glossário e balões de ajuda)
# ==========================================================================
GLOSSARIO = [
    ("Liquidez",
     "É a facilidade e o tempo necessário para transformar seu investimento em dinheiro disponível na conta.",
     "Poupança: dinheiro na hora. Imóvel: pode levar meses para vender."),
    ("Carência",
     "É o tempo mínimo que o dinheiro precisa ficar aplicado antes de você poder retirar.",
     "Uma LCI de 12 meses não pode ser resgatada antes desse prazo."),
    ("Risco",
     "É a possibilidade de o resultado ser diferente do esperado — para menos ou para mais.",
     "Poupança quase não oscila. Fundo de ações pode cair e demorar a se recuperar."),
    ("Oscilação (volatilidade)",
     "É o quanto o valor do investimento sobe e desce no caminho até o final.",
     "Oscilação baixa: o valor sobe quase em linha reta. Alta: sobe e desce bastante."),
    ("Rentabilidade",
     "É o quanto o dinheiro rendeu em um período, em percentual.",
     "R$ 100 que viraram R$ 110 em um ano renderam 10% no ano."),
    ("CDI",
     "É a taxa de referência dos investimentos de renda fixa no Brasil. Anda quase junto com a taxa Selic.",
     "'100% do CDI' significa render o mesmo que essa taxa de referência."),
    ("Selic",
     "É a taxa básica de juros da economia, definida pelo Banco Central.",
     "Quando a Selic sobe, a renda fixa tende a render mais."),
    ("IPCA",
     "É o índice oficial da inflação: mede quanto os preços subiram.",
     "Se o dinheiro rendeu 8% e a inflação foi 5%, o ganho real foi de cerca de 3%."),
    ("Ganho real",
     "É o quanto o dinheiro rendeu ACIMA da inflação — ou seja, o quanto você realmente ganhou de poder de compra.",
     "É o número que importa em prazos longos."),
    ("Come-cotas",
     "É um imposto que alguns fundos pagam automaticamente em maio e novembro, mesmo sem você resgatar.",
     "Ele reduz um pouco o saldo duas vezes por ano. Fundos de ações não têm come-cotas."),
    ("Tabela regressiva de IR",
     "Quanto mais tempo o dinheiro fica aplicado, menor o imposto sobre o rendimento.",
     "22,5% até 6 meses, caindo até 15% depois de 2 anos."),
    ("IOF",
     "É um imposto que só existe quando o resgate acontece nos 30 primeiros dias.",
     "A partir do 30º dia ele deixa de ser cobrado."),
    ("FGC",
     "É um fundo que devolve seu dinheiro, até um limite por CPF e por banco, se a instituição quebrar.",
     "Protege poupança, CDB, LCI e LCA. Não protege fundos de investimento."),
    ("PGBL",
     "Plano de previdência para quem declara o Imposto de Renda no modelo completo: permite abater os aportes.",
     "Na retirada, o imposto incide sobre o valor total, não só sobre o rendimento."),
    ("VGBL",
     "Plano de previdência para quem declara no modelo simplificado ou é isento.",
     "Na retirada, o imposto incide apenas sobre o rendimento."),
    ("Regime regressivo (previdência)",
     "O imposto começa em 35% e cai 5 pontos a cada 2 anos, até 10% depois de 10 anos.",
     "Faz sentido para quem vai deixar o dinheiro por muitos anos."),
    ("Regime progressivo (previdência)",
     "Segue a tabela do salário: 15% na fonte e acerto na declaração anual.",
     "Faz sentido para quem vai receber valores baixos ou é isento de IR."),
    ("Marcação a mercado",
     "É a variação diária do preço de um título antes do vencimento.",
     "Um Tesouro IPCA+ pode valer menos hoje e ainda assim pagar o combinado no vencimento."),
    ("Vacância",
     "É o tempo em que um imóvel fica sem inquilino — e portanto sem renda.",
     "Vacância de 8% ao ano equivale a cerca de um mês por ano sem aluguel."),
    ("Yield de aluguel",
     "É o aluguel anual dividido pelo valor do imóvel.",
     "Um imóvel de R$ 300 mil que rende R$ 1.500/mês tem yield bruto de 6% ao ano."),
    ("Ganho de capital",
     "É o lucro na venda de um bem — a diferença entre o preço de venda e o de compra.",
     "Na venda de imóvel há imposto sobre esse lucro, com regras de isenção específicas."),
    ("Diversificação",
     "É dividir o dinheiro entre alternativas diferentes para não depender de um único resultado.",
     "Parte com liquidez para emergências, parte em prazo mais longo."),
    ("Suitability",
     "É a análise de perfil que verifica se um investimento combina com o cliente.",
     "É obrigatória e é feita no sistema oficial — esta planilha não substitui esse processo."),
]

# ==========================================================================
# 8) LISTAS DE ESCOLHA (validação de dados)
# ==========================================================================
HORIZONTES = [
    ("Até 1 ano", 12),
    ("1 a 3 anos", 36),
    ("3 a 5 anos", 60),
    ("5 a 10 anos", 120),
    ("Mais de 10 anos", 180),
    ("Prazo personalizado", 0),
]

PRIORIDADES = [
    "Segurança acima de tudo",
    "Equilíbrio entre segurança e rentabilidade",
    "Rentabilidade, aceitando oscilação",
    "Poder retirar a qualquer momento",
]

PERFIS = ["Conservador", "Moderado", "Arrojado"]
TETO_RISCO = {"Conservador": 2, "Moderado": 3, "Arrojado": 5}
RESGATE_ANTES = ["Sim", "Talvez", "Não"]
CENARIOS = ["Conservador", "Base", "Otimista"]
SIM_NAO = ["Sim", "Não"]
DESTINO_ALUGUEL = ["Reinvestir", "Consumir (renda mensal)"]

# Tradução de números para linguagem de cliente
ESCALA_RISCO = {
    1: ("Muito baixa", "O valor praticamente não oscila."),
    2: ("Baixa", "Pequenas variações no caminho."),
    3: ("Média", "Sobe e desce, mas tende a se acomodar em prazos longos."),
    4: ("Alta", "Variações grandes. Exige prazo e tranquilidade."),
    5: ("Muito alta", "Pode cair bastante e demorar a se recuperar."),
}
