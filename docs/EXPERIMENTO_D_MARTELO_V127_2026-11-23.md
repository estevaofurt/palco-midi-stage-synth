# Stage Synth v1.12.7 — experimento de martelo grave para escuta A/B

**23/11/2026 | escopo experimental autorizado, exclusivamente motor D dentro do módulo Piano Acústico.** Esta é uma iteração física com avaliação **mista**: não representa um Steinway calibrado, nem uma melhoria global comprovada por medição ou escuta. A v1.12.6 histórica passa a usar snapshots físicos do D e seus dois módulos auxiliares, e a v1.12.7 usa o novo D. **A/B/C/Clássico e default C preservados**, sem novos painéis, categorias ou seleção duplicada.

## Alterações efetivas, somente MIDI 21–48 (C1–C3)

- **Antes (v1.12.6):** cada parcial da corda começava com deslocamento não nulo, e uma rampa simples revelava o sinal; ruído/impacto curto positivo era adicionado de forma independente.
- **Candidato (v1.12.7):** pulso causal de pressão de contato de martelo com forma de cosseno levantado, correspondente à compressão senoidal elevada ao quadrado, duração dependente da nota/velocidade/dureza do feltro; distribuição de energia por ressonador calculada da **transformada espectral fechada do pulso discreto**, em O(1) por parcial. Inicialização de corda com deslocamento zero e força aplicada ao longo dos primeiros milissegundos; ruído de impacto exponencial unilateral removido **apenas nos graves**; transmissão de radiação grave aumenta gradualmente (~5–7ms) segundo nota/velocidade, ainda uma aproximação.
- **MIDI 49–108** passa pelo mesmo algoritmo v1.12.6; teste de 45 configurações do C4 ao extremo agudo confirmou **3.240.000 amostras estéreo exatamente iguais** no GitHub, além de testes específicos importando diretamente snapshots imutáveis.
- **Não há** ressonadores longitudinais, F_h(t) com massa/velocidade/deformação resolvidos pela dinâmica completa ou resposta passiva bidirecional de ponte: é **um primeiro experimento isolado de excitação**, não conclusão da arquitetura.

## Evidência: ajuste do ataque melhor, parciais sustentados um pouco piores

O conjunto comparável tem **15 gravações originais do Steinway B/Iowa com SHA256 verificado**, em C2/C3/C4/C5/C6 × pp/mf/ff, sem WAV/AIFF embutido ou publicado. Nos mesmos dados já usados para o D v1.12.6:

| Métrica (erro absoluto relativo ao original) | D v1.12.6 | D candidato |
| --- | ---: | ---: |
| Envelope de banda larga de C2/C3 nos **0–12ms** (6 casos) | **3,58 dB** | **2,96 dB** |
| Magnitudes relativas de parciais na janela chamada `early` (FFT de 171/341ms, **não** 12ms) | **3,23 dB** | 4,30 dB |
| Magnitudes relativas de parciais em sustentação | **9,38 dB** | 10,49 dB |

**Leitura:** melhora modesta da FORMA TEMPORAL do ataque grave, **piora na correspondência do espectro**, sem prova perceptiva. A janela de FFT chamada “early” é longa. Não inferir força física de martelo a partir de áudio de microfone. O resultado é **in-sample** e referência dos microfones/sala Iowa. **Não promover D a default ou chamar v1.12.7 versão estável**. Comparar auditivamente com a v1.12.6 e, caso continue com som de violão ou tenha piorado, restaurar a v1.12.6 e passar ao próximo experimento isolado.

### Testes e proteção

- `tests/bass_hammer_v127.test.mjs`: força positiva de área 1, transferência analítica versus DFT exata, nota realmente excitada, CC64/stop/64 vozes finitas.
- `scripts/check_piano_d_candidate_v127.mjs`: 45 cenários de MIDI 49–108 × 3 velocities × 3 perfis de CPU, com **comparação amostra por amostra** contra o antigo `physical-piano-hybrid.js` recuperado do commit `3a104f...`; mudança deliberada só em C1–C3.
- `tests/piano_d_archive_v127.test.mjs`: confirma que o navegador em **`v1.12.6.html` seleciona verdadeiramente `physical-piano-hybrid-v126.js`** e módulos auxiliares congelados; `v1.12.7.html` escolhe código novo. Nomes de arquivos HTML históricos sozinhos não preservam JavaScript se todos importam a mesma URL mutável.
- `.github/workflows/piano-d-bass-candidate-v127.yml`: testes Node/sintaxe, comparação v126/v127, CPU por 128 amostras, 48 kHz e 32/48/64 vozes (Node Linux, **não certificação Windows/Moto g04s**).
- `.github/workflows/hybrid-d-iowa-timbre-diagnosis.yml`: download das 15 fontes originais somente no CI, SHA256, análise acústica e artefatos **somente numéricos**. A versão física completa, pedal meio curso, pontes 2×2 e direitos comerciais continuam a depender de R-GATEs globais: **0/7 integralmente fechados**.

## Próximo experimento após escuta

Se a alteração do ataque não eliminar o caráter de violão do grave, **não compensar com EQ, chorus, mais reverb ou boosts especulativos**. Experimento isolado seguinte: parcial/ressonador **longitudinal fracamente acoplado** à vibração transversal, com excitação não linear e amplitude limitada, acompanhado de medições de 0–100ms e trajetória dos harmônicos C2/C3. Só depois considerar decaimento rápido/lento, mapa físico das cordas e reação passiva do tampo.

**Prioridade absoluta:** preservar as notas médio-agudas já aprovadas em escuta, custo de CPU, 32/64 vozes disponíveis como alocação e os motores A/B/C/Clássico.
