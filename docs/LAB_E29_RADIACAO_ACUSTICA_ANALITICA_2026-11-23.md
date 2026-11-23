# STAGE SYNTH — E2.9: radiação acústica analítica, 100% modelagem física

**23/11/2026.** PR #37, pesquisa isolada. O titular exige que o piano seja **gerado somente por modelagem física**. E2.6/E2.7 sampling permanece descartado como arquitetura, PR #38 fechada sem merge. Nenhuma WAV externa é carregada neste novo motor.

## Cadeia funcional

1. **Ataque:** pulso positivo sen² da E2.3, aplicado diretamente às coordenadas mecânicas das cordas (força normalizada, martelo não identificado).
2. **Cordas:** 88 teclas ligadas, até 5 parciais por polarização nos graves e 2 nos agudos, 592 coordenadas numéricas no perfil padrão, molas recíprocas, amortecedores/CC64.
3. **Ponte/tampo:** dois graus mecânicos compartilhados, integrados via método do ponto médio implícito passivo. E2.9 expõe como saídas independentes as velocidades *no ponto médio do passo* da ponte e do segundo modo de tampo, sem modificar a força, massa, amortecimento, rigidez ou balanço energético.
4. **Ar:** `research/analytic-soundboard-radiation.mjs` integra por quadratura em **48 regiões espaciais** a **primeira integral de Rayleigh** para superfície em placa rígida infinita:
   `p(r,t) ≈ ρ₀/(2π) Σ (ΔS_i/R_i) · d[v_i(t−R_i/c)]/dt`.
   Dois formatos modais de placa são prescritos por funções seno `sin(πu)sin(πv)` e `sin(2πu)sin(πv)`. Distância física de cada região até os microfones, retardo `R_i/c`, atraso fracionário e queda `1/R_i` originam o estéreo. Não há convolução IR gravada, EQ musical, sample attack, SF2, PCM de piano nem adição de osciladores secos.
5. **WAV de avaliação:** `scripts/render_pure_physical_e29.mjs` gera **13 segundos PCM16, 48 kHz, estéreo** de arpejos e acordes com pedal, sem qualquer entrada WAV. Normalização por **ganho global único** e fades pequenos contra estalos. `research/pure-physical-radiation-e29.mjs` controla a sequência e o rastreio de energia.

**Fundamento técnico externo da fórmula, apenas texto/equações, nenhum material sonoro derivado:** [Rayleigh integral e pistão em baffle — Euphonics](https://euphonics.org/4-3-2-the-rayleigh-integral-and-the-baffled-piston/); [campo temporal do pistão em baffle — Acta Acustica](https://doi.org/10.1051/aacus/2020002).

## Resultados confirmados

[CI E2.9 com áudio e CPU, execução 45222938800](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45222938800):

- **217/217 testes Node passaram, 0 falhas**. Inclui nove novos testes: causalidade da viagem no ar, linearidade, queda aproximada `1/R`, simetria e antissimetria estéreo, ausência de amostras, escrita WAV, determinismo, robustez de entrada, energia passiva.
- **WAV físico puro gerado:** `e29-physical-piano-analytic-air.wav`, 2.496.044 bytes, PCM16 estéreo 48 kHz, 13 s; SHA256 `f4f3c19de2c5d4bfad780dd4c633b3841330dd5357481cd3d74da1eee9b12d45`. Fica no artefato de Actions `stage-e2-88-key-node-benchmark`, ao lado do WAV mecânico E2.8.
- **Balanço de energia da rede mecânica:** erro relativo `3,75×10⁻¹⁴`; a radiação é **somente de ida**, não realimenta a impedância acústica ao sólido. Portanto, o teste de passividade é da mecânica, **não da interação acústico-estrutural completa**.
- **Benchmark offline Node/Linux — solver de 88 teclas + radiador de 48 regiões por amostra, blocos de 128 frames/48 kHz**:

| Notas percutidas | P50 do bloco | P95 do bloco | Orçamento ideal de 128 frames |
|---|---:|---:|---:|
| 32 | 0,695 ms | 0,706 ms | 2,667 ms |
| 48 | 0,681 ms | 0,789 ms | 2,667 ms |
| 64 | 0,681 ms | 0,692 ms | 2,667 ms |

O algoritmo **sempre mantém as 88 teclas e 592 coordenadas conectadas**, independentemente da quantidade de notas percutidas. Valores não monotônicos são possíveis por aquecimento/cache/ruído do runner. Esses tempos **não** certificam PC/Android, AudioWorklet com overhead do sistema operacional, pedal real, FX ou ausência de underruns.

[Baseline do aplicativo 45222502018](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45222502018): verde; checagem de diff de DSP, UI, presets e MIDI publicados: nenhuma mudança. **Main = v1.12.8**.

## Lacunas obrigatórias e limitações (sem propaganda enganosa)

- `SharedPassiveModalPiano` ainda trabalha com **coordenadas generalizadas não calibradas em m/s**. Portanto, embora a fórmula da radiação converta *velocidades SI* em pressão acústica SI, nosso WAV ainda é apenas **pressão relativa aproximada**, não Pa medidos nem nível SPL real.
- Os modos em senos e as dimensões/radiador infinito refletem **um painel idealizado**, não o formato/ripas, contorno e fechamento de um piano real; o modo antissimétrico pode criar um estéreo plausível, mas não validado.
- Quadratura de 8×6 regiões é **muito grosseira** para a distribuição espacial de frequências altas; testes com malha mais refinada, convergência espacial e parâmetros reais são necessários.
- O radiador unidirecional despreza carga acústica de retorno, radiação traseira, estrutura do aro, padrões complexos de diretividade e sala. **Sem áudio de piano gravado incorporado** não significa simulação física completa.
- O espectro audível dessa saída **não foi validado perceptivamente**, nem comparado em escuta nivelada com o E2.8 ou referências externas. Não declarar melhoria timbral comprovada e não alterar D até testes rigorosos de C2/C3/C4–C6 e hardware.
- Medições externas de instrumentação, quando autorizadas, podem informar **parâmetros escalares e geometria**; **nenhum WAV medido ou IR acústica gravada será misturado na síntese**.
- R-GATEs comerciais **0/7**; PR #37 draft. Direção E2.9: avanço físico/engenharia em pesquisa, não publicação comercial.

## Próximo experimento e critério de promoção

1. Convergência de malha `8×6 → 12×8 → 16×12`, e teste de diferenças de pressão/CPU por frequência e posição, verificando alias espacial.
2. Priorizar fisicamente perdas e mobilidade complexa da ponte; **identificar os parâmetros geométricos de radiação por dados e leis da física**, não por equalização arbitrária.
3. Criar A/B físico E2.8 vs E2.9, sem amostras externas como entrada, e validação por escuta do titular de **caráter de piano**, gravações reais somente como referência externa.
4. Medir em Chrome/Edge/Android com AudioWorklet e 32/48/64 notas, CC64, 0 underruns; somente depois discutir integração opcional em D.

**Decisão:** manter pesquisa 100% física e preservar integralmente o Stage Synth público.
