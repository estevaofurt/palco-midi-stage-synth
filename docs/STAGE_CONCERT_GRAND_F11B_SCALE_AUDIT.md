# F11b — auditoria cromática e preparação F11c

Base 6da2ac932e7b7bb964283a7c91150b20072c49f9. F11a CI 45518512147: 16+37 checks confirmados. Consulta paginada REST: 40 jobs totais, renderizações ainda em andamento. Snapshot de logs: 17 novos renders aprovados, 38 casos válidos com os 21 anteriores, 26 pares adjacentes, pico máximo .820566812014095. Três flags preliminares pp: MIDI55→56 cauda +9.2757dB, 56→57 cauda -12.7682dB, 58→59 RMS inicial -6.6003dB. Não são reprovação perceptiva; triagem de engenharia. A gravação do JSON completo de snapshot não foi confirmada por limite de chamadas; recuperar logs novamente ao concluir F11a.

Implementados f11b-s50-scale-audit.mjs e .test.mjs: valida matriz de casos, ganho comum, pico <=.85, energia, clipping, RMS0/RMS2, fração e potência fora de bandas, dinâmica e diferenças adjacentes; distingue ausências e rejeições. Limiares 6dB inicial / 9dB cauda são triagem arbitrada, não padrões acústicos. 12 checks com 21 resultados reais congelados e casos sintéticos. Não normalizar por tecla.

Preparação F11c: f11c-wound-wire.mjs e .test.mjs, massa de enrolamento helicoidal, EI apenas núcleo, tensão para frequência alvo, massa linear e dispersão. Hipótese homogeneizada de uma camada, sem rigidez do enrolamento, efeitos de extremidade, medições, escala real ou especificação segura de fabricação. 12 checks SI; sem integração no renderizador ou novo áudio de graves. 

CI 45518798425 (workflow commit d0345caef38d5c46063e388ba7b2114bb14c8aa2) estava queued na consulta. S50 anterior e main preservados, nenhum parâmetro sonoro alterado. Próximo: concluir F11a e registrar 60 casos, executar auditoria completa, tratar flags por análise física/escuta, só então ampliar regiões e validar cordas enroladas.
