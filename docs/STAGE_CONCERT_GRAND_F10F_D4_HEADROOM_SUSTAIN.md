# F10f — D4: margem digital comum e hipótese de sustain

Base 3024475fe84384d5d06d8cc7676ce3888d45ac84. F10e CI 45507422898: 36/36 checks; 11/12 renders curtos e 5/8 longos aprovados na consulta; três fortes em execução. A3 MIDI127 rejeitado, pico 1.0900230933519346 FS, 52 amostras saturadas. Dados em audio/analysis_f10e_d4_ci.json (snapshot parcial dos logs, atualizar ao concluir). C4 pp D/D4 2s no limiar contextual, C4 mf D4 13.5s (D histórico 13.5s), G4 mf D/D4 11/9.5s. Limiar não representa audibilidade e não validado para pp/G4. Não inferir duração forte antes do resultado.

## Margem digital
Novo ensaio de exportação, sem alteração mecânica: ganho comum 0.75 × .36767023440034063 = .2757526758002555 (aprox. −2.5 dB). Sete notas no forte, mantendo o cálculo de pico/clipping original antes de exportação. Gate de pico <=.85 FS e zero clipping. A3 pico previsto .8175173 FS; previsão, não resultado. Sem normalização por nota, limiter ou compressão. Não substituir ganho original de diagnóstico, nem comparar RMS absoluto entre ganhos sem correção. Margem monofônica, não garantia de polifonia; somar vozes exigirá estratégia futura.

## Sustentação
Ensaio D4-loss50, redução de 50% somente da parcela de perda de corda independente de frequência (vertical .2→.1; horizontal .1→.05), sigma2 inalterado (.0002/.00012). Parâmetros hipotéticos, constantes e positivos, sem envelopes artificiais. Wrapper antes da construção de PolarizedBridge, mesmo D4 de 337 modos, patch, feltro, cordas, curva MIDI, ganho ORIGINAL para comparação, checkpoint protegido. Teste fator 1 exige pressão/estado exatos ao D4. Cinco ensaios 20/40s C4 pp/mf/ff, G4 mf/ff. Comparar potência fora de bandas, RMS por parcial, quedas relativas e limiar contextual com F10e; não aprovar simplesmente por aumento de sustain. Não alterar D/D4 anteriores. Sem homologação auditiva ou polifonia.

## Implementação
f10f-d4-headroom-demo.mjs, f10f-d4-sustain.mjs, .test.mjs, -demo.mjs, workflow concert-grand-f10f-d4.yml (17ed123ce321af378657e8014ea5589f93ce2e0a). 18 regressões extensão + 12 novos checks; 7+5 renders dependem do smoke. Execução ainda não listada na primeira consulta; não declarar aprovação. 

## Execução

Run 45508716694: in_progress / sem conclusão, 0 artefatos. [CI](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45508716694). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536. F10e ainda com três renders fortes em execução na consulta.
