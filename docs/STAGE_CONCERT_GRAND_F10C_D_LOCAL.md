# F10c — modelo D, amortecimento modal localizado no G4

Base F10b e969974dc569439125e472cb777b92ad1059d7b9. F10b: 35 verificações aprovadas, 5/6 renders; D1/D2 rejeitados por aumento de potência fora das bandas e clipping de D2 ff. D original, C4 e G3 congelados. Não avançar para novos registros antes de diagnosticar G4.

F10c é sensibilidade experimental, não correção confirmada: quatro modos do tampo 372.5984818599289, 376.10992819640126, 380.62893452755657, 384.3371342573889 Hz, escolhidos por proximidade do pico observado e pelos modos registrados na F10b. Não assumir que um deles seja a causa única do pico 367.7 Hz. Aplicar multiplicadores absolutos 6 ou 8 da perda estrutural base; referência D mantém 4× no primeiro e 3× nos outros. Global 3×, quatro outros modos previamente selecionados a 4×, patch original, cordas, feltro, curva de velocidade, ganho e matriz radiativa preservados. Alteração no objeto de pesquisa depois da construção HybridBoard e antes da junta e do cache fastBoard; recomputar coeficientes, fatoração Cholesky dos blocos afetados e compliance G. Não é filtro de áudio. Guardar variante no checkpoint, rejeitar notas diferentes de MIDI67. Não usar perda dependente de nota como solução definitiva para tampo compartilhado.

Arquivos novos f10c-d-local.mjs, f10c-d-local.test.mjs, f10c-d-local-demo.mjs e workflow concert-grand-f10c-d.yml. 22 testes F10a + 15 novos, exigindo equivalência exata do controle, continuidade e passividade. Seis renders 3s em velocidades 24/76/127, PCM16/24 com ganho fixo; clipping rejeitado e registrado. Comparar potência absoluta fora das bandas nas janelas iniciais, pico próximo de 368 Hz, RMS2 e ataques; nenhuma variante adotada antes de resultados e escuta. Sem extrapolar duração a partir de 3s. CI configurado no commit 6ca2af9abd42c55bd3d02538261ecc1d906fcf48, ainda sem confirmação nesta anotação. Main, motor D original e F10a preservados. Polifonia real 32–64 e expansão 88 teclas pendentes.

## Execução

CI 45487489322: smoke in_progress / sem conclusão, 0 artefatos na consulta. [Run](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45487489322). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536; alterações restritas a pesquisa, dados, CI e documentação.

## Resultados finais F10c

CI [45487489322](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45487489322), 22+15 testes aprovados, 6/6 renders concluídos, sem clipping, passividade preservada. Dados em audio/analysis_f10c_d_ci.json com IDs e resultados de logs, sem reanálise auditiva local. Comparação G4 de ganho fixo com F10a, janela .025–.525s:
| Touch | D3 potência pico 367.68 Hz relativa | D4 potência pico relativa | D3 potência fora de bandas relativa | D4 potência fora de bandas relativa | D3 RMS2 relativo | D4 RMS2 relativo |
|---|---:|---:|---:|---:|---:|---:|
|24|.27893|.10155|.42991|.29169|.94385|.90964|
|76|.27634|.09983|.39862|.25526|.95852|.93344|
|127|.27592|.09956|.40141|.25907|.95821|.93295|

Potência estimada fora de bandas = rmsBand² × wideOffFraction. RMS2 = janela 2–2.5s. D4 reduz ~90% do pico nas três dinâmicas, mas perde 6–9% de RMS2. Na janela .525–1.025s as diferenças D3/D4 são menores (ff .30659/.29743 em potência relativa). Não confundir pico com ruído mecânico ou qualidade auditiva. D4 priorizado para teste inter-notas, D3 fallback. D original não substituído. F10d verifica se a mesma configuração estrutural pode ser aplicada sem depender da nota; não é ainda tampo com estado compartilhado polifônico.
