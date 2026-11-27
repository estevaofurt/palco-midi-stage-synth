# G3 — Histórico híbrido exato da radiação exterior

Continuação de 0bd292a. Abertura integral 369 portas, 127825 estados acústicos, parâmetros físicos inalterados. Cabeça direta [0,32), cauda em partições diádicas [b,2b) com FFT temporal complexa, simetria espacial e paridade preservadas. Saídas agendadas após fechar o bloco de entrada; sem truncar coeficientes. Cinco casos sintéticos d1/d2/d3 e L1/7/9/17/35, voltas de anel, preview e reset: erro máximo 3,823019e-16, preview/reset zero. Corrigidos erros iniciais de subtração de listas e tipagem Numba do índice. 45 arquivos e 17 insumos do checkpoint anterior, 12 entradas diretas e dois arquivos regionais conferidos (sobreposição).

Quatro impactos fortes Mi4, 3 m/s, 64 modos por corda, 720 coordenadas, 12 ms a 192/384 kHz, abertura integral, 18432 subpassos acústicos. Aquecimento de 130 passos nulos e reset. Capturas 357/713, forças de pico 45,215355/45,202138 N. Máximos balanço integrado 2,266463e-13, continuidade 1,783867e-15, compressão 1,138412e-18 m, trabalho relativo 5,292079e-16. Trabalho exterior acumulado mínimo zero. Força/compressão idênticas; velocidade 2,832857e-14, fluxo inferior 3,467514e-14, pressão fina causal 5,132528e-14, completa 4,804996e-14, filtrada causal 4,517693e-14. Controles diretos 5,048625e-17, pré-chegada 1,209203e-15, prefixo FIR zero. Maior diferença de banda 1,676966e-12 dB. Equivalência na mesma discretização, não revoga reprovações históricas 192 vs 384 kHz. Pós-janela pressupõe fluxo zero, não decaimento natural.

| Taxa | Variante | Loop s | Histórico médio ms | Commit médio ms | Commit p99 ms | Commit máximo ms | Bytes persistentes exterior |
|---|---|---:|---:|---:|---:|---:|---:|
|192k|parallel|25,855500|4,774782|0,827783|1,516458|5,404026|162489600|
|192k|hybrid|20,910261|0,746460|2,921816|27,008151|1020,852005|663433728|
|384k|parallel|46,970094|4,673484|0,677030|1,369898|25,313829|179600608|
|384k|hybrid|30,785447|0,423616|2,255708|15,093400|1961,669601|636967168|

Uma execução por configuração, uma thread BLAS/OMP e quatro Numba, FFT workers=4. Auditoria arquivada executada durante comparação paralela 384 kHz; possível interferência no tempo. Não benchmark controlado. Loop exclui preparação, aquecimento e gravação. Memória só F/X0/X1/partições/anel de saídas, sem temporários e demais estados. Redução 19,126%/34,457%, ganho 1,2365x/1,5257x. Memória aumenta 4,083x/3,547x, picos de atualização acima de 1 s. Candidata offline, não promover ao motor em tempo real. Caudas longas ainda não validadas. Próximo: redução de memória, escalonamento das FFTs ou aproximação passiva de carga, com controle integral. Nenhum render, EQ, normalização individual, alteração física ou promoção. Cabeça e parâmetros de ensaio escolhidos nesta etapa. Main preservada.

Pacote G3_Historico_Hibrido.zip: 42 entradas SHA256SUMS verificadas, ZIP íntegro. Reprodução conforme CHECKPOINT.md. Publicação parcial do módulo, relatório e hashes, demais scripts e binários locais.
