# G3 — Convergência modal do ataque acoplado
Continuação de 522106e. 205 entradas de manifestos conferidas, 42 arquivos locais verificados. Três novos impactos de Dó4, 12 ms cada: 96 modos por corda a 384 kHz forte (3 m/s), 64 modos a 384 e 192 kHz fraco (0,3 m/s). Mesma escala, feltro, terminações, 10 cordas, tampo de 80 coordenadas, 369 portas, 127.825 estados acústicos. Abertura integral. Todos capturados; 13.824 subpassos acústicos. Máximos balanço 5,359109e-13, continuidade 2,216751e-15, compressão 1,192622e-18 m, trabalho de contato relativo 5,974168e-16. Trabalho exterior acumulado mínimo zero. Prefixo fraco de 4 ms reproduzido: fluxo 1,312786e-14, velocidade 5,853931e-15, força 3,118584e-17, compressão 1,708609e-16. Pico força forte 43,383801 N; fraco 3,242186/3,242181 N. Tempos de loop locais 55,893/50,523/31,322 s, não benchmark controlado.
| Caso | Mic | Fino causal % | Fino completo % | Filtrado causal % | Nível causal dB | Banda máx dB |
|---|---|---:|---:|---:|---:|---:|
|64/384 forte vs 96/384|1|0,288343|0,284912|0,275533|+0,001598|0,168356|
|64/384 forte vs 96/384|2|0,183822|0,158089|0,160067|+0,001194|0,057489|
|64/192 forte vs 96/384|1|0,650919|0,650549|0,309422|+0,000532|0,273886|
|64/192 forte vs 96/384|2|1,489207|0,955068|0,223895|+0,001041|0,048508|
|64/192 fraco vs 64/384|1|0,541531|0,542655|0,151073|-0,001471|0,009111|
|64/192 fraco vs 64/384|2|1,290472|0,865176|0,040828|-0,000259|0,017349|
FIR Kaiser 617 taps, 48 kHz, atraso 0,802 ms, bandas significativas >=1e-4 da norma quadrática espectral 0–20 kHz. Cinco sinais, checagem direta máxima 7,882506e-17, pré-chegada 1,448941e-15. Todos passam 1 dB global/3 dB banda e 1% fino completo; dois falham 1% fino causal (192 kHz receptor 2). 64/384 forte passa 1% frente a 96/384 neste caso. Fraco ainda sem referência de 96 modos. Convolução após janela assume fluxo zero, não cauda natural. Sem prova de convergência da base interna de 128 funções, sem aprovação geral, sem render, EQ, normalização ou promoção. Próximo: referência fraca de 96 modos e validação regional. Parâmetros de ensaio escolhidos nesta etapa, parâmetros físicos preservados.
Pacote local G3_Convergencia_Modal_Wet.zip, reprodução no CHECKPOINT.md. Publicação parcial: verificação do prefixo, relatório e hashes, não todos os scripts/binários. Main preservada.
