# G3.11j — núcleo compilado em blocos

G3.11i aprovado: energia 9.348526505989057e-13, estados 7.82340957475466e-12. Benchmark lowrank Python 47.06/47.38/48.10/48.66 us em 32/64/128/256 modos. Denso 45.40/48.00/56.34/93.10 us. Não cabe no orçamento 20.833 us a 48 kHz.

Núcleo Numba em Float64 sem fastmath, arrays de trabalho pré-alocados, inversa do pequeno sistema SPD calculada antes do bloco. Processar 256 amostras por chamada; manter estados entre blocos. Validar 32/64/128/256 modos e 44.1/48/96 kHz contra solução densa, energia <=1e-9, estados e ledger <=1e-8. Testar independência da partição de blocos. Benchmark 32–512 modos, mesma máquina, Python vs compilado, exclui compilação e inicialização. Reportar p95 por amostra amortizado no bloco e fração de orçamento 48k. Não é callback de áudio, não inclui MIDI/cordas/observadores, não certifica polifonia. Coeficientes sintéticos; nenhuma alteração do motor estável. Densificação e frequências independentes continuam pendentes.
