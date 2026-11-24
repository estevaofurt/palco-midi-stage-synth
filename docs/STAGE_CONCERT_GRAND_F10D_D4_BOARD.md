# F10d — D4 com configuração estrutural fixa entre notas

Base ddf769454a6cf7e4d1daa0a8d5afe0215bd9315f. F10c 37/37 verificações e 6/6 renders, sem clipping. D4 local8 reduz potência do pico G4 367.68 Hz ~90% nas três dinâmicas, RMS2 menor 6–9%. D3 alternativa. D original permanece referência selecionada pelo titular; D4 não homologado. F10d é teste de risco de regressão, não promoção.

Aplicar exatamente a mesma configuração de amortecimento de quatro modos (8× absoluto) a G3/C4/G4, sem dependência da nota, usando applyLocalLoss antes da construção da junta e do cache. Global 3×, quatro outros modos a 4×, 337 modos, mesmas posições, cordas, feltro, curva MIDI, ganho e radiação do piloto. Assinatura das 337 frequências/coeficientes de amortecimento deve ser idêntica entre notas. Simulações monofônicas independentes, NÃO um tampo compartilhado em tempo real. G4 F10c deve ser bit-exato em 25 ms e estado, permitindo reaproveitar os três WAVs. D original, C e G3/C4 originais preservados. C4 do candidato pode variar, comparar explicitamente.

Arquivos f10d-d4-board.mjs, .test.mjs, -demo.mjs, workflow concert-grand-f10d-d4.yml, commit 38d116aaacc358383352fa932eda22a3e31642d5. 22 regressões D + 18 novos checks: assinatura idêntica, passividade, pressão e estado exatos no G4, preservação da geometria, continuidade, checkpoints. Seis novos renders G3/C4 × 24/76/127, 3s, PCM16/24, ganho fixo. Clipping é rejeição, não normalizar. Comparar contra dados F10a; auditar ataque, energia fora das bandas e RMS2, além de espectro de parciais. Nenhuma adoção antes de revisão e escuta. Se D4 prejudicar C4, preservar D e investigar alternativa física; não fazer seleção de coeficientes do tampo por nota. F10 expansão completa, sustain longo G4, validação independente e 32–64 vozes reais pendentes.

## Execução

CI 45490795427: smoke in_progress / sem conclusão, 0 artefatos na consulta. [Run](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45490795427). Main reconferida em ff73ddc95e57e192ea8b65a03fae11ba132e0536; alterações restritas a pesquisa, dados, CI e documentação.
