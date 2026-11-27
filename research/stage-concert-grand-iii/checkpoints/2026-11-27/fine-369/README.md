# G3 — Referência fina de 369 portas e compactação espectral
Continuação de G3_Acoplamento_369. 20 entradas do manifesto anterior e cinco insumos físicos verificadas. Cavidade arquivada de 127.825 estados; 80 fluxos superiores prescritos em d3, 289 inferiores; comunicação 48 kHz, referência 384 kHz. Sem observador completo, render, integração mecânica ou promoção.

Fine369: solve causal de 289 incógnitas por subpasso (equivalente à abertura d8), LU fatorada uma vez, condição 1,00940939. Replay dos fluxos d3 arquivados, não nova resolução d3. Mesma excitação superior. 64 intervalos de cada caso, 6 avaliações, 512 subpassos por caso. Parte imaginária relativa do kernel espacial 2,25815e-17 descartada por simetria par. Apenas lags alcançáveis no prefixo, sem truncamento dentro dele.

| Caso | Erro fluxo inferior % | Erro carga fina % | Erro carga projetada % | Resíduo fino d3 % |
|---|---:|---:|---:|---:|
|Ruído|6,994200|3,158680|0,168051|76,909361|
|Pulso|0,003933|0,002398|0,000222|0,469056|
|Alta|0,284222|0,117546|0,007395|26,671250|

Normas L2, referência discreta, não erro audível. Resíduo d8 máximo 1,086851e-13; energia 1,604744e-17; trabalho final 1,293688e-15; replay de carga/exterior até 2,828380e-15; resíduo projetado d3 1,837788e-13. Trabalho de d3 não conserva em todo prefixo fino (máximo 0,001289988); conserva no final do ensaio, fronteiras individuais não revalidadas nesta etapa. D8 conserva em prefixos finos até 1,429626e-15.

CompactStream: espectro espacial real, história circular em dois segmentos, acumulação Numba. 320 intervalos de ruído arquivado, mesma entrada, aquecimento de dois intervalos e reset, uma thread. Erro entre variantes 6,824648e-16, após preenchimento 8,873423e-16, versus exterior arquivado 1,543718e-15. Kernel 161.239.680 -> 80.619.840 bytes; histórico inalterado 53.746.560 bytes; total kernel + histórico -37,5%. Média 24.785,21 -> 8.719,02 us; após preenchimento 46.854,78 -> 14.939,23 us (19 intervalos). Não inclui compilação, preparação, campos e temporários; ensaio único, ordem fixa, exterior isolado, não tempo real nem circuito fechado. Primeira variante sem Numba excedeu limite em 640 intervalos, log preservado; baseline apenas concluído.

Reprodução com Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0 / Numba 0.65.1; uma thread BLAS/OMP/Numba. Usar pacote G3_Referencia_Fina_369.zip, que inclui módulos irmãos, hashes, resultados e sinais. Validar os manifestos antes de execução. Comandos:
```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python fine369.py /raiz/restaurada /pasta/G3_Acoplamento_369 --blocks 64
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python compact_stream.py /pasta/G3_Acoplamento_369
```
Este commit não publica binários ou todos os módulos irmãos. Manter d3 prioritária; d6/mista experimentais; d8 referência. Próximo: circuito fechado com CompactStream, particionamento temporal dos espectros e redução modal passiva. Observadores e 12 dependências de regeneração ainda pendentes. Geometria piloto, parâmetros de teste definidos nesta etapa.
