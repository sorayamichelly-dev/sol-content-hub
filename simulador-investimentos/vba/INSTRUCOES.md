# Macros — opcionais, e só se o seu ambiente permitir

## Leia isto antes de instalar

**A planilha funciona inteira sem macro nenhuma.** Isso não é preguiça: é
decisão de projeto.

Ambiente corporativo de banco costuma bloquear arquivos `.xlsm` por política de
segurança. Uma ferramenta de atendimento que só funciona com macro habilitada é
uma ferramenta que, na hora do aperto, não funciona — e o pior momento para
descobrir isso é com o cliente sentado na sua frente.

Por isso tudo que normalmente viraria botão de macro foi resolvido com fórmula:

| Botão que você esperaria | Como está resolvido |
|---|---|
| **SIMULAR** | Não existe, e é melhor assim: mudou a resposta, o número muda na hora. Você altera o prazo conversando e o cliente vê o efeito acontecendo. |
| **COMPARAR** | A aba **Comparar** já mostra as seis alternativas mais o imóvel, sempre atualizadas. |
| **SUGERIR ALTERNATIVAS** | Parâmetro *"Preencher as alternativas com a sugestão automática?"* na aba **Consultor**. |
| **VER DETALHES / VER GRÁFICOS / VOLTAR** | Os botões azuis são hyperlinks internos. Funcionam em `.xlsx`, no Excel Online e no LibreOffice. |
| **VER MÊS A MÊS** | Aba **MesAMes**, com seletor de alternativa. |
| **LIMPAR** | As células que você preenche são as amarelas. Selecionar e apagar leva três segundos. |

Sobra pouca coisa que macro resolve de verdade — e é o que está no módulo.

## O que os macros acrescentam

| Rotina | O que faz |
|---|---|
| `NovoCliente` | Volta todas as respostas ao padrão, oferecendo salvar a simulação atual antes. |
| `LimparEscolhas` | Zera as alternativas escolhidas à mão e religa a sugestão automática. |
| `GerarRelatorioPDF` | Exporta a aba Relatório em PDF já nomeado com cliente e data, na pasta da planilha. |
| `SalvarSimulacao` | Guarda um resumo do atendimento numa aba `Historico` (criada na primeira vez). |
| `AtualizarIndicadores` | Busca Selic, CDI, IPCA e TR na API do Banco Central e grava na coluna *Base* da aba Premissas, carimbando a data e registrando na aba Fontes. |

`AtualizarIndicadores` **não** mexe nos cenários Conservador e Otimista: um dado
observado não vira projeção sozinho. Essa escolha continua sendo sua.

## Como instalar

1. Abra `Simulador_Investimentos.xlsx`.
2. **Arquivo ▸ Salvar como ▸ Pasta de trabalho habilitada para macro (`.xlsm`)**.
3. `Alt + F11` abre o editor do VBA.
4. **Arquivo ▸ Importar arquivo** e escolha `vba/modSimulador.bas`.
5. Volte para a planilha. Para criar um botão: **Desenvolvedor ▸ Inserir ▸ Botão**,
   desenhe onde quiser e associe à rotina desejada.
   (Se a guia Desenvolvedor não aparece: **Arquivo ▸ Opções ▸ Personalizar Faixa
   de Opções ▸ marcar Desenvolvedor**.)

Guarde os dois arquivos. O `.xlsx` é o que sempre abre em qualquer máquina; o
`.xlsm` é a versão com os extras, para quando o ambiente permitir.

## Se a rede bloquear a consulta ao Banco Central

Muita rede corporativa exige proxy autenticado, e o `AtualizarIndicadores` vai
falhar com um aviso — sem quebrar nada. Nesse caso use o caminho de fora da
planilha, que aceita as variáveis de proxy do sistema:

```
python3 scripts/atualizar_dados.py
python3 build.py
```
