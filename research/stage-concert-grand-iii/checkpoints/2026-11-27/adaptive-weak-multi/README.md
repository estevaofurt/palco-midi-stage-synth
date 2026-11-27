# G3 — Ataque fraco adaptativo e primeiro piloto de três martelos acoplados

Continuação de f1d47f3. 55 entradas do checkpoint anterior e 111 entradas dos insumos conferidas; 64 arquivos locais verificados. Parâmetros históricos mantidos. Generalização de assembly_rank para conjunto de teclas mantidas: lista unitária reproduz cinco matrizes exatamente; M/K/P/L invariantes, diferença D conforme soma das parcelas dos abafadores removidos, resíduo 4,122809e-17, menor autovalor D 0,2053592.

Dó3 fraco: dois impactos 0,3 m/s, 12 ms a 384 kHz, abertura integral, 369 portas e 127825 estados acústicos. Uniforme 128 modos por corda (1360 coordenadas) vs adaptativo MIDI45/48/60/64=64/128/64/64 (848). Captura passo1686, pico2,178098983 N, contato4,057291667 ms, impulso0,004794736539 Ns. Máximos balanço1,494647e-13, continuidade2,221561e-15, compressão2,303930e-19m, trabalho relativo9,118553e-16. Trabalho exterior acumulado mínimo zero. Loop 75,0996/55,2393 s (26,45% menor, execução única, não benchmark).
| Receptor | Fino causal % | Fino completo % | Filtrado causal % | Filtrado completo % |
|---|---:|---:|---:|---:|
|1|0,0000705122|0,0000976188|0,0000411901|0,0000979870|
|2|0,00000196308|0,0000825000|0,00000156927|0,0000820660|
Passam 1% fino causal/completo, 1 dB global e 3 dB por banda significativa (máximo1,447334e-6 dB). Verificação direta6,53612e-17, pré-chegada8,26899e-16. FIR Kaiser617 taps, atraso0,802ms, DFT retangular, bandas significativas >=1e-4 da norma quadrática 0–20 kHz. Convolução após janela assume fluxo zero, não cauda física.

Três pares secos 48 kHz/12ms: Dó3 fraco reproduz exatamente rotina anterior; Dó3/Dó4/Mi4 velocidades 0,3/1/3 e 3/3/3 m/s, ordem inversa das raízes; captura coincidente, máximos balanço3,395765e-13, diferença força1,337749e-12, velocidade1,811479e-12. Todos capturados.

Um impacto simultâneo acoplado a 192 kHz/12ms, 4608 subpassos, abertura integral m2, 3 martelos (8 cordas excitadas, 10 no sistema), velocidades 0,3/1/3 m/s. Captura passos843/452/357, picos2,178073/12,474790/45,215355 N. Balanço2,203154e-14, continuidade1,626577e-15, compressão5,421011e-19m, trabalho relativo3,461412e-16. Mínimo trabalho exterior zero, máximo três varreduras e três martelos concomitantes. Loop35,9902 s. Auditoria direta5,097478e-17, pré-chegada8,438536e-16, prefixo filtrado zero. RMS causal0,594566/0,217662 Pa (hipótese sem calibração); fração quadrática causal56,0461/25,2726% da convolução finita. Sem comparação uniforme do acorde ou 384kHz, não aprovar precisão polifônica.

Lançamentos em t=0, gap0,1mm, abafadores estacionários, captura simplificada. Sem pedal/repetição, calibração MIDI, render, EQ, normalização individual ou promoção. Próximo: referência uniforme e refinamento temporal do acorde, afinação com carga e decaimento. Parâmetros de ensaio definidos durante desenvolvimento. Pacote local G3_Adaptativa_Fraco.zip (64 entradas SHA256SUMS e ZIP íntegro), reprodução no CHECKPOINT.md. Publicação parcial dos módulos, relatório e hashes; demais códigos e binários locais. Main preservada.
