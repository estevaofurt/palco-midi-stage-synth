# G3.12p — protótipo de polifonia B/C/D

Run 45772113622: 128 e 192 vozes reais, 44.1kHz, 40/40 leituras de sinal, relógio 1.0025 e 1.00246, redução Stage 64. Run 45772113721: 51/72 com margem, B/C/D 48k Studio 192 p99 .437/.419/.419, 256 .616/.619/.552 (D 1 atraso). B/C/D 128 promissor, não certificado; C benchmark isolado anterior não ativou explicitamente mecânica.

Expandir overlay exclusivamente, B/C/D até 128 explicitamente em Balanced/Studio, lite/>48k teto 64, eco 32, automático mantém qualidade nativa. Alocar pool e buffers no construtor via processorOptions, sem alteração de parciais ou presets. Stage permite expansão apenas piano sozinho e worklet pronto; camadas limite legado. Testar Chromium 128 em B/C/D Studio, C com mecânica ligada, presença de sinal, 40 polls, relógio, IDs e roubo. Não confundir caudas com slots registrados. Não certificar prazo real de callback, 192/256 em B/C/D, ou G3 físico. Main e fontes raiz preservadas.
