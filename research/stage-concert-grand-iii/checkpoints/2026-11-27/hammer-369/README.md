# G3 — Martelos, feltro e cordas com 369 portas

Continuação de 5c40588. 111 entradas de insumos verificadas, 35 arquivos no manifesto local. Hipótese G3-felt-memory-01 e fórmulas históricas de physical_sources.json/physical_inventory.py/felt_law.py; 70% equilíbrio, 30% memória, recuperação 1 ms, parâmetros divididos por número de cordas. Raiz de Brent na relaxação, gradiente discreto e solução coordenada do contato. Um martelo compartilhado por tecla, contato pontual e memória individual por corda, gap inicial 0,1 mm, captura do martelo recuando com perda cinética explicitamente contabilizada. Sem calibração MIDI, modelo de ação ou largura distribuída. Alvo físico de 400 coordenadas mecânicas do checkpoint anterior.

18 ensaios secos: MIDI48/60/64, velocidades 0,3 e 3 m/s, taxas 48/96/192 kHz, 8 ms. Todos capturados, balanço máximo 3,561412e-13. Comparação das duas taxas menores com 192 kHz: pior pico de força 1,681918%, impulso 0,0395675%, duração 0,03125 ms, tempo de captura 0,015625 ms. Não valida convergência espectral.

6 ensaios wet: MIDI60, 192 blocos (4 ms), d3/d7/d8, ambas velocidades. Tampo constante por intervalo, 127825 estados, 369 portas. Capturas 149/97 passos, pico total 3,2478406/44,0751473 N, duração de contato 2,791667/2,0 ms. Balanço máximo 1,971787e-13, resíduo compressão 9,757820e-19 m, força 6,395595e-11 N, trabalho contato relativo 3,514624e-16, continuidade 2,114128e-15, máximo 3 varreduras. Trabalho exterior acumulado não negativo.

| Velocidade m/s | Pior pressão fina d3 % | d7 % | Pior filtrada d3 % | d7 % |
|---|---:|---:|---:|---:|
|0,3|0,0571086|0,0073764|0,00014630|0,00002309|
|3|0,1437232|0,0195017|0,00024352|0,00003804|

A primeira auditoria direta de pressão falhou por normalização pontual perto de zero; repetida com norma do sinal completo, resíduo máximo 5,052303e-17. Sinais inalterados. Convolução com fluxo zero após janela, não cauda real. D8 referência da abertura, não da mecânica fina. Filtro Kaiser 617 taps diagnóstico. Ambos d3 e d7 passam o limite exploratório de 1% nestes dois impactos, sem revogar falhas anteriores. Sem render, afinação, sustentação, aprovação geral ou promoção.

Reprodução no ZIP local G3_Martelos_369.zip, 35 entradas SHA256SUMS conferidas e teste ZIP aprovado. Uma thread BLAS/OMP/Numba; pastas irmãs G3_consolidacao_20261127, G3_Acoplamento_369, G3_Observadores_369. Executar hammer.py --mode dry, depois --mode wet --d 3 --blocks 192 e repetir d7/d8; audit.py. Próximo: convergência espectral e energética do ataque com taxa mecânica mais fina, ampliar notas/duração. Este commit publica relatório e hashes, não os scripts completos ou binários. Main preservada.
