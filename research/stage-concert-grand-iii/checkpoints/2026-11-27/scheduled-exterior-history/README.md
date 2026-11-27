# G3 — Histórico exterior escalonado

Continuação de 7ae99af. Sem alteração física, abertura integral 369 portas, 127825 estados acústicos. Cabeça direta [0,32); para entrada [e-b,e), lags [2b,4b), última partição limitada ao comprimento original L. FFT next_fast_len(b+length-1). Primeira saída e+b. Tiles espaciais disjuntos nos commits e..e+b-1, antes de qualquer saída. Histórico preservado 2b passos, anel saída L. Kernel real comprimido por rFFT temporal, simetria conjugada, dupla precisão. Sem truncar coeficientes. 42 arquivos anteriores e 18 entradas INPUTS verificados (sobreposição). Nove ensaios sintéticos: maior erro6,616354e-16, preview/reset zero.

Dois impactos Mi4 forte 3 m/s, 64 modos por corda, 720 coordenadas, 12 ms a 192/384 kHz, 6912 blocos/9216 subpassos. Captura357/713. Máximos balanço2,206291e-13, continuidade1,795165e-15, compressão1,138413e-18m, trabalho relativo5,292079e-16. Trabalho exterior acumulado mínimo zero. Força e compressão idênticas; velocidade2,534045e-14, fluxo inferior3,596274e-14, pressão fina causal4,990026e-14, completa4,688753e-14, filtrada causal4,282539e-14. Checagem direta5,048625e-17, pré-chegada1,209203e-15, prefixo FIR zero. Maior diferença de banda1,338487e-12 dB. Equivalência na mesma discretização, não revoga falhas 192 vs384. Pós-janela pressupõe fluxo zero, não cauda física.

| Taxa | Variante | Loop s | Commit p99 ms | Commit máximo ms | Bytes persistentes exterior |
|---|---|---:|---:|---:|---:|
|192k|híbrido arquivado|20,910261|27,008151|1020,852005|663433728|
|192k|escalonado|20,723433|4,640933|13,488317|301162272|
|384k|híbrido arquivado|30,785447|15,093400|1961,669601|636967168|
|384k|escalonado|29,962385|4,359999|18,601599|332971744|

Uma execução nova por taxa, sequencial, comparação com tempos arquivados, não benchmark controlado. BLAS/OMP 1 thread, Numba configurado 4 (tile serial), FFT 1 worker, aquecimento130 passos nulos/reset. Loop exclui preparação/aquecimento/gravação; memória só arrays persistentes F/X0/X1/ring/spatial/partições, não temporários nem demais estados. Picos observados, não garantia de deadline. Candidata offline, custo ainda incompatível com tempo real e cauda longa prática. Cabeça e escalonamento definidos nesta etapa. Próximo: redução passiva da carga ou compressão exata adicional, validar cauda com controle integral. Sem render, EQ, normalização individual, alteração física ou promoção. Main preservada.

Pacote local G3_Historico_Escalonado.zip, 39 entradas SHA256SUMS verificadas, ZIP íntegro. Reprodução conforme CHECKPOINT.md. Publicação parcial de módulo, relatório e hashes; demais scripts/binários locais.
