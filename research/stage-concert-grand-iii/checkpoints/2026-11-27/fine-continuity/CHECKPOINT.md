# G3 — Continuidade fina da abertura acústica (27/11/2026)

Reprodução de operadores físicos arquivados (normalização corrigida), 127.825 estados da cavidade. Tampo d3 fixo, abertura d3/d6/d8, comunicação 48 kHz, oito subpassos a 384 kHz. 6/12 portas b16; 24/48 b64. 128 intervalos por ensaio. Excitações: ruído nos coeficientes (seed 294), pulso senoidal amortecido 329,6276 Hz, seno 7851,2 Hz. Referência d8 mantém d3 no tampo.

36 casos únicos concluídos, todos satisfazem critérios de resíduo projetado, energia e trabalho <1e-10 e trabalho acumulado não negativo dentro de 1e-10; continuidade fina d8 <1e-10. Máximos observados: projetado 7,11990377579047e-14; energia 3,5204904651448714e-17; trabalho 1,9075584546907997e-16; continuidade fina d8 7,119903775790471e-14.

| d | resíduo fino máximo % | erro pressão máximo % | erro carga máximo % | erro fluxo máximo % |
|---|---:|---:|---:|---:|
|3|94,889248|5,867296|5,936436|31,270514|
|6|79,394793|0,475671|0,978277|8,364175|
|8|~0|0|0|0|

Resíduo fino: norma L2 do resíduo inferior / soma das normas das pressões inferiores. Erros de pressão, carga, fluxo: normas relativas L2 frente a d8. Não são erros máximos por amostra nem métricas audíveis. Ruído de 48 portas: d3/d6 pressão 2,449127/0,475671%, carga 2,938193/0,776672%, resíduo fino 70,270030/32,457446%.

Método: projeção mista J, congruência J^T K J dos lags causais alcançáveis, LU inferior, reprodução fina exterior/receptores via FFT. Python 3.13.5, numpy 2.3.5, scipy 1.17.0, uma thread BLAS/OMP. O comando de 48 portas sofreu timeout após ruído completo e pulso d3; pulso e alta frequência repetidos separadamente. Preservada a falha. Nenhum render sonoro.

Decisão: d3 permanece prioritária, d6 alternativa experimental, d8 referência. A continuidade projetada não comprova precisão fina. Não promover candidato; próxima etapa decompor resíduo por frequência e coordenada e investigar operador exterior espacial implícito. Geometria piloto, apenas até 48 portas acopladas temporalmente, 12 dependências da regeneração ainda ausentes.

O pacote local G3_Continuidade_Fina.zip contém compare.py, replay.py, resultados, logs, manifestos e relatório integral. Os hashes abaixo identificam arquivos locais; este commit registra o relatório e os hashes, não publica o ZIP nem o código compare.py. Não há validação de tempo real.
