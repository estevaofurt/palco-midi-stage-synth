# F11a — Stage Concert Grand S50, piloto cromático F3–C5

Base 145aef30c3e313c6dab65fbbf1ed8d8dceab0398. Preferência explícita do titular: "gostei do s50"; S50 congelado como referência sonora de pesquisa, não homologação de produto. F10h confirmou 21/21 renders (sete notas × MIDI24/76/127) a ganho comum .2757526758002555, pico máximo .820566812014095, zero clipping, pico e RMS inicial monotônicos. C4 ff 33s, mf 23s, pp 2.5s no limiar contextual a ganho diagnóstico .36767023440034063; não representa duração audível. S25, D4, D e main preservados.

## Escopo
Preencher todos os semitons MIDI53–72 (F3–C5, 20 notas). Sete notas anteriores (53/55/57/60/64/67/72) delegam diretamente ao renderizador S50 F10g, sem trocar cálculos. Treze novas (54/56/58/59/61/62/63/65/66/68/69/70/71) usam a mesma hipótese de tricórdio maciço, L=.65 / 2^((midi-60)/12), d=.96mm, E=200GPa, rho=7850kg/m3, tensão calculada, uníssono ±.5 cent. Não escala medida, não extrapolar aos graves enrolados ou agudos extremos. Mesmo tampo D4 de 337 modos, 3× global, quatro modos 8×, quatro outros 4×, feltro 1.5, perdas constantes .1/.05 e coeficientes .0002/.00012, patch, curva MIDI e ganho comum. Checkpoint identifica etapa, nota, perdas, e parâmetros prévios. Monofônico offline, não compartilhamento de estado ou pedais.

## Validação
16 checks F10g + 37 novos F11a: frequências alvo, tensão positiva, comprimento, uníssono, passividade, mesma assinatura do tampo, perdas e feltro; equivalência bit-exata da pressão nos primeiros 25ms, estado e corda das sete notas anteriores no toque médio, continuidade e rejeição de checkpoint incompatível. 39 renders novos 3s × MIDI24/76/127, ganho comum, sem normalização, gate pico <=.85 e zero clipping, PCM16/24 estéreo 48k, análise espectral e RMS. Limite de 12 jobs simultâneos. Após concluir, reunir os 60 casos (21 anteriores +39 novos), verificar dinâmica monotônica por nota, descontinuidades entre notas adjacentes, picos, energia, parciais e preparar escala auditiva. Se falhar headroom ou timbre, manter S50 anterior e investigar geometria/radiação; não normalizar por tecla nem reduzir perdas indiscriminadamente.

## Implementação
f11a-s50-scale.mjs, .test.mjs, -demo.mjs, workflow concert-grand-f11a-s50.yml, commit f38983e3143cc0c8bc601f3e5ca20dd64fab9eb5. Escala de 20 notas implementada, 13 novas ainda sujeitas a validação. F11b: análise adjacente e extensão por registros, com modelo de cordas enroladas e transições de uníssono quando apropriado. Tampo compartilhado, pedal, 88 notas completas, CPU real 32–64 e integração pendentes. Não alterar motor de produção.

## Execução

CI 45518512147: smoke in_progress / sem conclusão, 0 artefatos. [CI](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45518512147). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536. Alterações restritas à pesquisa, CI e documentação.
