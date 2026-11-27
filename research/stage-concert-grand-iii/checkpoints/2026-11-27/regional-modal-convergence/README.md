# G3 — Convergência regional e frequências naturais
Continuação de a9ebb1d. 161 entradas dos manifestos verificadas. Quatro impactos fortes de 12 ms: Mi4 96/384, 64/384, 64/192 e Dó3 96/384. 18432 subpassos, 369 portas, 127825 estados acústicos, tampo de 80 coordenadas, dez cordas. Parâmetros físicos preservados. Todos capturados. Máximo balanço 7,817318e-13, continuidade 1,741565e-15, compressão 2,168404e-18 m, força 9,653833e-12 N, trabalho relativo 7,554462e-16; mínimo trabalho exterior acumulado zero.
| Comparação | Fino causal mic1 % | mic2 % | Maior banda dB |
|---|---:|---:|---:|
| Dó3 64/384 vs 96/384 |1,457010|0,545590|0,184360|
| Dó3 64/192 vs 96/384 |1,414287|1,065318|0,171898|
| Dó3 64/192 vs 64/384 |0,449063|0,938042|0,051741|
| Mi4 64/384 vs 96/384 |0,085089|0,084290|0,011708|
| Mi4 64/192 vs 96/384 |0,794151|1,219448|0,071076|
| Mi4 64/192 vs 64/384 |0,800393|1,220262|0,060464|
12/12 receptores passam critério espectral; 7/12 passam pressão fina causal 1%, 10/12 na convolução finita. Dó3 reprova redução modal de 96 para 64, com erro predominantemente abaixo de 24 kHz. Mi4 passa redução modal, mas reprova temporal no segundo receptor. Consolidando checkpoints anteriores, 3/4 ataques passam redução 64/384 vs 96/384. Não adotar rank uniforme nem 192 kHz globalmente. Filtro Kaiser 617 taps/48 kHz, atraso 0,802 ms; bandas significativas >=1e-4 da norma quadrática de referência em 0–20 kHz. Convolução finita não é cauda natural.
Nove problemas secos conservativos K V = M V lambda em MIDI48/60/64 e 64/96/128 modos por corda, faixa ±100 cents. Frequências ordenadas, contagem constante 4/9/10. Máxima diferença 64 vs 128 em cents 7,06557e-7 / 1,26174e-5 / 1,30951e-5; resíduo máximo 1,553684e-10, ortogonalidade de massa 3,63650e-15. Não mede ressonâncias amortecidas, pressão ou afinação percebida. 128 é limite da base interna existente, não prova de convergência espacial contínua.
Próximo: 128 modos no Dó3, redução regional e picos harmônicos com carga acústica. Parâmetros de ensaio escolhidos nesta etapa, sem render, EQ, normalização ou promoção. Pacote G3_Convergencia_Regional.zip: 60 entradas SHA256SUMS, 61 entradas ZIP, reprodução em CHECKPOINT.md. Publicação parcial dry_modes.py, relatório e hashes; main preservada.
