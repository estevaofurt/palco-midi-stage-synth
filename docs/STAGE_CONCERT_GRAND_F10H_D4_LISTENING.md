# F10h — consolidação S50, dinâmica e comparação auditiva

Base 322147c5acc43eca38ceb8f8177876010a926c4f. F10f 30/30 checks, 12/12 renders. S50 C4 ff crossing 33s vs 19.5s D/D4, no mesmo ganho e limiar RMS contextual; pp 2.5s, mf 23s (F10g 40s). S25 C4 mf 34.5s, ff crossing não observado até 39.5s, pp 2.5s. G4 mf S25 14s vs S50 12s. G4 ff S25 ainda em execução. F10g 28 checks, sete S50 ff aprovados, máximo A3 .8205668 FS no ganho .75, zero clipping. S50 priorizado provisoriamente pelo equilíbrio de C4 forte, não adoção final; S25 preservado. Não interpretar crossing como audibilidade; pp depende muito da amplitude inicial, analisar queda relativa, parciais, escutar. S50 C4 ff potência residual inicial +.152%, tardia +49.10% vs D4; S25 ff fração fora de bandas na última janela apenas 1.00474× S50 apesar da potência +22.30%, não afirmar retorno perceptivo de ruído. 

F10h completa 14 renders S50 pp/mf, sete notas, ganho comum .75 (mesmo dos sete ff F10g). Gate pico <=.85, zero clipping, passividade. Não alterar mecânica, curva MIDI, ganho diagnóstico ou modelos anteriores. Compara 6 WAVs já gerados C4 pp/ff D4/S50/S25 no ganho original, sem normalização. PCM24 48k, SHA256, metadata, prefixo PCM exato, 50ms fade e 1s gap. Sequência pp 47s (15s cada; inícios 0/16/32), ff 107s (35s cada; inícios 0/36/72). Analisa JSON de ponto flutuante de origem e verifica crossings absolutos/relativos, não reanálise acústica de gravação real. Cross-run artifacts F10e/f/g; nenhum áudio novo até CI confirmar. 

Workflow commit 46e9e0bc2c038b1f04a3c6b8ac0afcc40026e7ad. Próximo: revisar dinâmica e escuta; só então ampliar escala e tratar tampo compartilhado/pedais. Não homologar 32–64 vozes ou 88 teclas. D original e main preservados.

## Execução

CI 45511128271: {"success":5,"failed":0,"active":10,"queued":0}, 6 artefatos. [CI](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45511128271). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536; alterações apenas de pesquisa/documentação/dados/CI.
