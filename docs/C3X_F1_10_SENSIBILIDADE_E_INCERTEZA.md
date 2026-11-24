# F1.10 — sensibilidade e identificação de parâmetros do Dó4 (24/11/2026)

**F1 PENDENTE.** Base: 5d7c55b7c19f6ebb7aaecdaf0f5575c54874fb42. Pesquisa de metrologia, sem alteração de V10, DSP, aplicativo, PCM ou avanço das fases F2–F13. Não é especificação de construção/regulagem de piano real.

## Entradas e método
Reutilizada a função solidWire do laboratório F1.9, blob 8ae5b2bb81a2374ad0cc9bc88030b1c2d20b935a. Baseline hipotético homogêneo maciço retensionado para f1=261,6255653 Hz: L=0,545 m, d=1,032894736842 mm, T=534,543997811 N, E=200 GPa, rho=7850 kg/m³, B=0,0006946202431257347. Não é escala medida do C3X nem parâmetro homologado.

B=pi³ E d⁴/(64 T L²); mu=rho*pi*d²/4; f1=sqrt(T*(1+B)/mu)/(2L).
Com q=B/(1+B), derivadas logarítmicas (variação relativa infinitesimal):

| Entrada | d ln f1 / d ln entrada | d ln B / d ln entrada |
|---|---:|---:|
| L | -1-q | -2 |
| d | -1+2q | 4 |
| T | (1-q)/2 | -1 |
| E | q/2 | 1 |
| rho | -1/2 | 0 |

Derivadas conferidas por diferenças finitas centrais independentes. Para o cenário definido, f1 e B são monotônicos em cada entrada no domínio de incerteza (B muito menor que 1). Calculados extremos nos 32 vértices da caixa de limites independentes, sem hipótese probabilística. Não são intervalos de confiança. A função de vértices não garante extremos de funções arbitrárias não monotônicas.

| Limite hipotético | Erro f1 (cents) | Variação B (%) |
|---|---:|---:|
| L ±0,5 mm | -1,589 a +1,590 | -0,1832 a +0,1837 |
| d ±0,005 mm | -8,349 a +8,389 | -1,922 a +1,950 |
| T ±1% | -8,694 a +8,607 | -0,990 a +1,010 |
| E ±5% | -0,0300 a +0,0300 | -5 a +5 |
| rho ±1% | -8,613 a +8,700 | 0 |
| Todos | -27,275 a +27,316 | -7,918 a +8,328 |

f1 combinado: 257,536063 a 265,786274 Hz. B combinado: 0,000639622118 a 0,000752467518. Isto não é erro de afinação real da V10.

## Identificação inversa e medições mínimas
Dados L, d, rho, f1 e B independentes, deduzir T=4L² rho A f1²/(1+B) e E=B*T*L²/(pi² I). E inferido é efetivo dentro do modelo de apoios ideais; não equivale automaticamente ao Young intrínseco do aço real. A massa linear geométrica é rho*A; a massa derivada do alvo de afinação é efetiva/hipotética enquanto não verificada. Não misturar.

Mesmo com L e d conhecidos, multiplicar simultaneamente T, E e rho pelo mesmo fator positivo mantém f1 e B exatamente iguais. Uma medição independente de densidade/massa linear (ou de tensão ou elasticidade, sob a hipótese adotada) é necessária para eliminar essa ambiguidade; f1 e B não bastam. A geometria e propriedades precisam corresponder à mesma corda isolada. Não extrapolar para cordas enroladas.

Ensaio inverso ilustrativo: L ±0,5 mm, d ±0,005 mm, rho ±1%, f1 ±0,1 Hz, B ±5%. T=522,708350 a 546,566279 N (-2,214% a +2,249%); E efetivo=185,473918 a 215,112370 GPa (-7,263% a +7,556%). Todos os 32 vértices inversos recompõem f1 e B. Intervalos de T e E são marginais, correlacionados; não combinar extremos independentes para construir uma corda.

Prioridades: (1) identificar exemplar e contar cordas, medir comprimento vibrante e diâmetro com técnico; (2) obter massa linear/densidade independente ou outra propriedade mecânica independente e sua incerteza; (3) obter f1 e B por corda isolada, repetir em intensidades e janelas, registrar afinação e condições; (4) confrontar T e EI inferidos com medida independente, registrar resíduos/limitações dos apoios; (5) guardar proveniência, direitos e incertezas. Sem dados reais não há aceite F1.

## Testes e decisões
13/13 verificações no ambiente JavaScript V8 antes da gravação: Jacobiana versus diferenças finitas, potências do diâmetro, independência de rho em B, limites nulos, extremos e monotonicidade, 100 pontos internos determinísticos, inversão, ambiguidade de escala, limites inversos, 32 recomposições e rejeição de dados inválidos. Reproduzir em checkout Node:
`node research/c3x-physical/c4-wire-uncertainty.test.mjs`
Commits: 12dbd8f3dff17c734d0bf0e923ad63174dc8d4e8 e 600512884b9ab8bfc2fb2982e29c9aee7a9097f1. Sem alegação de CI ou hardware novo.

**Decisão:** preservar V10 e meta 32–64 vozes, sem homologar. F1.6–F1.10 forneceram 71 verificações de pesquisa, não 71 validações acústicas. A barreira agora é evidência física independente; não subdividir F1 indefinidamente com cálculos sobre os mesmos números. Próximo marco: inventário final das lacunas e protocolo de aquisição verificável, busca dirigida por dados originais legalmente utilizáveis; se indisponíveis, registrar bloqueio ou propor referência alternativa explicitamente aprovada pelo titular. Não declarar F1 concluída nem iniciar F2 sem o aceite exigido no roteiro.
