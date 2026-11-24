# F10g — validação ampliada S50 e sensibilidade S25

Base 51ad3286b68742c3365d1e0371157f879ffc76c7. F10e final 36 checks, 19/20 renders, oito longos completos, A3 ff rejeitado (52 amostras, pico 1.090023 FS). F10f 30 checks, sete headroom aprovados, quatro longos S50 aprovados, C4 ff ainda em execução na consulta. Dados CI em audio/analysis_f10e_d4_ci.json (final) e audio/analysis_f10f_d4_ci.json (snapshot). Não houve escuta nem reanálise local de WAV.

F10f ganho comum .75 do original, máximo observado A3 .8175173, zero clipping nas sete notas ff. S50 C4 pp 2.5s vs D4 2s; C4 mf sem crossing até 19.5s vs 13.5s; G4 mf 12 vs 9.5s; G4 ff 17 vs 13s, D original 15.5s. No G4 ff potência fora de bandas S50/D4 nas quatro janelas .025–.525/.525–1.025/1.025–1.525/2.025–2.525s = 1.00135/1.02571/1.22527/1.43991; RMS2 1.16473. Ganho de sustain promissor mas potência residual tardia aumenta. Comparar proporções e parciais, não confundir aumento absoluto da cauda com retorno de ruído. Limiar contextual não equivale a audibilidade.

S50 segue candidato provisório. Novo wrapper uniforme para sete notas: F3/G3/A3/C4/E4/G4/C5, preservando D4 e S50 anteriores. S25 hipótese adicional: constantes vertical .05 e horizontal .025 (25% do D4, redução 75%), coeficientes de frequência inalterados .0002/.00012, mesma placa 337 modos, feltro, geometria, curva MIDI. Não adotar perdas por nota. 12 regressões F10f + 16 checks novos (equivalência S50 C4/G4, controle A3, passividade, assinatura e continuidade). 7 S50 ff 3s no ganho comum .75, gate pico <=.85 e zero clipping. Cinco S25 ensaios C4 pp/mf/ff e G4 mf/ff no ganho original, um S50 C4 mf de 40s para obter crossing. C4 mf/ff e G4 ff 40s; pp/G4 mf 20s. Comparar potência absoluta e relativa fora de bandas e evolução dos parciais, limiar e quedas relativas. Não promover S25 apenas por duração. Monofônico offline, sem pedal, 88 teclas e polifonia pendentes.

Arquivos f10g-d4-loss-pilot.mjs, .test.mjs, f10g-d4-s50-demo.mjs, f10g-d4-long-demo.mjs, workflow concert-grand-f10g-d4.yml commit 966a249d2ba263e5cc2da8369d5c576696e01637. D original e D4/S50 anteriores preservados.

## Execução

CI 45509969698: smoke in_progress / sem conclusão, 0 artefatos. [CI](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45509969698). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536; somente pesquisa, documentação, dados e CI alterados.
