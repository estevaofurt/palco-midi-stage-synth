# G3 — Primeiro acoplamento temporal de 369 portas

Cavidade e exterior físicos arquivados, 80 fluxos superiores prescritos, 289 inferiores resolvidos implicitamente. Normalização corrigida, d3 a 48 kHz, 8 subpassos a 384 kHz. 63.913 termos modais (um modo de frequência zero), 127.825 estados físicos. Geometria piloto 30×30. Não inclui integração mecânica, observador completo, render sonoro ou aprovação para tempo real.

Agrupamento por 1800 canais DCT/paridade; integração exata de entrada mantida, coeficientes modais e amortecimento preservados. Condensação temporal por congruência; sistema inferior de 867 incógnitas fatorado por LU uma vez, número de condição 1,1228564209921257. Memória exterior de 301 intervalos recebe a entrada após resolver o fluxo inferior. Tolerância 1e-10 nos resíduos e mínimos acumulados normalizados.

| Caso | Intervalos | Energia | Trabalho | Continuidade projetada | Exterior versus lote |
|---|---:|---:|---:|---:|---:|
| Ruído |320|9,6914e-18|1,2199e-15|1,1454e-15|1,5549e-15|
| Pulso |128|4,0052e-18|4,9098e-16|4,0842e-15|2,6873e-15|
| Alta |128|2,9401e-18|4,0121e-16|1,8419e-15|1,2711e-15|

3/3 ensaios passaram; 576 intervalos, 4.608 subpassos. Nenhum trabalho acumulado negativo observado. Ruído ultrapassou os 301 intervalos da memória; 19 intervalos após preenchimento. Comparação de incidência, matriz instantânea, saída, história, perda e energia com cavidade densa de 48 portas e operador exterior arquivado: máximo 6,10e-13 (perda); saída 3,03e-15. Regressão de 48 portas em circuito fechado: 24 intervalos de ruído, seed 271130, erro relativo de fluxo 5,481388407531468e-16, de carga 1,35785487571174e-15 e de termo instantâneo 1,2088491206833266e-15. A referência exterior de 369 portas usa a mesma malha, não geometria independente.

Tempos brutos de loop: 13,598 s (320); 3,494 s (128); 3,305 s (128). Não incluem preparação, comparação em lote ou escrita; houve concorrência entre execuções, portanto não constituem benchmark controlado. Muito acima de 20,833 us/intervalo. Continuidade fina não medida nesta etapa. Observadores completos ausentes, 12 dependências de regeneração pendentes. Sinais armazenados são fluxos e cargas projetados, não áudio.

## Reprodução
Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. Use o pacote local G3_Acoplamento_369.zip e raiz de pacotes restaurados; confira LOCAL_ARTIFACTS.sha256 no pacote e INPUT_SHA256SUMS na raiz. Execute apenas sobre fontes verificadas. Uma thread BLAS/OMP; runner reutiliza definições por extração AST.
```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python coupled369.py /raiz/restaurada grid-b64.npz --kind noise --blocks 320
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python coupled369.py /raiz/restaurada grid-b64.npz --kind pulse --blocks 128
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python coupled369.py /raiz/restaurada grid-b64.npz --kind high --blocks 128
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python regression48.py /raiz/restaurada grid-b64.npz
```
Seed 271129; pulso senoidal amortecido 329,6276 Hz; seno 7851,2 Hz. Parâmetros experimentais definidos nesta etapa. Sem alteração de amortecimento ou geometria. Este commit publica relatório e hashes, não os binários nem o runner completo.

## Decisão
Manter d3 prioritária, d6/mista experimentais, d8 referência. Próximo: referência fina de 369 portas, ampliar duração e casos, recuperar observadores, otimizar estado modal e memória espacial; somente depois integrar mecânica e avaliar ataque/afinação/cauda. Nenhuma promoção para main.
