# Simulador de Investimentos

Ferramenta de apoio à venda consultiva. Motor de cálculo pesado, painel simples.

O cliente responde cinco perguntas e vê, em linguagem de gente, quanto pode ter,
quando pode retirar e o que pode dar errado. O consultor abre a mesma simulação
por outra porta e enxerga cada premissa, cada taxa, cada centavo de imposto e a
data de atualização de cada dado.

> **Leia primeiro:** [`docs/ANALISE_CRITICA.md`](docs/ANALISE_CRITICA.md) — o que
> foi mudado em relação à ideia original, o que foi acrescentado, o que foi
> simplificado de propósito e o que ficou de fora.

---

## Começando

```bash
pip install openpyxl requests
python3 build.py
```

Gera `Simulador_Investimentos.xlsx`. Abra e comece pela aba **Início**.
(Se houver LibreOffice na máquina, o `build.py` já preenche os valores no fim.
Se não houver, tudo bem: a planilha pede recálculo sozinha ao abrir no Excel.)

**Antes do primeiro atendimento**, atualize os dados — a planilha nasce com
taxas de referência, todas marcadas em laranja como `EXEMPLO — VERIFICAR`:

```bash
python3 scripts/atualizar_dados.py     # Selic, CDI, IPCA e TR no Banco Central
python3 build.py                       # regera já com os dados novos
```

E confira produto a produto na lâmina e na tabela de taxas vigente, mudando o
**Status** para `VERIFICADO` na aba Produtos.

---

## As três camadas

A separação é rígida, e é o que faz a manutenção ser possível: **mudar uma taxa
nunca exige mexer em fórmula nenhuma.**

```
   INTERFACE          Início · Cliente · Comparar · Relatório
   (o que se vê)      Consultor · MesAMes · Imóvel · Previdência
        ↑
        │ só leem
        │
   CÁLCULO            Motor · MotorImovel · Adequação
   (nada é digitado)  32 mil fórmulas, projeção mês a mês, 0 a 240 meses
        ↑
        │ só leem
        │
   DADOS              Produtos · Premissas · Fontes · Glossário
   (nada é fórmula)   é aqui que você mexe
```

| Aba | Camada | Para que serve |
|---|---|---|
| **Início** | interface | Capa, navegação e situação dos dados |
| **Cliente** | interface | As cinco perguntas e o resultado. É a tela para virar o monitor |
| **Comparar** | interface | Alternativas lado a lado e os quatro gráficos |
| **Consultor** | interface | Premissas, painel técnico, alertas, calculadora de IOF |
| **MesAMes** | interface | Projeção linha a linha de uma alternativa |
| **Imóvel** | interface | Comprar para alugar — o caso do Seu João |
| **Previdência** | interface | PGBL × VGBL, progressivo × regressivo, benefício fiscal |
| **Relatório** | interface | Uma página A4, pronta para PDF |
| **Adequação** | cálculo | Nota de encaixe com o objetivo — **não** usa rentabilidade |
| **Motor** | cálculo | Projeção mensal das seis alternativas financeiras |
| **MotorImovel** | cálculo | Projeção mensal do imóvel (mecânica própria) |
| **Produtos** | dados | Base de produtos — cadastre e altere aqui |
| **Premissas** | dados | Indicadores, cenários e todas as tabelas de tributação |
| **Fontes** | dados | De onde vem cada dado, com que atraso, e o log de atualizações |
| **Glossário** | dados | Explicações curtas para usar na conversa |

---

## O que o motor calcula, mês a mês

Para cada mês, de 0 a 240:

```
saldo inicial       = saldo final do mês anterior
aporte              = aporte do cliente (+ restituição do PGBL, se reinvestida)
custo de entrada    = aporte × carregamento
rendimento bruto    = saldo inicial × taxa mensal bruta do cenário
taxa de adm.        = saldo inicial × (administração + custódia) / 12
taxa de performance = % sobre o que o rendimento excedeu o benchmark
come-cotas          = em maio e novembro, alíquota × ganho ainda não tributado
saldo final         = saldo inicial + rendimento − custos + aporte líquido − come-cotas
IR no resgate       = alíquota(prazo) × base tributável − come-cotas já pago
valor líquido       = saldo final − IR − carregamento de saída
em R$ de hoje       = valor líquido ÷ inflação acumulada
```

Tributação coberta: tabela regressiva de renda fixa, isenção de LCI/LCA e
poupança, come-cotas de fundo de curto e de longo prazo, 15% de fundo de ações,
regressiva e progressiva de previdência (com PGBL tributando o valor total),
IOF regressivo dos 30 primeiros dias, carnê-leão do aluguel e ganho de capital
na venda do imóvel.

---

## Como sei que os números estão certos

Planilha grande falha em silêncio: uma referência trocada gera um arquivo sem
nenhum `#VALUE!` e com números errados. Por isso há dois scripts de conferência,
e vale rodar os dois depois de qualquer mexida no motor.

```bash
python3 scripts/verificar.py          # refaz as contas por fora e compara
python3 scripts/cenarios_teste.py     # repete tudo em 5 perfis de cliente
```

