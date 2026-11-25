# F11d — martelo de uma/duas cordas e piloto grave S50

Base 5edeaac93c6cf29c6b94d53cabbc6adb14a437a1. F11c review 45520232315 success, artifact 14977779872: três escalas 20 notas, 60/60 fontes PCM verificadas, dinâmica crescente nas 20 notas (pico/RMS0/RMS2), máximo .8305203117745873 FS, 57 transições, 12 flags de triagem. Resumo em audio/analysis_f11c_s50_scale_bass.json. Forte MIDI70→71 -26.449dB de RMS2 e 71→72 +23.553dB; MIDI65→66 -10.709dB. Flags 6/9dB não são critérios perceptivos. Não modificar S50 ou normalizar por nota; estudar mobilidade/energia e radiação para distinguir causa, depois testar alteração física isolada se necessário. Preferência S50 permanece.

F11d novo VariableHammer: n=1/2 com solver de contato passivo e memória individual; n=3 delega métodos de PolarizedHammer e solveCoupledContact anteriores, preservando despacho de subclasses de instrumentação. Novo renderBassPilot isolado, 36/43/48, 1 ou 2 cordas enroladas, uníssono ±.5 cent para duas. Mesma hipótese de tampo D4 337 modos, S50 perdas .1/.05 e .0002/.00012, feltro 1.5, patch, ganho, massa do martelo e geometria de radiação como controle experimental, não calibração dos graves. Estado/checkpoint protege nota, número de cordas, velocidade. Passividade, contato unilateral, separação, continuidade; regressão exata do C4 S50 (pressão 25ms e estado no toque médio). Modelo de enrolamento apenas massa e EI núcleo, não inclui efeito de extremidades/rigidez de contato. Não adotar uma configuração de cordas por registro antes de comparar.

10 checks de geometria +36 novos checks (contato, regressão, seis casos, continuidade e guards), 18 renders 3s a 48k PCM16/24, MIDI24/76/127 e ganho .2757526758002555; pico <=.85, zero clipping. Sem normalização por tecla. Se gate falhar, investigar em vez de promover. Nenhum áudio grave confirmado ainda. Monofônico offline, não acordes/pedal/tampo compartilhado nem polifonia real. Workflow commit 304c0f477965b9244fd0bea9156b97a6803b4338. CI 45522085368 in_progress. Main preservada; sem alteração de módulos antigos.

## Execução confirmada

2026-11-25T00:57:26.7966443Z F11C_BASS_TESTS 10
2026-11-25T00:57:38.6101931Z F11D_BASS_TESTS 36
Smoke aprovado, 18 jobs graves queued na última consulta, zero artefatos novos. Main reconferida ff73ddc95e57e192ea8b65a03fae11ba132e0536.
