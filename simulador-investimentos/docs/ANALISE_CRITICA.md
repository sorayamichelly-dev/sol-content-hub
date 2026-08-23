# Análise crítica do projeto, antes de construir

Você pediu para não executar as instruções cegamente. Este documento registra o
que foi mudado, o que foi acrescentado, o que foi deliberadamente simplificado e
o que ficou de fora — com o motivo de cada decisão.

---

## 1. Onde a ideia original tinha um problema

### 1.1 Botões e macros esbarram na política de segurança do banco

Você pediu botões (`SIMULAR`, `COMPARAR`, `LIMPAR`, `GERAR RELATÓRIO`). Faz todo
sentido do ponto de vista de usabilidade — mas macro exige `.xlsm`, e ambiente
corporativo de banco costuma bloquear isso. Uma ferramenta de atendimento que só
funciona com macro habilitada é uma ferramenta que falha justamente quando o
cliente está sentado na frente.

**O que foi feito:** o núcleo é 100% fórmula, em `.xlsx`.

- `SIMULAR` deixou de existir — e ficou melhor. Mudou a resposta, o número muda
  na hora. Você altera o prazo conversando e o cliente vê o efeito acontecer.
  Um botão SIMULAR introduziria a dúvida "esse número já está atualizado?".
- `SUGERIR` virou um parâmetro liga/desliga na aba Consultor.
- `VER DETALHES`, `VER GRÁFICOS`, `VOLTAR` viraram hyperlinks internos —
  funcionam no Excel, no Excel Online e no LibreOffice, sem macro.
- Sobrou o que macro resolve de verdade (novo cliente, PDF, histórico,
  atualizar dados): está em `vba/modSimulador.bas`, **opcional**.

### 1.2 "Não faça ranking" e "mostre o patrimônio lado a lado" se contradizem

Você foi claro: nada de ranking de "qual rende mais". Mas qualquer tabela que
mostre patrimônio final lado a lado **vira** um ranking na cabeça do cliente.
Dizer "não é ranking" no rodapé não resolve.

**O que foi feito:** separação real entre as duas coisas.

- A **nota de aderência** (aba Adequação) não usa rentabilidade em nenhum ponto
  do cálculo. Ela pontua prazo, liquidez, prioridade declarada e eficiência
  tributária. O retorno estimado aparece só na última coluna, marcada como
  informação.
- Aderência é rótulo, não número, na tela do cliente: *"Pode fazer sentido"*,
  *"Talvez faça sentido"*, *"Provavelmente não é o mais indicado"*.
- O maior patrimônio é destacado, sim — mas com a frase colada nele: *"Maior
  patrimônio não significa melhor escolha: liquidez, risco e objetivo pesam
  tanto quanto o número."*
- Um produto pode ter aderência alta e rentabilidade baixa. Isso é proposital.

### 1.3 A comparação do Seu João estava torta desde o começo

O exemplo pede: R$ 150.000 em aplicação **ou** uma casa de R$ 150.000.
Só que R$ 150.000 **não compram** uma casa de R$ 150.000. Faltam ITBI (~2%),
escritura e registro (~1,5%). O desembolso real fica em torno de R$ 155.250.

Comparar R$ 150.000 aplicados contra R$ 155.250 em imóvel infla o imóvel — e é
exatamente o erro que a maioria das simulações de corretor de imóveis comete.

**O que foi feito:**

- A aba Imóvel calcula o **desembolso total** e avisa, em vermelho, quanto falta.
- Se sobrar dinheiro, a sobra entra na simulação como caixa aplicado (senão o
  lado financeiro é que ficaria inflado).
- Os aportes mensais também entram na estratégia imobiliária, indo para o caixa.
  Sem isso, comparar "R$ 150.000 + R$ 500/mês aplicados" contra "só a casa" seria
  desonesto do outro lado.
- Entram na conta: vacância, IPTU, manutenção, seguro, taxa de administração
  imobiliária, carnê-leão sobre o aluguel (com IPTU e administração dedutíveis, e
  manutenção **não** dedutível — são tratamentos diferentes), corretagem na
  venda e ganho de capital.
