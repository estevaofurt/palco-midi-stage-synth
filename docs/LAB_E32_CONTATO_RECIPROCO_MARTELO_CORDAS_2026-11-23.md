# Stage Synth — E3.2 | Contato não linear recíproco martelo–cordas com ponte compartilhada

**Data:** 23/11/2026. **Estado:** pesquisa isolada na PR #37. O usuário rejeitou corretamente o timbre E3.0 e exigiu som **gerado exclusivamente por modelagem física**. Esta etapa não é um novo piano aprovado, não integra a versão pública, não usa WAVs/SF2/PCM gravado na síntese.

## Mudança real da arquitetura

Até E3.1, a ligação entre a força do martelo e a rede de 88 teclas ainda dependia de um pulso `sin²` de duração predefinida. **A E3.2 remove esse pulso somente no novo caminho de teste**, por meio de `externalForceMode:true` do `SharedPassiveModalPiano`, sem modificar o modo anterior nem DSP público.

`research/coupled-nonlinear-hammers-e32.mjs` implementa um martelo de massa efetiva para cada tecla acionada, junto a **todas as coordenadas modais da mesma corda**, com reação mecânica igual e oposta. A compressão do feltro depende da diferença entre a posição do martelo e a soma das posições das cordas projetadas pela posição de impacto:

- `δ = x_martelo − Σ_j w_j x_corda,j`;
- `U(δ) = k · max(δ,0)^(p+1)/(p+1)` (**energia armazenada no feltro**, unilateral, não atrai corda separada);
- `F = [U(δ_depois)−U(δ_antes)]/[δ_depois−δ_antes]` (gradiente discreto implícito; força retorna ao martelo com `−F` e às cordas com `+w_j F`).
- A rede mecânica de 88 teclas e ponte compartilhada é resolvida pelo mesmo Schur positivo-definido da E2.3. Um complemento de posto 1 resume a influência da força sobre o deslocamento de contato, possibilitando tratar 1–64 martelos com contato recíproco e amortecimento passivo.
- Um método de Newton com limites e fallback por bisseção calcula a força sem substituir a física por uma forma de pulso inventada. A força é verificada por resíduo. **Sem simulação em dois sistemas independentes ou mistura posterior de ondas gravadas.**

**Unidades e limites:** a rede original E2.3 utiliza massas, acoplamentos e velocidades *generalizados e não calibrados em SI*. As massas do martelo, rigidez e localização de impacto E3.2 são parâmetros ilustrativos. A implementação **não garante que a relação de massas corresponda à de um piano acústico real**. Não interpretar `peakForce` como força N medida.

## Testes e evidências

`tests/coupled_nonlinear_hammers_e32.test.mjs` valida:

- fidelidade do modo antigo sem mudanças, além do modo externo que recusa `noteOn` com pulso prescrito;
- contato unilateral e conservação da energia potencial + cinética das cordas, do martelo e do feltro;
- força e energia de corda maiores para golpe de maior velocidade;
- abafadores e pedal CC64 modificando fisicamente a energia remanescente;
- acordes de 2, 8, 32, 48 e 64 teclas com reação de força e finitude;
- reataque como injeção **explícita de nova energia cinética**; ausência de dependência de samples, SoundFonts, WAV ou IR.

`scripts/benchmark_nonlinear_hammers_e32.mjs` e `scripts/diagnose_nonlinear_hammers_e32.mjs` verificam custo por contato e os harmônicos C2–C5 sem ler gravações. **Amostras externas são apenas referências de diagnóstico em escuta separada, não partes da geração.**

[**CI E3.2 otimizado — run 45232273314**](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45232273314) **250/250 testes Node aprovados**, benchmark, diagnóstico de harmônicos, a geração antiga de WAVs físicos, proteção por diff do DSP/UI público e fechamento de energia completos. [Regressão pública Stage 45232273136](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45232273136) também verde.

### Resultado do novo contato e diagnóstico sincero do timbre

Na C3 (MIDI48), o antigo martelo com pulso fixo alimentando apenas a coordenada **real do tampo** tinha quinto harmônico em **−103,49 dB relativos à fundamental**. A reação martelo–cordas E3.2 apresentou aproximadamente **−61,01 dB**: aumento relativo significativo do quinto harmônico **nessa comparação mecânica específica**, mas **ainda insuficiente** como caráter de piano. A referência do usuário em análise anterior sugeria cerca de −8 dB numa captação/velocity não pareada; **não equiparar diretamente valores ou inferir qualidade perceptiva**. C4 e C5 continuam com graves déficits de harmônicos devido à representação limitada de parciais e à estrutura de dois modos de tampo.

### Limite de desempenho

O primeiro solver escalar usava 36 passos de bisseção e 5 varreduras; em Node/Linux offline, 64 martelos custaram até **12,36 ms** no primeiro bloco 128 frames/48 kHz (orçamento ideal **2,667 ms**). A substituição por Newton analítico resguardado (3 varreduras, até 16 passos com critério de resíduo) preservou o balanço de energia em ~`10⁻¹⁴` nos testes de múltiplos contatos e reduziu esse primeiro bloco para **3,61 ms** com 64 martelos; após o contato, p95 **0,98 ms**. Entretanto **3,61 ms excede 2,667 ms** e o benchmark NÃO inclui radiação, FX, AudioWorklet, MIDI ou hardware real. Os tempos sofrem influência de JIT, runner e aquecimento. **Não afirmar 64 vozes aprovadas para execução ao vivo.**

## Estado e critérios de avanço

**E3.2 é um avanço de correção física, não de certificação do timbre.** Não gerar/publicar um novo WAV rotulado como piano melhorado antes de atacar os problemas centrais do instrumento:

1. **E3.3:** implementar cordas dispersivas com mais parciais fisicamente justificadas, perdas por frequência e geometria de impacto por região, com verificação de aliasing e custo.
2. **E3.4:** substituir a ponte distribuída fictícia por tampo com modos vibratórios físicos acoplados, irradiando exclusivamente velocidades de superfície; validar mobilidade e contato ar→estrutura.
3. A/B nivelado de C2/C3/C4/C5, sustentação e pedal, confronto com gravações de referência **somente para medição ou escuta**, nunca como voz do motor. Audição do usuário precisa reconhecer caráter de piano.
4. Benchmark 32/48/64 com DSP completo em PC/Android/AudioWorklet, sem underruns. Mudar public D só depois de evidência auditiva e de regressão.

A versão pública `main` permanece em **v1.12.8**, motores A/B/C/D/Clássico, MIDI, presets, FX e painel sem alterações; PR #37 continua **draft**. Os gates comerciais físicos continuam **0/7**. Os resultados antigos E3.0 continuam rejeitados pela escuta.
