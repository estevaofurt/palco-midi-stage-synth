# Stage Synth v1.12.8 — motor D experimental com uníssonos F1–C2

**Data:** 23/11/2026. **Objetivo:** atualizar SOMENTE o motor D dentro do seletor existente do módulo **Piano Acústico**, preservar todos os demais motores e permitir comparação real em WAV com o D v1.12.7.

## Alteração realizada

- `physical-piano-hybrid.js`: recebe **exatamente o mesmo código testado** em `physical-piano-hybrid-v128-candidate.mjs`, arquivado na PR #32. A única mudança física-algoritmica é a passagem de A0–C2 monofônico por parcial para **A0–E1 sem dupla e F1–C2 com dois modos de uníssono**. As amplitudes desses dois modos são distribuídas em **50/50 somente entre F1 e C2**, como hipótese de prompt sound/aftersound, sem adicionar harmônicos extras ou reverb.
- `physical-piano-hybrid-v127.mjs`: snapshot byte a byte do D v1.12.7 de antes da alteração; **não é um novo preset nem nova categoria**.
- `acoustic-v127.mjs` + `v1.12.7.html`: a página histórica carrega o roteador de áudio congelado que usa o núcleo D v1.12.7 (não aponta mais para o D atual). A página `v1.12.6.html` continua apontando para seu módulo arquivado.
- `acoustic.js`: atualiza apenas identificadores de cache dos Worklets para a distribuição 1.12.8. `index.html` e `package.json`: versão 1.12.8. **Não criar categorias, links na UI, nem alterar seletores A/B/C/Clássico, FX, MIDI, presets ou padrão C**.
- `tests/piano_d_v128_release.test.mjs`: verifica que D atual e candidato auditado são PCM idênticos em 12 teclas × 3 qualidades; que notas A0–E1 e C#2–C8 são PCM idênticas às do D v1.12.7; e que C2/A1/F1 realmente mudaram.

## Referência acústica original e limitações

Comparação no **GitHub Actions 45183947692**, usando **AIFF originais Iowa Steinway B C2 mf e C3 mf, SHA256 e bytes validados**. **Nenhum áudio de terceiros incluído no produto ou em WAV gerado**. Em C2 mf, contra D v1.12.7, o erro do novo D:
- **0–12 ms:** diminui **0,34 dB** (melhor)
- **12–36 ms:** aumenta **0,28 dB** (pior)
- **900–1400 ms:** aumenta **0,87 dB** (pior)
- Os 7 harmônicos confiáveis têm diminuição modesta de erro médio nas quatro janelas de **171 ms**: −0,035/−0,160/−0,347/−0,152 dB. Essas janelas **não são o primeiro instante de impacto**. C3 mf mantém os valores idênticos, pois seu caminho não foi alterado.

**Conclusão:** ganhos pequenos e métricas mistas, sem confirmação perceptiva. Não declarar que v1.12.8 reproduz madeira, tampo, ponte real, ou possui certificação de 32–64 notas no dispositivo; **R-GATEs completos 0/7**. A atualização é autorizada como **motor D EXPERIMENTAL**, mantendo a capacidade de reverter e comparar com as páginas históricas.

## Áudios A/B gerados pelo código autêntico do Stage Synth

O renderizador `scripts/render_piano_d_v128_candidate_wav.mjs` gera **estéreo PCM 24-bit 48 kHz, mesmo ganho, sem normalização individual, sem FX, sem samples externos**, com C2 pp/mf/ff, F1/A1, C3/C4 e acorde. Artefato temporário do GitHub Actions [45183947692](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45183947692); caminho `stage-synth-D-v127-versus-v128-bass-unison-wav`. O áudio de referência Iowa **nunca é incluído neste artefato**.

## Critérios de aceitação e reversibilidade

Exigir CI geral verde e testes de identidade de PCM, seleção do mesmo módulo Piano, nenhuma regressão de CC64 e release antiga com roteamento de Worklet real. A versão 1.12.8 será disponibilizada como EXPERIMENTAL; a próxima promoção dependerá de **escuta do titular (forte diferença de timbre versus violão)**, avaliação fora das referências in-sample e benchmark em AudioWorklet no Moto g04s/PC. Se o caráter ainda parecer violão, comparar/voltar para D v1.12.7, não manter mudança apenas por novidade.

**Fontes de construção acústica:** Gabriel Weinreich, *The Coupled Motions of Piano Strings* (triplas/duplas, prompt/aftersound); Yamaha [Design of the Strings Enriches the Sound](https://www.yamaha.com/en/musical_instrument_guide/piano/mechanism/mechanism004.html). Nenhum código/áudio dessas fontes foi copiado.
