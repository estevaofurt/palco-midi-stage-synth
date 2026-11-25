# F11t — amortecedores independentes e CC64 (protótipo)

Base F11s commit 0b8cbc942617129986a2e9d1df1f986ca5f0d9f5. Os workflows 45531921363 (6 acordes) e 45531946844 (12 dinâmicas) terminaram com sucesso; sem certificação auditiva.

Implementados comandos por nota e pedal CC64 com rampa de 25 ms e coeficiente de amortecimento experimental. A resolução de forças é simultânea com a matriz recíproca completa de compliance do tampo compartilhado e os contatos das cordas; trabalho viscoso não pode injetar energia. Nenhuma soma de WAVs. O renderizador antigo sem eventos segue sem alterações acústicas (regressão requerida). Soltura atua apenas após separação completa dos martelos.

Limites: eventos off/pedal apenas, sem retrigger ou arpejo, sem meio pedal, sem geometria de amortecedor calibrada, no máximo seis notas e três segundos. K750/K1000 continuam candidatos provisórios. Não integrar ao motor Stage Synth nem promover antes de F12.5, medição de afinação, evidência musical e testes 32/48/64 notas.

## Resultado verificado — F11t

Workflow [45533102919](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45533102919): **success**. 13 verificações unitárias de controle, 9 regressões originais F11s, ensaio físico de 85 ms aprovado (dry damperLossJ 0.0026755850673 J; pedal damperLossJ 0.0006848914319 J; maxBalance 2.5648e-15 J).

Workflow [45533190104](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45533190104): **success**, 4 artefatos de 3 segundos, 48 kHz, PCM estéreo 16/24, 144239 frames por canal incluindo delay de radiação, sem clipping, sem normalização, mesmo ganho fixo. Todos maxIncrease=0 e maxBalance<8.6e-14 J. Comparação *G7* com todas as teclas soltas em 1.5 s, pedal liberado em 2.7 s na versão com pedal.

| Variante | Caso | Dissipação dos abafadores (J) | Energia mecânica final (J) | Pico exportação | Artefato |
| --- | --- | ---: | ---: | ---: | --- |
| K750 | dry | 0.0029611421071 | 0.0125535776302 | 0.2481084 | 14984254961 |
| K750 | pedal | 0.0015083140866 | 0.0130047983895 | 0.2481084 | 14985279563 |
| K1000 | dry | 0.0032385560800 | 0.0124690273403 | 0.2684185 | 14985900957 |
| K1000 | pedal | 0.0018166497935 | 0.0127293522173 | 0.2684185 | 14986200201 |

A redução de dissipação nos amortecedores é comportamento mecânico coerente com pedal pressionado, não comprovação automática de sustain musical ou afinação. Pico idêntico entre dry/pedal ocorre porque a alteração acontece após o ataque. F12.5 **não aprovado para produto**. Escuta dos pares, mapa espacial, transições reais, reataque/arpejo e 88 notas continuam pendentes.