`verificar.py` **reimplementa** a projeção mês a mês em Python, partindo da
regra tributária — e não transcrevendo a fórmula da planilha. A diferença
importa: na primeira rodada o verificador foi escrito copiando a fórmula, e por
isso repetiu junto com ela um erro de come-cotas que fazia R$ 150 mil virarem
R$ 55 mil. Além da reprojeção, ele checa invariantes que precisam valer sempre —
imposto nunca supera o ganho bruto, líquido nunca supera o bruto, com inflação
positiva o valor real fica abaixo do nominal. São esses que pegam erro de lógica
sem depender de eu ter reimplementado a conta certa.

`cenarios_teste.py` roda cinco perfis bem diferentes (o Seu João, acumulação de
20 anos com aporte corrigido pela inflação, reserva de curto prazo, imóvel com
caixa suficiente e PGBL com restituição reinvestida), porque um motor só está
certo quando está certo para clientes diferentes.

---

## Manutenção

A planilha é um **artefato gerado**: o código-fonte é este projeto. Manter 32 mil
fórmulas arrastando célula na mão não é sustentável — uma referência quebrada no
meio da grade é silenciosa e destrói a confiança no resultado inteiro.

### O ciclo

```bash
# 1. atualizar indicadores de mercado (Banco Central)
python3 scripts/atualizar_dados.py

# 2. se você cadastrou/alterou produtos DENTRO do Excel, traga-os de volta
python3 scripts/exportar_produtos.py Simulador_Investimentos.xlsx

# 3. regerar
python3 build.py
```

O passo 2 existe por um motivo técnico: a biblioteca que gera a planilha não sabe
reler gráficos. Se um script abrisse o arquivo pronto só para trocar uma taxa e
salvasse por cima, os quatro gráficos sumiriam. Então os dados moram em arquivos
(`dados/mercado.json`, `dados/produtos.csv`) e a planilha é sempre regerada a
partir deles — o que preserva gráficos, formatação e fórmulas.

Se nenhum desses arquivos existir, valem os valores de referência de
`src/dados_seed.py` e nada quebra.

### Cadastrar um produto novo

Direto no Excel: copie a linha `ZZ99` (a última da aba Produtos, em cinza), cole
numa linha vazia, ajuste os campos e ponha `SIM` em **Ativo**. Ele aparece
sozinho nas listas de escolha e na aba Adequação. Depois rode o passo 2 acima
para não perder o cadastro na próxima regeração.

### Estrutura do código

```
build.py                     monta a planilha
src/refs.py                  mapa de células e nomes definidos — o contrato entre camadas
src/dados_seed.py            valores de referência (produtos, premissas, glossário, fontes)
src/carga.py                 carrega dados/mercado.json e dados/produtos.csv por cima
src/estilo.py                paleta, formatos e helpers de escrita
src/abas_dados.py            abas Produtos, Premissas, Fontes, Glossário
src/motor.py                 abas Motor, MotorImovel, Adequação
src/interface.py             as oito abas de interface e os gráficos
scripts/atualizar_dados.py   Banco Central e CVM  → dados/mercado.json
scripts/exportar_produtos.py planilha             → dados/produtos.csv
scripts/verificar.py         confere os números contra uma reimplementação
scripts/cenarios_teste.py    repete as conferências em cinco perfis de cliente
vba/                         macros OPCIONAIS (leia vba/INSTRUCOES.md antes)
docs/ANALISE_CRITICA.md      as decisões de projeto e o que ficou de fora
```

Para mexer numa fórmula do motor, edite `src/motor.py` e rode `build.py`. Para
mudar onde uma entrada mora na planilha, edite só `src/refs.py` — os nomes
definidos fazem o resto e nenhuma fórmula quebra.

### Mudar o horizonte máximo

`MESES_MAX` em `src/refs.py` (padrão 240 = 20 anos). Todo o resto se ajusta.

---

## Convenção de cores

| Cor | Significado |
|---|---|
| Fundo **amarelo** | Célula que você preenche |
| Texto **azul** | Valor digitado |
| Texto **preto** | Cálculo da própria aba |
| Texto **verde** | Valor que vem de outra aba |
| Linha **laranja** (aba Produtos) | Dado ainda não conferido |

---

## Botões

Os botões azuis são hyperlinks internos — funcionam no Excel, no Excel Online e
no LibreOffice, sem macro. Não existe botão `SIMULAR`: mudou a resposta, o número
muda na hora. Detalhes e as macros opcionais em [`vba/INSTRUCOES.md`](vba/INSTRUCOES.md).

---

## Avisos

**Simulação baseada nas informações e premissas registradas na planilha. Os
resultados reais podem ser diferentes.** Rentabilidade passada não é garantia de
rentabilidade futura, e nenhum número aqui representa promessa de retorno.

**Ferramenta de apoio à conversa, de uso do profissional.** Não é peça oficial de
oferta e não substitui a lâmina, o regulamento, o prospecto do produto nem o
questionário oficial de perfil (suitability).

Cenário não é previsão: é um conjunto de premissas escolhido pelo consultor para
mostrar ao cliente uma faixa de resultados possíveis.
