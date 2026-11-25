# F11t — amortecedores independentes e CC64 (protótipo)

Base F11s commit 0b8cbc942617129986a2e9d1df1f986ca5f0d9f5. Os workflows 45531921363 (6 acordes) e 45531946844 (12 dinâmicas) terminaram com sucesso; sem certificação auditiva.

Implementados comandos por nota e pedal CC64 com rampa de 25 ms e coeficiente de amortecimento experimental. A resolução de forças é simultânea com a matriz recíproca completa de compliance do tampo compartilhado e os contatos das cordas; trabalho viscoso não pode injetar energia. Nenhuma soma de WAVs. O renderizador antigo sem eventos segue sem alterações acústicas (regressão requerida). Soltura atua apenas após separação completa dos martelos.

Limites: eventos off/pedal apenas, sem retrigger ou arpejo, sem meio pedal, sem geometria de amortecedor calibrada, no máximo seis notas e três segundos. K750/K1000 continuam candidatos provisórios. Não integrar ao motor Stage Synth nem promover antes de F12.5, medição de afinação, evidência musical e testes 32/48/64 notas.
