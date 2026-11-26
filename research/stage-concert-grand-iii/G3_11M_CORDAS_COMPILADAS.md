# G3.11m — núcleo compilado cordas/tábua/ar

G3.11l aprovado (run 45733154637): energia 4.129200384177374e-13, estados 3.0035905802050934e-12, ledger 3.4855452556808583e-12. G3.11d/g ainda pendentes.

Compilar o acoplamento Schur validado com layout modo-major de G3.11k. Manter equações, Float64, sem fastmath, parâmetros sintéticos, buffers pré-alocados. Testar 32/64 vozes, 4/8 parciais (até 512 DOFs) com tábua de 64 modos, 5/39 átomos e 48/96 kHz, contra referência densa. Benchmark 48 configurações (32/64 vozes, 4/8/16 parciais, 128/256 modos de tábua, 5/39 átomos, 48/96 kHz), 200 blocos de 64 amostras. Até 1024 DOFs das cordas no benchmark; verificar energia também durante estresse. P99, máximo e ultrapassagens são diagnóstico de orçamento de bloco, não aprovação de callback. Não inclui martelo, MIDI, pedal, observadores, I/O ou parâmetros físicos calibrados. Não promover se falhar. Main preservada.
