# G3 — Diagnóstico espectral e enriquecimento seletivo

Checkpoint de pesquisa de 27/11/2026. Operadores físicos arquivados e incidência corrigida, 127.825 estados da cavidade, 48 kHz de comunicação e oito subpassos a 384 kHz. 6/12 portas b16, 24/48 b64. Tampo d3 fixo, d8 na abertura como referência discreta (não contínua).

264 avaliações harmônicas: 76 pares interface/frequência, cada um em d3/d6/d8, mais 36 avaliações mistas reservadas. Dez frequências de desenvolvimento e nove reservadas por interface; faixa 130,8128–23.000 Hz. Congelamento da metade inferior de maior contribuição quadrática espacial do resíduo d3 nos pontos de desenvolvimento (arredondamento para baixo, mínimo uma direção); d6 nessas direções e d3 nas demais. Base ortonormal por porta, mesma projeção para pressão e fluxo. Não comutar durante processamento.

264/264 controles numéricos aprovados: continuidade projetada <1e-10, forma de potência inferior amostrada não negativa dentro de 1e-10 e identidade de Parseval. Máximo resíduo projetado e fino d8: 8,551235726824727e-14; menor autovalor hermitiano relativo inferior: 1,2585785647268062e-7. Não constitui certificado global.

Máximos relativos em 36 pontos reservados por configuração:
| Modelo | Pressão total % | Pressão base % | Carga % | Fluxo % | Resíduo fino % |
|---|---:|---:|---:|---:|---:|
|d3|0,620676|0,046961|1,080426|3,115257|87,334289|
|misto|0,286402|0,019104|0,514952|2,033366|81,172498|
|d6|0,055886|0,00001218|0,075488|0,491824|32,696099|

Em d3, as imagens não fundamentais f+j*48000 (módulo 384 kHz) concentram pelo menos 99,8177% da norma quadrática do resíduo nos pontos reservados. Não é energia física ou evidência de inaudibilidade. Misto melhora a pressão total em 36/36 pontos. Na interface 48, 12 de 24 direções inferiores enriquecidas: 108 incógnitas inferiores versus 72 em d3 e 144 em d6. As direções selecionadas concentram 53,04–62,47% da norma quadrática do resíduo d3 nos pontos reservados. Condicionamento máximo reservado d3/misto/d6: 5,5771/14,2299/14,2783.

Quatro ensaios temporais mistos de 128 blocos, com d8 recalculado e excitações iguais às do checkpoint anterior. Todos passam controles de trabalho/energia/projeção e trabalho acumulado não negativo na tolerância adotada.
| Caso | Pressão d3 histórica % | Misto novo % | d6 histórica % |
|---|---:|---:|---:|
|12/ruído|5,867296|1,633997|0,457660|
|12/pulso|0,006035|0,000466|0,000435|
|12/alta|0,177153|0,161475|0,034213|
|48/ruído|2,449127|1,063189|0,475671|

Resíduo fino misto no ruído de 12/48 portas: 91,7061/60,0667%. Precisão fina não aprovada. Demais transientes não repetidos. Sem benchmark de tempo real. Parâmetros de teste escolhidos nesta etapa; reservado significa não utilizado para seleção, não validação externa.

Decisão: preservar d3 prioritária, d6 e misto experimentais, d8 referência. Próximo passo: operador espacial implícito por convolução de grade e confronto com kernels arquivados, depois expansão temporal a 369 portas. Geometria piloto, 12 dependências de regeneração pendentes, sem áudio renderizado, sem promoção. O pacote local G3_Diagnostico_Espectral.zip contém scripts, resultados detalhados, logs e manifesto; este commit registra relatório resumido e hashes, não publica os binários nem os scripts integrais.