- A pergunta "reinvestir ou gastar o aluguel?" está lá, com a frase explicando
  que ela muda o resultado inteiro.

### 1.4 Prioridade e perfil não são a mesma coisa

O questionário original mistura "o que é mais importante para você" com o perfil
de investidor. São coisas diferentes: prioridade é o que o cliente **quer** hoje;
perfil é o que o processo formal de suitability **apurou**. Um cliente de perfil
conservador pode dizer que quer rentabilidade — e a ferramenta não pode
simplesmente obedecer.

**O que foi feito:** duas perguntas separadas. A prioridade define os **pesos**
da nota de aderência; o perfil funciona como **teto duro** de risco. Produto
acima do perfil recebe nota zero e sai da sugestão, com o motivo escrito.

---

## 2. O que faltava e foi acrescentado

### 2.1 Carência (o campo que ninguém lembra)

LCI e LCA têm prazo mínimo antes do resgate. CDB de prazo tem vencimento. Sem
esse campo, a planilha recomendaria uma LCI de 12 meses para quem acabou de
responder "sim, posso precisar do dinheiro antes" — e essa recomendação
destruiria a confiança do cliente no dia em que ele tentasse sacar.

Cada produto tem agora **carência** e **liquidez após a carência**, separadas.
A resposta sobre resgate antecipado vira filtro, e o cliente vê a data exata a
partir da qual pode retirar.

### 2.2 Come-cotas com efeito de caixa correto

Não basta descontar imposto no final. O come-cotas **sai do saldo** em maio e
novembro e, a partir dali, deixa de render. Em 10 anos isso é dinheiro de
verdade — e é a principal desvantagem de fundo de renda fixa contra LCI.

O motor cobra o come-cotas no mês em que ele acontece, acumula o que já foi pago
e, no resgate, cobra apenas o **complemento** (`alíquota do prazo × ganho
total − come-cotas já pago`). Sem dupla tributação e sem subestimar o imposto.

### 2.3 O benefício fiscal do PGBL

É o principal argumento do produto e a maioria das simulações ou ignora, ou
trata como se fosse desconto permanente. Não é: é adiantamento. Na saída, o IR
incide sobre o **valor total**, não só sobre o rendimento.

A planilha calcula a dedução (limitada a 12% da renda bruta anual), converte em
reais pela alíquota marginal do cliente, e oferece dois caminhos: **consumir** o
benefício ou **reinvestir** (volta como aporte extra em maio de cada ano, e
passa a compor). A diferença entre os dois costuma ser a parte mais convincente
da conversa.

Há um portão antes de tudo isso: *"o cliente declara no modelo completo?"*. Se
não, a aba Previdência diz com todas as letras que o PGBL não faz sentido ali.

### 2.4 Valor real, em toda tela

Projeção de 10 anos sem deflacionar engana. "R$ 380 mil" impressiona; "R$ 250 mil
em poder de compra de hoje" é a informação útil. Toda tela mostra os dois.

### 2.5 Renda mensal honesta

"Renda potencial" costuma ser calculada como o rendimento nominal do patrimônio —
o que, na prática, corrói o principal ano após ano. A planilha mostra duas linhas:
renda nominal e **renda que preserva o poder de compra**. A segunda é bem menor,
e é a que dá para sustentar por décadas.

### 2.6 Alerta de FGC

R$ 150.000 em CDB somados à poupança do mesmo banco podem passar do limite por
CPF e instituição. O alerta é automático na aba Consultor.

### 2.7 IOF de curto prazo, num lugar que faz sentido

A projeção mês a mês trata cada mês como 30 dias — o que faz as faixas de IR
baterem exatamente (180, 360, 720 dias), mas significa que o IOF nunca aparece.
Só que "e se eu precisar sacar em 10 dias?" é pergunta de balcão.

Solução: uma calculadora separada de resgate antes de 30 dias na aba Consultor,
com a tabela de IOF completa. O motor mensal fica limpo e a pergunta real tem
resposta.

### 2.8 Rastro de procedência

