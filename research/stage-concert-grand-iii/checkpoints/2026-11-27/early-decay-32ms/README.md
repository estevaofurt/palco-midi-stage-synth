# G3 — Cauda física inicial do Mi4, 32 ms
Continuação de e175f869. Checkpoint anterior 39 entradas SHA256SUMS e 18 INPUTS verificadas; 21 dependências no novo checkpoint (sobrepostas). Mi4 forte 3 m/s, 64 modos por corda, 720 coordenadas mecânicas, tampo 80, abertura integral 369 portas, 127825 estados acústicos, midpoint 384 kHz, histórico escalonado cabeça32, 2398 atrasos. 12288 passos em 32 ms. Captura 713 (1,856771 ms), pico45,202138 N, força nula após captura. Balanço4,963243e-13, continuidade1,087901e-15, compressão9,757820e-19 m, trabalho relativo4,750762e-16; mínimo trabalho exterior acumulado zero. Prefixo de 12 ms idêntico em força/compressão/velocidade/fluxo; pressão erro relativo até3,411490e-15, filtrada até2,879653e-15. Convolução direta4,303771e-17, pré-chegada9,008665e-16, prefixo FIR zero. Reconstrução de energia mecânica por velocidades e midpoint: erro final zero.
| Fim ms | Energia mecânica J | Fração energia inicial % | RMS filtrado mic1/mic2 Pa |
|---:|---:|---:|---|
|4|0,020732102|54,47917|0,006230/0 (ruído numérico)|
|8|0,020135597|52,91170|0,636704/0,079671|
|12|0,019342255|50,82698|0,797802/0,322627|
|16|0,018529964|48,69246|0,928622/0,339854|
|20|0,017780292|46,72250|0,752356/0,338257|
|24|0,017055518|44,81796|0,911881/0,365662|
|28|0,016447258|43,21959|0,581147/0,446717|
|32|0,015828426|41,59345|0,510759/0,201870|
Convolução finita truncada aos 12 ms termina antes de 18,348959 ms. Trecho causal posterior até 32 ms apresenta RMS fino 0,685592/0,340387 Pa e 40,82243/55,04292% da norma quadrática causal dos receptores; não energia radiada. Filtro Kaiser617 taps, atraso0,802 ms. Energia mecânica/cavidade final 0,015828426/5,977268e-7 J. Perdas mecânica/cavidade/feltro/captura 0,005073378/2,973483e-7/0,000155808/0,016890024 J; trabalho exterior0,000106565 J.
Loop79,182506 s, commit p99 3,981610 ms e máximo37,025735 ms; memória persistente exterior332971744 bytes, execução única. Não tempo real. Janela e resolução escolhidas nesta etapa; não demonstram convergência modal da cauda nem T60 de segundos. Polos analíticos anteriores usaram 128 modos, não validados aqui. Preservar referência e investigar redução passiva, controle temporal da cauda e polos. Nenhuma alteração física, render, EQ, normalização ou promoção. Main preservada.
Pacote local G3_Cauda_Inicial_32ms.zip, 35 entradas SHA256SUMS verificadas, ZIP íntegro e hashes internos confirmados. Reprodução conforme CHECKPOINT.md: wet_scheduled.py --rate 384000 --partials 64 --speed 3 --ms 32 --key 64 --hybrid --head 32; audit_tail.py. Este commit publica relatório e hashes, scripts e binários no pacote local.
