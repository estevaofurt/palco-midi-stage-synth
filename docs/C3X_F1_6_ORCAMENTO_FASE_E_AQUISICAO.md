# C3X — F1.6: orçamento de erro de fase para aquisição sincronizada (24/11/2026)

**Pesquisa F1, não F7. F1 permanece PENDENTE.** Continuação de [F1.5](C3X_F1_5_RADIACAO_IDENTIFICABILIDADE_E_ABLACAO.md). Nenhum sensor físico, dado C3X, WAV externo ou DSP alterado. O C5 Salamander é referência de pressão de outro instrumento; não fornece simultaneamente força, velocidade espacial ou aceleração. Não ajustar a V10 por H4/H5 isolados.

## Hipóteses e método

Para erro de tempo residual absoluto `dt`, a incerteza de fase em graus é limitada por `360*f*dt`. A tolerância ilustrativa de 5° (não norma nem gate aprovado) implica `dt_max=5/(360*f)`. Somamos conservadoramente limites distintos: desfasagem residual de sincronização, deriva RELATIVA residual do relógio (ppm × duração em segundos = microssegundos) e atraso diferencial residual da cadeia de sensores após calibração. Não confundir tempo de voo físico com atraso instrumental. Não assumir zeros se faltarem medições; a função rejeita campos ausentes.

Para comparar a pressão prevista por um modelo geométrico com pressão medida, acrescenta-se a incerteza do comprimento do caminho dividida por c (aqui 343 m/s hipotéticos). Isso é um limite apenas do termo de propagação; a geometria também afeta amplitude, interferência e modos, que este cálculo NÃO cobre. A incerteza de caminho não entra no H1 observado em posição fixa. Temperatura, velocidade do som, calibração de ganho/fase por frequência, ruído, reflexão e coerência precisam de validação independente. Não usar estes números como parâmetros físicos Yamaha.

## Resultados ilustrativos a 48 kHz, sem outros erros

| Frequência nominal | Limite temporal (µs) | Erro de um sample (°) | Limite de caminho se todo orçamento for geométrico (mm) |
|---:|---:|---:|---:|
| 261,626 Hz (C4) | 53,087 | 1,962 | 18,209 |
| 1046,502 Hz (4×C4) | 13,272 | 7,849 | 4,552 |
| 1308,128 Hz (5×C4) | 10,617 | 9,811 | 3,642 |
| 5000 Hz | 2,778 | 37,500 | 0,953 |
| 10000 Hz | 1,389 | 75,000 | 0,476 |

H4/H5 usam múltiplos nominais, não frequências inarmônicas medidas. A 48 kHz um sample corresponde a 20,833 µs; alinhar apenas por samples inteiros pode ser insuficiente. Exemplo: deriva relativa residual de 10 ppm por 2 s dá 20 µs e ultrapassa o orçamento nominal H5, mesmo com offset inicial zero. O cálculo não exige aumento arbitrário da taxa: requer medir e corrigir atraso fracionário, usar relógio comum, validar incerteza residual.

## Protocolo futuro de aquisição (não realizado)

1. Identificar exemplar C3X, condição, direitos, posições tridimensionais, direções e sensores. Registrar calibração complexa e seu intervalo de validade, taxa de amostragem, temperatura e hashes dos dados originais.
2. Medir força [N] e velocidade de ponte [m/s] simultâneas para mobilidade; medir aceleração [m/s²] e pressão [Pa] simultâneas para H1; mapear velocidade normal do tampo em posições conhecidas para radiação distribuída. Não inferir um bloco a partir do outro. Não aplicar H1 a C5 sozinho.
3. Calibrar atraso diferencial por frequência e medir sincronização/deriva com evento comum, no início e fim; manter relógio compartilhado e incerteza residual, sem alinhar artificialmente a propagação real. Testar saturação, piso de ruído e SNR. Se algum limite for desconhecido, não afirmar aprovação do orçamento.
4. Usar o estimador existente `research/bridge-radiation-h1.mjs` apenas com sinais calibrados simultâneos. Registrar frequência, coerência, amplitude, fase, incertezas e excitação. Usar medições repetidas e posições/excitações reservadas (holdout); comparar previsão geométrica em posições não usadas no ajuste.
5. Manter F1 pendente até evidências e aceite explícito. F2–F13 não avançam. V10 permanece intacta e prévia V8 sem samples; não promover nenhum motor.

## Implementação e testes

`research/c3x-physical/radiation-phase-budget.mjs` — função offline determinística, sem dependências, sem caminho de áudio ou integração.
`research/c3x-physical/radiation-phase-budget.test.mjs` — 12 verificações: zero, fórmula, sample, deriva, soma dos erros, geometria, fronteira, frequência, orçamento remanescente, ausência de campos, entradas inválidas e taxa de amostragem.

**Resultado:** 12/12 aprovadas executando as mesmas funções JavaScript no ambiente V8 de ferramentas antes de gravar o código. Reexecução independente em checkout/Node: `node research/c3x-physical/radiation-phase-budget.test.mjs`. Não afirmar CI ou hardware testados neste passo. Não houve nova síntese nem alteração do modelo de referência.

Commits de implementação: 795267b778b129ce1ccc9481eb556ef4911f5b2a e b1ee57fa948c3c04c19519013f252791426562b6.

**Decisão:** não substituir IR da V10. Próximo trabalho F1: buscar dados originais legalmente utilizáveis e definir a matriz de incerteza/calibração por frequência (incluindo amplitude e fase); se não houver medição física adequada, registrar bloqueio em vez de inventar parâmetros. Meta 32–64 notas preservada, sem homologação real.
