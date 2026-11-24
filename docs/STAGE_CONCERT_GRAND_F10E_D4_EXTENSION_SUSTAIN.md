# F10e — extensão restrita D4 e sustain prolongado

Base dd7732dcaa60c45c11caa0a109d9ef79eda0960c. F10d confirmado (40/40 checks, 6/6 renders, sem clipping) e registrado em audio/analysis_f10d_d4_ci.json e docs/STAGE_CONCERT_GRAND_F10D_D4_BOARD.md. D permanece referência escolhida pelo titular; D4 candidato experimental, sem promoção. Escuta e validação independente pendentes.

## Extensão restrita
MIDI 53/55/57/60/64/67/72 (F3/G3/A3/C4/E4/G4/C5), comprimento .65 / 2^((midi-60)/12), diâmetro .96mm, aço e três cordas; mesma geometria hipotética e posição do patch. Não escala medida nem prova de adequação das cordas maciças em todos os registros. D4 aplica os mesmos 337 coeficientes do tampo, perdas, feltro, ganho e curva MIDI a todas as notas. Notas anteriores delegam ao renderer F10d, exatidão e checkpoints testados; novas notas transpõem apenas comprimento e frequência. Novos 12 renders 3s nas velocidades 24/76/127. Rejeitar clipping, sem normalizar. Verificar frequências teóricas, uníssono, passividade, assinatura do tampo, continuidade. Não extrapolar para 88 teclas ou cordas enroladas.

## Sustain
8 renders 20/40s: D e D4 C4 MIDI24, D4 C4 MIDI76/127, D e D4 G4 MIDI76/127. D C4 médio/forte já medidos em F9.19e. Ganho comum .36767023440034063, PCM16/24, análise por nota, limiar contextual histórico .0006518758466381057 FS e queda relativa. Esse limiar não é audibilidade e sua transferência a G4 ou pp não é validada. Comparar com referência D na mesma nota/dinâmica; não afirmar meta 30–35s forte/10–15s suave atingida sem evidência. Sem mudança de perdas para alongar sustain. 20s suave/médio, 40s forte, sem pedal ou note-off; não é comportamento completo de tecla/pedal.

## Implementação
f10e-d4-extension.mjs, .test.mjs, -demo.mjs, f10e-d4-long-demo.mjs, workflow concert-grand-f10e-d4.yml commit 4faa487fb37b28680adbf987302e6f59ebcc7e3e. 18 checks F10d e 18 novos; 20 renders dependem do smoke. CI [45507422898](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45507422898) inicialmente queued, não confirmar êxito antes dos jobs/artefatos. Sem mudança em D original, D4 F10d ou main. Simulações monofônicas offline, não polifonia compartilhada nem integração. 
