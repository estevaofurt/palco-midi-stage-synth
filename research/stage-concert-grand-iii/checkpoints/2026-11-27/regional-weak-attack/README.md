# G3 — Ataque fraco refinado e validação regional do Dó3

Continuação de 79811bf. 153 entradas de manifestos de insumos e checkpoint conferidas, quatro entradas de dependência dos sinais anteriores reconferidas. Três novos impactos de 12 ms: Dó4 fraco 0,3 m/s 96 modos/384 kHz; Dó3 forte 3 m/s 64 modos/192 e 384 kHz. 13.824 subpassos acústicos, 80 coordenadas estruturais, dez cordas, 369 portas e 127.825 estados acústicos. Parâmetros físicos mantidos. Abertura integral e tampo constante no intervalo mecânico. Runner aceita MIDI48/60/64, nomes de saída incluem a tecla. Mi4 não ensaiado nesta etapa.
Todos capturados. Máximos energia 5,518236e-13, continuidade 2,784732e-15, compressão 1,897354e-18 m, força 9,999890e-12 N, trabalho de contato relativo 5,900381e-16. Mínimo trabalho exterior acumulado zero. Dó4 pico 3,241343 N, contato 2,763021 ms, captura 3,096354 ms. Dó3 192/384 pico 29,835532/29,827291 N, contato 3,34375 ms e captura 3,375 ms. Tempos locais 56,4143/31,1940/49,0492 s, sem benchmark controlado.
| Caso | Mic | Fino causal % | Fino completo % | Filtrado causal % | Nível causal dB | Banda máx dB |
|---|---:|---:|---:|---:|---:|---:|
|Dó4 fraco 64/384 vs 96/384|1|0,139803|0,131908|0,131737|+0,007321|0,013751|
|Dó4 fraco 64/384 vs 96/384|2|0,120842|0,127553|0,120015|+0,005103|0,012737|
|Dó4 fraco 64/192 vs 96/384|1|0,551097|0,553048|0,172535|+0,005851|0,014940|
|Dó4 fraco 64/192 vs 96/384|2|1,295730|0,873538|0,114256|+0,004844|0,025235|
|Dó3 forte 64/192 vs 64/384|1|0,449063|0,397368|0,181869|-0,000350|0,051741|
|Dó3 forte 64/192 vs 64/384|2|0,938042|0,675446|0,135351|-0,000111|0,027844|
Seis de seis passam 1 dB global/3 dB banda, cinco de seis passam 1% fino causal, seis de seis fino completo. Dó4 64/384 passa fraco e forte frente a 96/384; Dó3 64/192 passa frente a 64/384 neste caso, sem referência de 96 modos. Dó4 192 kHz reprova receptor 2. FIR Kaiser 617 taps, atraso 0,802 ms, bandas significativas >=1e-4 da norma quadrática 0–20 kHz. Checagem direta máxima 7,882506e-17, pré-chegada 1,133675e-15. Convolução após janela pressupõe fluxo zero, não cauda natural.
Parseval verificado em quatro bandas. Fração do erro quadrático acima de 96 kHz receptores 1/2: Dó4 modal 0,0006295/0,0033408%; Dó4 64/192 vs 96/384 87,5337/99,1570%; Dó3 192 vs 384 80,7682/97,8922%. Dó4 modal concentra erro abaixo de 24 kHz; diferenças envolvendo 192 kHz predominam acima de 96 kHz. Não revogar critério físico de 1%. Sem render, EQ, normalização ou promoção. Próximo: Mi4, referência de 96 modos Dó3, afinação e decaimento. Parâmetros de ensaio definidos nesta etapa.
Pacote local G3_Validacao_Regional_Ataque.zip, 46 entradas SHA256SUMS verificadas e ZIP íntegro, reprodução no CHECKPOINT.md. Publicação parcial de runner, auditoria de bandas, relatório e hashes; demais módulos e binários no pacote local. Main preservada.
