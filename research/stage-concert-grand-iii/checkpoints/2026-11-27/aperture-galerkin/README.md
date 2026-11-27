# G3 — Projeção espacial passiva da abertura inferior

Continuação de 715cdce. Mantidos parâmetros físicos, tampo 80, 127825 estados acústicos e kernels de radiação. A projeção real fixa u=(S v,V w), V^T y_b=0 preserva o trabalho conjugado v^T S^T y_a. A passividade do operador original é preservada por congruência com histórico e condições iniciais consistentes; não há prova de precisão nem continuidade integral. Sem refit polinomial.

Base estreita: SVD de respostas inferiores reais/imaginárias para 80 entradas superiores, 19 frequências 80–600 Hz, ranks 8/16/24/32/48/64/96/128/192/289. 84 pontos de comparação, 840 avaliações. Base ampliada: 31 frequências 45–2400 Hz, ranks 96/128/160/192/224/256/289, 87 pontos, 609 avaliações, incluindo 16 frequências 2500–24000 Hz. Grades de médias geométricas, três regiões e oito polos Mi4. Máximos ortogonalidade 3,686244e-14, continuidade projetada 3,978599e-15, reciprocidade 5,977267e-15, replay rank289 3,001301e-14. Mínimo autovalor hermitiano normalizado da carga 2,953465e-11 nos 1449 casos. Rótulo literal 64 no log amplo corresponde ao rank160, JSONs corretos.

Rank96 estreito: 289->96 incógnitas inferiores (-66,78%); 369->176 portas. Maior erro regional da carga 0,0007859%, pressão coletiva 0,003533%; observador amplo 45–2400 Hz 15,2286%. Base ampliada rank224/256: erro do observador na grade intermediária 0,606522/0,170222%, acima de 2,4 kHz 4,074757/2,100080%. Nenhuma redução aprova globalmente.

Mi4 forte 3 m/s, 12 ms, 64 modos por corda, 192 kHz, m2 integral, rank96 estreito vs referência arquivada integral com mesma discretização. 2304 blocos, 4608 subpassos, 720 coordenadas mecânicas. Captura passo357, pico45,215355 N, balanço7,694668e-14, continuidade projetada1,352667e-15, mínimo trabalho exterior zero. Erro força2,392998e-15, velocidade0,003759%, fluxo superior0,010008%, inferior6,577498%. 
| Indicador | Mic1 | Mic2 |
|---|---:|---:|
|Fino causal %|2,391844|2,847778|
|Fino completo %|2,182229|2,109438|
|Filtrado causal %|2,394975|2,745511|
|Nível causal dB|-0,018506|+0,012838|
|Banda máx dB|0,239780|0,556245|
Passa conservação e limites 1/3 dB; reprova critério fino 1% nos dois receptores. Checagem direta 5,049e-17, pré-chegada1,05401e-15, prefixo FIR idêntico. Pós-janela pressupõe fluxo zero, não cauda física. Loop 38,626 s contra histórico 32,564 s, execução atual em paralelo com triagem ampla, comparação não controlada. Não demonstrou ganho de desempenho; FFT espacial não diminui custo dominante do histórico. Não promover, preservar abertura integral. Nenhuma alteração física, render, EQ, normalização, aprovação de cauda ou tempo real. Próximo: reduzir custo da memória/carga passiva e validar cauda longa, com controle integral.

Pacote local G3_Abertura_Projetada.zip, 45 entradas SHA256SUMS, 17 INPUTS, 60 entradas do checkpoint regional e 24 do Mi4 conferidas (sobreposições). ZIP íntegro. Reproduzir screen.py, screen_wide.py, wet_projected.py --rate 192000 --partials 64 --speed 3 --ms 12 --key 64 --parallel, audit_wet.py, verify.py; uma thread BLAS/OMP e quatro Numba no wet. Este commit publica relatório e hashes, scripts completos e binários no pacote local. Main preservada.
