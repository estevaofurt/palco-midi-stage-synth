# G3 — Operador espacial implícito de 369 portas

Continuação de G3_Diagnostico_Espectral. Normalização corrigida, d3 a 48 kHz, 384 kHz internos. Exterior isolado com fluxos prescritos, não acoplamento temporal da cavidade. 147 entradas dos manifestos internos conferidas. Sem render ou promoção.

Malha 30×30 recuperada dos menores polos dos canais 60, 2, 1: dx=0,04733333333333334 m, dy=0,05333333333333333 m, h=0,1 m. Campos DCT inversos de T/ix arquivados, raios b16/b64 dos JSON históricos. Erro das escalas 2,4755e-16. Não recupera posições absolutas dos receptores.

Agregação exata dos atrasos, projeção temporal d3 e convolução espacial Toeplitz embutida em grade circulante 60×60 com padding. FFT espaço-temporal em lote retorna resposta linear causal completa. 26/26 controles, tolerância 1e-10: duas escalas, 12 símbolos (6 frequências em cada interface de 12/48 portas), seis reproduções temporais contra kernels arquivados, três controles de trabalho e três comparações harmônicas na interface completa. Erros máximos: símbolos 3,1084e-15; temporais 1,2342e-15; 369 portas 9,4621e-15 perante símbolo calculado separadamente da mesma malha (não referência física independente). Impulso, ruído e seno 5183,7 Hz, 24 blocos e resposta completa 324 blocos. Nenhum trabalho acumulado negativo observado nos três casos de 369 portas.

b64: 2398 taps finos, 301 lags d3. Coeficientes densos teóricos 2.950.881.192 bytes, grade 39.009.600 bytes (98,68% menor). Não inclui campos, buffers ou estados; denso completo não alocado.

SpatialStream: histórico causal circular, contribuição instantânea, preview sem avanço de estado, step confirma entrada. 40 blocos de ruído em 369 portas: erro lote 7,9443e-16, preview zero, decomposição 1,4497e-15, reset 7,1933e-16, prefixo 4,8486e-16. Janela não testa volta completa do anel. Média step 3357,90 us vs orçamento total 20,833 us. Kernel FFT 161.239.680 bytes e histórico 53.746.560 bytes, sem campos/temporários. Não é candidato de tempo real.

Reprodução: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, BLAS/OMP 1 thread. Verificar INPUT_SHA256SUMS na raiz restaurada; python spatial.py /raiz/restaurada; python causal.py. Binário grid-b64.npz e logs em pacote local G3_Operador_Espacial.zip, não publicados neste commit.

Decisão: preservar d3, d6/misto experimentais, d8 referência. Próximo: testar anel completo, implementar cavidade causal agrupada, Schur inferior com 867 incógnitas, acoplar e verificar energia/trabalho/continuidade. Receptores completos não reconstruídos; 12 dependências da regeneração geométrica pendentes. Parâmetros experimentais definidos nesta etapa. Sem certificação global ou render sonoro.
