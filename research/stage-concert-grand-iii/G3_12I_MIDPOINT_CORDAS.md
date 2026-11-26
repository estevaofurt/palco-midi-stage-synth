# G3.12i — integrador temporal físico das cordas

G3.12h run 45742331448 aprovado: 80 coordenadas, dez cordas, quatro teclas; treino 0.0001531998340295518, interno 0.00015651453684746073, externo 0.00015210886616773877. Base 72 externa 0.2626712581527556. Mapa físico arquivado divergente neste runner (massa 0.01567, rigidez 111821), reconstrução aprovada 8.635486178711192e-08. Não reutilizar mapa bruto entre montagens.

Ajuste denso run 45742331124 reprovado nos dois ângulos, externo 30° 0.4907916569948588, 55° 0.2004581921130277. Otimizador e passividade aprovados. Não usar como carga.

Novo integrador midpoint de 80 coordenadas e dez cordas, normalização dos interiores com Wire.U, termos cruzados de massa/rigidez/amortecimento entre ponte e cordas; Schur exato do sistema midpoint com fatoração fixa. Comparar com montagem física densa independente, energia/trabalho/perdas/estado/observação, 48/96k. Seleção de 8/16/32/64/128 modos internos por corda contra resposta condensada de 128, congelar antes de 15 frequências novas a 7/8 dos intervalos. Validação do integrador separada de redução dos interiores. Benchmark Python diagnóstico, não certificação de tempo real. Sem ar, martelos, pedal, polarização lateral, calibração ou áudio. Main preservada.
