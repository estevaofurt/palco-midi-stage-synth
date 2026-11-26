# G3.11d2 — comparação de bases congeladas e benchmark harmônico

G3.11d 45729588927 continua em execução, unit aprovado. G3.10m/p bloqueados por falha das quadraturas disjuntas: não usar 429. G3.11c aprovou distribuição [16,16,16,16,16,16,24] nos dois ângulos.

Reaproveitar matrizes independentes de 55/175/275 Hz quando completas, mesmo que a redução 168 falhe, exigindo proveniência, inventário reativo, quadratura suave, estabilidade física e hash dos operadores. Comparar as bases fixas 120 e 168 sem retreinamento; cada uma deve passar 5%. Em paralelo reproduzir comparações de malha refinada nas seis frequências anteriores e medir fatoração + solução de quatro RHS com matrizes pré-projetadas, 21 repetições, BLAS single-thread, mediana/p95. Não medir projeção, síntese, latência de áudio ou polifonia. Benchmark não certifica ganho de tempo real. Sem novas simulações físicas. Main preservada.
