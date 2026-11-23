# Stage Synth — Diagnóstico REAL do timbre D, sem alterar DSP (23/11/2026)

**Motivação:** após escuta da v1.12.5, o titular relatou: **“ainda está muito longe de um piano real, o timbre não se parece com um piano de verdade”**. Não considerar testes numéricos de estabilidade como prova de naturalidade musical.

**Medição concluída no CI:** [GitHub Actions run 45115134998](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45115134998), job `iowa-diagnostic`; **15 arquivos originais AIFF Steinway B/Iowa**, cinco notas C2/C3/C4/C5/C6, **pp/mf/ff**, SHA256/tamanho/codec confrontados com [manifesto auditado](../research/commercial_audio/iowa_steinway_b_verified_original_sha256.json) antes de extrair métricas. Arquivos AIFF e float intermediário armazenados **somente temporariamente** no runner e removidos. **Nenhuma gravação incorporada à aplicação.**

Artefato numérico de 15 casos: `stage-iowa-d-real-timbre-numeric-only` (não contém audio), gerado por `scripts/analyze_reference_audio.mjs` e `scripts/extract_iowa_spectral_targets.mjs`. O artefato do CI é retido por sete dias; a origem, a metodologia e os hashes ficam documentados. `scripts/print_real_timbre_gaps.mjs` relata as diferenças de cada parcial.

## Resultado objetivo: D não preserva o conteúdo harmônico grave

| Nota real | Intervalo observável de diferença de forma espectral A/B/C/D† | Diagnóstico principal |
| --- | --- | --- |
| C2 (MIDI 36) | D **38,7 dB em mf** (7 parciais de espectro sustentado comparáveis) | O Steinway B real tem **harmônicos 2–7 fortíssimos em relação à fundamental**; D distribui energia principalmente para a fundamental e enfraquece progressivamente os demais. No ataque mf, o 6º parcial real é **+26,4 dB** em relação à fundamental, D **−23,4 dB**: falta aproximadamente **49,8 dB** de relação espectral. |
| C3 (MIDI 48) | D **31,3 dB em mf** (7 parciais comparáveis) | Persistem graves excessivamente centrados na fundamental e forte falta de harmônicos altos. |
| C4 (MIDI 60) | D **13,7 dB em mf** (6 parciais comparáveis) | Primeiro par de harmônicos relativamente próximo no ataque; 6º e 7º muito fracos (aprox. **−17,9/−24,2 dB** contra o original). |
| C5 (MIDI 72) | D **4,9 dB em mf** (3 parciais comparáveis) | Não extrapolar o número para “realista”: poucos parciais sustentados são detectáveis, e outros ataques/velocities geram erros maiores. |
| C6 (MIDI 84) | **Sem média confiável** (0–1 parcial sustentado comparável) | Não atribuir erro global artificial. No mf, o 2º harmônico de D está em **−13,4 dB**, contra **−26,2 dB** do original na janela curta; há **excesso de brilho nesta componente**. |

† Desvio médio absoluto **dos parciais identificáveis e suficientemente fortes**, nunca índice de semelhança perceptiva. O analisador não conhece a força do martelo, posição/calibração física da ponte nem a resposta acústica isolada da sala. Janelas FFT e início por detector são aproximações; a origem foi gravada com **dois microfones KM84 em sala não anecoica**. A escala de velocity Stage para `pp/mf/ff` não foi identificada: nesta medição, os motores foram renderizados **sempre com o mesmo speed 80/127**, para isolar a comparação da forma espectral; isso **não valida a curva de dinâmica**.

## O que **não** concluir destes números

- Não dizer que o timbre “está melhor” porque testes passam ou porque uma nota isolada atinge um índice baixo.
- Não dizer que C2 exige aumentar agudos por **equalizador global**: C6 apresenta um problema no **sentido oposto**, e a intensidade real pp/mf/ff altera fortemente o espectro dos graves.
- Não chamar os ajustes dos parciais de “força do martelo medida”. O som registrado mistura martelo, cordas, ponte/tampo, radiadores, microfones e sala. Uma transformação inversa única **não identifica a física de cada componente**.
- Não determinar B por número de picos apenas. As estimativas finitas de C2/C3/C4 variaram entre capturas: **desvios observados podem ser seleção de pico/ruído/interferência, não rigidez da corda**. O analisador não confirmou a afinação independente de cada original.
- Evitar utilizar n acima do piso de ruído como “alvo confiável” no agudo. A janela de C6 contém poucos parciais mensuráveis com confiança.

## Uma direção testável para o motor D — após esta fase de diagnóstico

1. **Criar um perfil de excitação/radiação efetiva por registro**, derivado somente de amplitudes harmônicas observadas nos originais Iowa (dados numericamente transformados), interpolando entre C2–C6 e níveis pp/mf/ff **marcados como aproximações**. Ajustar os MODOS DO NÚCLEO, não apenas adicionar EQ/room reverb.
2. Empregar **correções limitadas, suaves e por parcial**, com controle de headroom, energia total e descontinuidades entre teclas. Em frequências onde as medidas são fracas/inconclusivas, permanecer com um modelo geral em vez de inventar um alvo.
3. Validar novamente todo o conjunto original de 15 arquivos, separando **ajuste in-sample** (âncoras usadas) de **controle fora das âncoras** (notas/velocidades não usadas), e preservar comparação D anterior vs candidato, além de A/B/C. Verificar ataque e duplo decaimento; só promover mediante escuta do usuário.
4. **Nenhum arquivo de terceiros com restrição NC/AGPL importado**, nenhum sample WAV incorporado, e sem tocar nos motores A/B/C/FX/MIDI/seletores sem autorização adicional. **R-GATEs 0/7 completos**, polifonia 32–64 não homologada no hardware.

**Este commit produz dados de diagnóstico, não altera a sonoridade da v1.12.5.** É uma etapa deliberada de evidência antes do próximo ajuste.