Cada produto carrega **fonte**, **data de atualização**, **tipo de dado**
(tempo real / diário D+1 / mensal / histórico / cadastral / premissa / calculado)
e **status** (verificado ou pendente). Produto não conferido fica laranja na base
e dispara alerta na aba Consultor. Enquanto houver dado de exemplo, a tela
inicial avisa.

### 2.9 Alertas de conferência

Sete verificações automáticas antes de oferecer: FGC, aplicação mínima, perfil,
dados não conferidos, caixa insuficiente para o imóvel, PGBL sem declaração
completa e incompatibilidade entre carência e necessidade de resgate.

---

## 3. O que foi deliberadamente simplificado

Simplificações estão todas documentadas dentro da própria planilha, na aba
Premissas — não escondidas em fórmula.

| Simplificação | Por quê | Impacto |
|---|---|---|
| **Sem marcação a mercado** no Tesouro IPCA+ e prefixado | Modelar exigiria curva de juros e reprecificação diária | O motor projeta a taxa contratada até o vencimento. A oscilação aparece como risco e há aviso explícito |
| **Taxa de performance mensal**, não marca d'água | Marca d'água plena exigiria memória de máximo histórico por cota | Diferença pequena em cenário determinístico |
| **Previdência progressiva a 15%** | O acerto na declaração depende da renda total do cliente no ano do resgate | Parametrizado na aba Premissas; sinalizado na aba Previdência |
| **Mês = 30 dias** | Faz as faixas de IR baterem exatamente | IOF sai do motor mensal e ganha calculadora própria |
| **Retorno determinístico** por cenário | Monte Carlo confunde mais do que ajuda em atendimento de agência | Três cenários dão a faixa; "oscilação" comunica o risco |
| **Poupança sem regra de aniversário** | O motor é mensal, o aniversário é diário | Observação registrada no cadastro do produto |

---

## 4. O que ficou de fora, e por quê

- **Simulação estocástica (Monte Carlo)** — para o cliente que a ferramenta quer
  atender, "há 30% de chance de ficar abaixo de X" atrapalha mais do que ajuda.
  Três cenários e uma palavra sobre oscilação comunicam melhor.
- **Integração direta com o portal de fundos da CAIXA** — a página é HTML sem API
  pública. Raspar HTML quebra na primeira mudança de layout e não é base confiável
  para número que vai ao cliente. O caminho estruturado é a CVM (Informe Diário,
  por CNPJ), que está implementado em `scripts/atualizar_dados.py --fundo`.
- **Renda vitalícia atuarial da previdência** — exige tábua biométrica e taxa de
  conversão do plano. A arquitetura comporta; falta o dado.
- **Consórcio e COE** — cabem na base de produtos, mas têm mecânica própria
  (lance, contemplação, barreiras) que merece motor próprio.
- **Registro formal do atendimento** — isso é sistema corporativo, não planilha.

---

## 5. Uma observação sobre os dados

Não é possível, daqui, verificar as taxas vigentes dos produtos CAIXA nem os
indicadores do dia. **Tudo nasce marcado como `EXEMPLO — VERIFICAR`**, em
laranja na base, com alerta na tela inicial e na aba Consultor.

Antes do primeiro atendimento:

1. `python3 scripts/atualizar_dados.py` traz Selic, CDI, IPCA e TR do Banco
   Central (API pública, oficial).
2. Confira produto a produto na lâmina, no regulamento e na tabela de taxas
   vigente, e mude o **Status** para `VERIFICADO`.

Também vale registrar: bolsa, câmbio e valorização imobiliária **não são dados
observáveis do futuro**. São premissas suas, e a planilha as classifica assim,
em vez de disfarçá-las de projeção técnica.

---

## 6. Uma nota sobre responsabilidade

Isso está escrito na tela inicial, no relatório e na aba Consultor:

> Ferramenta de apoio à conversa, de uso do profissional. Não é peça oficial de
> oferta e não substitui a lâmina, o regulamento, o prospecto do produto nem o
> questionário oficial de perfil (suitability).

Vale insistir num ponto: a planilha **sinaliza** quando uma alternativa passa do
perfil declarado, mas quem responde pelo enquadramento é o processo formal da
instituição. A ferramenta ajuda a conversa; ela não assume a responsabilidade.
