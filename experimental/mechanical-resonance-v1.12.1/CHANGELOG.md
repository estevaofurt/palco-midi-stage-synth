# Stage Synth — evolução experimental de ressonâncias

## v1.12.1 — acoplamento mecânico (22/11/2026)

- Mantidos os 88 estados de tecla, amortecedores e pedal.
- Exposição de um sinal limitado de reação da ponte ao motor de cordas (`reaction`).
- Adição de `CoupledPianoBus` para fechar a malha dentro do mesmo callback de áudio, **quando um motor de cordas compatível é fornecido**.
- Melhoria do gate das notas mais agudas sem abafadores (18 teclas no modelo de referência simplificado).
- API de bloco compatível; benchmark e testes de ida e volta do sinal.
- Nenhuma mudança na v1.9.5 nem integração direta na v1.11.0.
