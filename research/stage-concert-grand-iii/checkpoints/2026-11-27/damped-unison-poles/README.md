# G3 — Polos amortecidos e uníssonos acoplados
Continuação de d815853. Hipótese física original inalterada, 128 modos por corda, 10 cordas, 80 coordenadas do tampo, 369 portas, 127825 estados acústicos, midpoint e abertura integral a 384 kHz. Uma tecla mantida, abafadores estacionários. Oito modos conservativos com indicador da primeira forma interna >=0,5, MIDI48/60/64. Extensão complexa f=fr+i fi, z=exp(2 pi i f/FS), s=2i FS tan(pi f/FS); K+sD+s²M mais s vezes impedância acústica efetiva. Condensação exata dos modos internos acima do primeiro por corda, 90 coordenadas mantidas. Raiz da equação bordada com vetor da forma conservativa, repetida com perturbação +0,015+i0,01 Hz. Todos os oito polos secos/acoplados apresentam fi>0 e passam os critérios locais. Máximo resíduo mecânico 4,947882e-16, diferença entre raízes repetidas 5,732087e-14 Hz. Verificação independente de 1649 incógnitas (1360 mecânicas e 289 abertura): máximo resíduo escalado 4,644367e-14 e continuidade 1,949255e-14.

| MIDI | Frequência seca Hz | Frequência acoplada Hz | T60 seco s | T60 acoplado s | Projeção mic1 / norma de massa da velocidade |
|---:|---:|---:|---:|---:|---:|
|48|130,498022|130,342322|2,848326|2,992109|1,603976|
|48|131,230134|131,230002|64,957997|65,451958|0,054354|
|60|261,187836|261,100837|6,837943|6,650933|2,330062|
|60|261,553772|261,551292|46,465790|49,963544|0,402597|
|60|261,725759|261,723896|50,428|52,742|0,344682|
|64|326,527881|325,989204|1,544540|1,105741|4,286758|
|64|329,520416|329,521066|51,557751|51,576336|0,141220|
|64|329,740340|329,740898|51,844965|52,163017|0,139869|

T60 modal=3 ln(10)/(2 pi fi). Modos lentos projetam no receptor 1 cerca de 3,39% (Dó3), 17,28/14,79% (Dó4), 3,29/3,26% (Mi4) da projeção do respectivo modo rápido, sob norma de massa unitária da velocidade. Não é coeficiente de excitação pelo martelo, eficiência de radiação ou medida de duração audível. Comparação de modos locais não prova estabilidade global. Não alterar tensão, amortecimento ou rigidez com base nestes resultados isolados. Próximo: resíduos da transferência e excitação pelos martelos, envelope de decaimento, verificação temporal longa. Nenhum render, EQ, normalização de áudio, alteração física ou promoção. Main preservada.

Pacote local G3_Polos_Amortecidos.zip: 15 entradas SHA256SUMS e sete entradas INPUTS.sha256 verificadas, ZIP íntegro. Reprodução conforme CHECKPOINT.md: executar poles.py e verify.py com uma thread BLAS/OMP e dependências históricas. Parâmetros de busca definidos nesta etapa. Este commit publica relatório e hashes; scripts e resultados completos permanecem no pacote local.
