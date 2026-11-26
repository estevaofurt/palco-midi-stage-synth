# G3.11k — layout contíguo e teste de carga

G3.11j aprovado: energia 9.300009988280396e-13; estados 7.727351732016937e-12; ledger 4.146973817333611e-12. Mediana compilada em us/amostra 0.52567/1.09242/2.19583/4.57538/9.33516 para 32/64/128/256/512 modos. 512 usa 45.49% do orçamento de 48 kHz no p95 amortizado. Não é polifonia.

Testar layout modo-major de A, acumuladores u/z/mid e U.T@y em laços contíguos, mantendo ordem de soma por campo e Float64 sem fastmath. Não substituir implementação anterior até evidência. Comparar referência densa com 64/256/512 modos, 5/39 átomos sintéticos, 48/96 kHz. Benchmark pareado alternado com 128/256/512/1024 modos, 5/39 átomos, 48/96 kHz, blocos 32/64/128/256, 200 blocos por variante; p95/p99/máximo e ultrapassagens do orçamento, 64 combinações. Não inclui I/O, MIDI, cordas, observadores, agendamento de callback, nem coeficientes físicos. Sem alteração da main. Simulações acústicas continuam pendentes.
