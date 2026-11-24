# Stage Concert Grand — F7.2 observação vibroacústica integrada

Data 24/11/2026. Base 15042133bd19ab624644d61a1d9923b4377aca59. Pesquisa offline, sem WAV, sem alteração de main/V10/DSP/UI. Radiação unilateral, não acoplamento fluido-estrutura completo.

## Método
Dependências verificadas: F7.1 13c578ab598171aaf500fc2a51de68f3cecbd6fa, surface-radiation.mjs b988ea15bbdcdb7a82050df1380b61d5e3e2fb11, board-coupling.mjs c6776df1a4000a4462e326d71cbfce7f78275703, mindlin-plate.mjs 04529d4b2a981316accbc8122e6e05a643a1433a, polarized-bridge.mjs 2b5820bc5e2779ffd0c6983bcc4dc10f8f768719. Preservar dinâmica e hipóteses F6.4. Aceleração média modal a=(v1-v0)/h, amostra representativa do centro do passo. Conferida diretamente pela evolução modal F2.2 com estado inicial salvo, força generalizada -F_ligacao*w e coeficientes H,D,J. Não é aceleração instantânea no fim do passo. As amostras representam uma média temporal, com resposta de janela associada; não aplicar correção artificial. Convolução offline por kernels geométricos F7.1 e zero padding, paridade com SurfaceRadiator conferida. O registro de 12 ms é interrompido, a cauda de propagação não representa decaimento completo; não usar esta série como áudio final. RMS inclui atraso inicial e cauda de convolução.
Energia acústica de diagnóstico em semiespaço de anteparo infinito, ar rho=1,204 kg/m³, c=343 m/s. Referência https://www.sciencedirect.com/science/article/pii/S0022460X0400063X e https://euphonics.org/4-3-2-the-rayleigh-integral-and-the-baffled-piston/. No campo distante, pressão vezes distância = rho/(2*pi)*integral a(s)*exp(+i*k*n_dot*s)dS, omitida fase comum de distância. Integral espacial dos senos via J(b)=L*sinc(bL/2)*exp(i*bL/2), I_m=[J(k+m*pi/L)-J(k-m*pi/L)]/(2i). Somar amplitudes complexas coerentes antes do quadrado. Integração angular de ponto médio em mu=cos(theta) em [0,1] e azimute em [0,2pi]. DFT de aceleração média, janela unitária até 75% do registro e cosseno até zero no final; padding até potência de dois >=2*len. Parseval unilateral 2/(N*fs) para bins positivos, metade no DC, Nyquist excluído; multiplicar rho/(4*pi²*c) e peso angular. Soma em bins até 2 kHz; estimativa do trecho finito modificado pela janela, não energia da nota inteira, nem pressão calibrada. A DFT e quadratura finitas não garantem exatidão contínua. Sem radiação de face inferior, tampa, caixa, sala, difração ou reação do fluido. Não subtrair energia estimada do balanço mecânico, nem ajustar perdas estruturais para mascarar deficiência.

## Resultados
Base Mindlin original 4 kHz, 140 modos ativos abaixo de 1,5 kHz, 96 kHz, 12 ms; ouvinte lateral x=1,05 y=0,38 z=1 m; malha 64x50.
| v m/s | pico pressão Pa | energia inicial J | perda modal tampo J |
|---:|---:|---:|---:|
|0,5|0,259012460|0,00125|1,78459762e-6|
|1|0,635900306|0,005|9,50918222e-6|
|2,5|1,796258994|0,03125|7,17817703e-5|
Pico forte/suave ~6,93. Não implica dB SPL de um piano real.
| posição x,y,z m | pico Pa | RMS Pa |
|---|---:|---:|
|0,7;0,55;1|0,430399810|0,097146139|
|1,05;0,38;1|0,635900306|0,167449769|
|0,7;0,55;2|0,211081567|0,044057771|
Regressão F6.4: energia tampo 0,3397351744967451 mJ após 12 ms; resíduo global 8,58515e-15 J, aumento observado zero, pico força 11,546166573 N. Erro máximo da equação de aceleração média 2,09610e-13 sqrt(kg)*m/s². Paridade convolução offline/streaming zero observado. Refinamento de malha 64x50 vs 128x101: erro relativo L2 de pressão 0,403902%. Comparação temporal 48 vs 96 kHz (média de pares da referência 96 kHz, sem filtro anti-alias ideal): 7,239898%; não é erro contra solução exata, inclui integração mecânica e atrasos. Ampliação corte ativo 1,5 para 2 kHz (140 para 211 modos), mesma base original e taxa: erro L2 20,652709%. A resposta acústica é muito mais sensível que energia mecânica agregada; estes resultados NÃO passam um gate de convergência de banda completa. Registros interrompidos afetam métricas. Reavaliar com registro longo, referência temporal e banda maior.
Energia estimada do trecho janelado, N=4096, resolução 23,4375 Hz, último bin 1992,1875 Hz:
| mu x azimute | energia microJ |
|---|---:|
|6x12|6,859400947|
|12x24|6,750908633|
|18x36|6,715168837|
Diferença 12x24 vs 18x36 ~0,53%. Valor último equivale a 0,1343% da energia cinética inicial de 5 mJ, apenas comparação de escalas. Perda estrutural do tampo no registro não janelado 9,509182 microJ, perda mecânica total 194,812527 microJ. Não interpretar razão entre essas grandezas como eficiência ou perda radiativa já contabilizada. A ordem de grandeza da radiação frente à perda do tampo motiva estudo de reação do ar. Nenhuma correção de amplitude por nota ou parcial aplicada.

## Testes e decisão
11 verificações iniciais e uma adicional de escala quadrática, 12/12 em V8. Reexecutadas com fontes recuperados do GitHub e reforço da verificação de aceleração (salvar deslocamento inicial real, em vez de reconstruí-lo pelo estado final), validação de entradas de energia e escala quadrática. Commits c8305d0606c27e46d94a0a25da9255dfb36988b6, f10585e64d1551eb5affd79ed2e4ce430644e46e, ffa065a47ecd4109058ef563fe3772cf0b9374c7, de1821204df576d4371a7f1cc606228600a7fb54. Reprodução: node research/stage-concert-grand/vibroacoustic-observer.test.mjs. Sem nova CI Node ou hardware.
F7.2 concluída no escopo de observador unilateral. F7.3 próxima por decisão técnica: estudar resistência de radiação matricial passiva e reação do ar (incluindo distinção entre resistência e reatância), não somar perdas sem justificar; estabelecer referência de convergência temporal e de banda para pressão. Evitar declarar F7 completa com erro de 20,65% no enriquecimento ativo. Preservar F7.2 como referência. F8 WAV original de pesquisa, declarar banda útil e limites; F9 escuta e comparação C5/V10; F12/F13 e 32–64 notas não homologados.
