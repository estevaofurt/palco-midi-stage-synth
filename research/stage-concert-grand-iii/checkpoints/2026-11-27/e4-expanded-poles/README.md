# G3 — Mi4: modos adicionais e fechamento da transferência
Continuação de d8e878b. Parâmetros físicos, 128 modos por corda, 1360 coordenadas mecânicas, tampo 80, 369 portas e midpoint a 384 kHz inalterados. 22 entradas SHA256SUMS, 8 INPUTS e 20 FORCES do checkpoint anterior conferidas; 4 entradas EXTRA_INPUTS reconferidas (sobreposição). Nenhum novo impacto.
Busca a partir de todas as dez frequências naturais secas de Mi4 em ±100 cents, sem limiar de participação da primeira forma interna da corda. Equação bordada e condensação exata; repetição com perturbação +0,015+i0,01 Hz. Dez buscas passam, oito raízes distintas, duas convergem ao mesmo polo de 328,459 Hz. Cinco adicionais aos três históricos. Não é censo de todos os polos. Máximos resíduo mecânico seco/acoplado 7,474663e-15, diferença repetição 3,934060e-12 Hz. Todos apresentam amortecimento positivo. Resíduos por derivada central 1e-4/5e-5 Hz, integração de contorno 16/8 pontos raio 0,004 Hz, solução integral em um ponto: máximos 3,311729e-10, 2,981626e-10, 8,473686e-12 e 6,778722e-13 respectivamente; 8/8 passam 1e-5.
| Frequência Hz | T60 s | Amplitude mic1 Pa aos 12 ms | Anterior |
|---:|---:|---:|---|
|317,036149|0,562313|0,399554|Não|
|321,460217|0,438921|0,141473|Não|
|325,989204|1,105741|0,528044|Sim|
|328,459008|0,696976|0,130442|Não|
|329,521066|51,576336|0,001071|Sim|
|329,740898|52,163017|0,001030|Sim|
|332,399404|0,408253|0,227619|Não|
|335,938939|0,499251|0,043567|Não|
Fechamento com soma de polos e conjugados, força coletiva conforme referência. 20 pontos originais, 19 pontos médios não usados no ajuste, 97 pontos em ±100 cents. Ajuste diagnóstico do resíduo complexo da transferência completa por polinômios grau 0/1/2 somente nos 20 pontos originais; não é realização causal/passiva. Erros agregados coletivos em %:
| Variante | Original | Pontos médios | Faixa ampla |
|---|---:|---:|---:|
|3 polos|25,566824|25,653149|52,418205|
|8 polos|5,519969|5,490628|15,012606|
|8 + constante|0,222246|0,206328|6,833464|
|8 + linear|0,114380|0,104068|7,216388|
|8 + quadrático|0,031460|0,026834|24,834006|
Pior ponto de oito polos na grade original 12,1850%, grade média 11,9942%, faixa ampla 70,1510%. Quadrático extrapola mal; rejeitar como modelo. Separa polos adicionais e fundo residual local sem identificar todos os mecanismos.
Excitação com força arquivada Mi4 forte 3 m/s, 96 modos, 384 kHz, 12 ms; transferência 128 modos. Recorrência IIR independente máximo 8,273446e-15. Soma de amplitudes dos cinco novos polos mic1 aos 12 ms 0,942655 Pa (177,811% da soma dos três anteriores 0,530145 Pa), mic2 196,114%. Aos 0,1 s após 12 ms razão 86,919%/98,246%; aos 0,5 s 7,633%/9,865%; a 1 s 0,293%/0,501%. Soma de amplitudes é limite superior, não pressão resultante, energia radiada ou duração audível. Novos polos T60 0,408–0,697 s. Nenhuma simulação longa integral, áudio, EQ, normalização, calibração ou alteração física. Parâmetros de busca/grades definidos nesta etapa. Próximo: ampliar busca com sementes/contornos, aproximação passiva da carga e validação da cauda. Não substituir por polinômio local.
Pacote local G3_Mi4_Modos_Adicionais.zip: 24 entradas SHA256SUMS verificadas, ZIP íntegro. Reprodução conforme CHECKPOINT.md: verificar manifestos, executar extra_modes.py, closure.py e excitation_expanded.py com uma thread BLAS/OMP. Este commit publica relatório e hashes; demais códigos e binários no pacote. Main preservada.
