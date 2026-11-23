# Stage Synth — preparação para o próximo modelo D (v1.12.7): grave de piano, não violão

**Data:** 23/11/2026. **Base verificada:** `main 7182d9c9b2c6acc585411436ef65f064e5020d0d`, Stage v1.12.6. **Origem da prioridade:** avaliação auditiva do titular: *“Tivemos progresso, na região médio agudo começou a parecer com piano real, o grave ainda se parece com um violão. Vamos terminar a preparação para a próxima versão do modelo.”*

**Decisão:** próxima iteração de modelo será **D (experimental) somente**, concentrada em **C1–C3 (MIDI 24–48)** e preservando a evolução positiva de C4–C6. **Este PR é somente preparação/medição/testes — não altera DSP, UI, MIDI, FX, preset, volume nem código de áudio.** A/B/C/Clássico permanecem intactos. O usuário autorizou anteriormente aperfeiçoar D por etapas, mas não liberou a versão v1.12.7 nem alegação comercial de realismo.

## Diagnóstico de engenharia — não confundir hipótese com evidência

| Suspeita (no código v1.12.6) | Impacto auditivo plausível | Evidência e estratégia |
| --- | --- | --- |
| **P0: martelo não excita um sistema dinâmico de cordas.** `hybridContactTime` alimenta um ganho estático por parcial, `v.impact` é um termo exponencial positivo de curta duração e `v.noise` é ruído filtrado. Não existe estado resolvendo `F_h(t)`/compressão, nem a excitação em onda propagante. | Percepção de corda percutida/dedilhada e falta do corpo imediato do martelo. | **Código confirmado, causalidade auditiva ainda hipótese.** Analisar energia 0–12, 12–36, 36–100ms e faixa acima de 900Hz, sem atribuir esses valores a força de martelo medida. Se a lacuna persistir, testar pulso causal de martelo com contato e rigidez dependentes do toque; comparar e reverter se o som piorar. |
| **P0: corpo/ponte de mão única.** `render` mistura o modal `dry` a `PianoResonanceBody.wet`, mas **não aplica `body.reaction` de volta aos estados modais**: é um modelo aditivo de corpo/ressonância, não ligação mecânica completa. | Menos sensação de caixa acústica/ponte viva e evolução de timbre artificial. | **Código confirmado**. Priorizar modelo reduzido de radiador + ponte acoplados e **passivos**, mantendo custo do modo Econômico e teste de estabilidade, sem importar IR/código de terceiros. Não prometer mobilidade 2×2 medida. |
| **P0: decaimento parcial insuficiente.** `baseT60/(1 + .052*n*n + .08*f/1000)`, com par rápido/lento somente para poucos parciais; amplitudes nascem todas de uma vez e não recebem alimentação da ponte. | Timbre de violão no grave, ataque sintético e pouca evolução de ressonância. | **Fórmula confirmada; culpa exata a medir.** Comparar trajetórias 0,02/0,22/0,52/0,85s e envelope de energia por nota/dinâmica; então validar nova parametrização de decaimento parcial, mantendo batimentos naturais. |
| **P1: transição de uníssonos arbitrária.** `single=key<37`: uma população modal para C2 (MIDI 36), outra com par desde C♯2 (37). | Mudança brusca entre teclas adjacentes e riqueza tímbrica incompleta em alguns graves. | **Código confirmado, mapeamento REAL de cordas NÃO confirmado.** Antes de alterar a divisão, identificar mapa de uma/duas/três cordas do piano de referência ou adotar aproximação contínua e documentar que não é uma escala Steinway medida. Testar MIDI 35–49 sem degraus artificiais. |
| **P1: espectro ajustado em 15 âncoras, não transientes.** 5 dó × pp/mf/ff foram usados para formar `piano-hybrid-calibration.js` e avaliar a própria aderência. | Bom médio-agudo/FFT, mas ataque do grave e variação por nota ainda artificiais. | **In-sample confirmado.** Preservar ganho anterior (**20,30→3,23dB de erro harmônico de janela curta, não percepção**) e acrescentar teste temporal/instrumental. Considerar 2–3 notas graves **fora das âncoras** como aceite quando houver direitos e origem verificados; não declarar validação externa usando os mesmos 15 arquivos. |

### Correção importante sobre o diagnóstico anterior

A janela de `measureEarlyPartials` começa em 0,018s, mas usa 16.384 pontos @48kHz nas notas graves: **duração ≈341ms**; em notas altas usa 8.192 pontos: **≈171ms**. **Isso não mede isoladamente o impacto inicial do martelo.** A v1.12.6 corrigiu o *espectro integrado de parte do ataque/começo da sustentação*, **não** comprovou a dinâmica física dos primeiros 10ms. Esta distinção encerra a lacuna metodológica sem descartar a melhora já ouvida.

## Preparação executável (CI real, sem alterar som)

- `scripts/diagnose_piano_bass_envelope.mjs` analisa **15 AIFF originais Steinway B/Iowa**, pré-validados por **SHA256**, com áudio **somente no runner temporário**. Mede energia relativa por janelas **0–12ms, 12–36ms, 36–100ms, 100–220ms, 220–450ms, 450–900ms, 900–1400ms**; alto-passante 900Hz para transiente; FFT **171ms** com início 20/220/520/850ms para evolução dos parciais. Dados são **diferenças numéricas**, não som nem medidas diretas de força de martelo.
- O mesmo script renderiza **D atual (v1.12.6)** em pp/mf/ff com MIDI nominal 32/80/120, cuja equivalência a martelo real é **desconhecida**; normalização pelo RMS 100–220ms elimina nível absoluto (necessário para comparar forma da nota, mas não intensidade física).
- `tests/piano_bass_preparation_v127.test.mjs` valida janela temporal real, estabilidade sob mudança de nível, diferença entre impactos lentos/rápidos, trajetórias dos parciais, finitude de saída e ausência de escrita em DSP.
- Workflow original `.github/workflows/hybrid-d-iowa-timbre-diagnosis.yml` mantém fonte oficial, hashes, conversão no runner, ausência de áudio no artefato. Publica **`bass-temporal-diagnostics.json`**, além dos relatórios espectrais já existentes. Nunca adicionar AIFF/WAV ao Git ou ao app.

## Decisões para implementação posterior (modelo D v1.12.7, não neste PR)

**Ordem mínima de experiências isoladas** (A/B com D v1.12.6 congelado):
1. **P1 — martelo e precursor de grave**: testar excitação causal / contato de martelo desacoplado do ruído mecânico; primeira diferença deve se concentrar nos **0–100ms**, sem boost global de agudos ou reverb. Só incorporar se houver melhora perceptiva e não houver piora sistêmica nos registros protegidos.
2. **P2 — ponte/radiação/tampo**: substituir gradualmente o corpo aditivo por transferência passiva e possível reação à corda (mesmo callback), com estado de energia estável, evitando realimentação WebAudio entre blocos.
3. **P3 — cordas graves**: calibrar evolução dos parciais, dupla cauda, polarizações/uníssonos e borda 36↔37 com dados rastreáveis; incluir complexidade de enrolamento apenas onde as gravações a sustentarem, não inventar parâmetros de Steinway.
4. Só então avaliar com piano **Yamaha C5** usando suas referências originais (separadamente, não afirmar Yamaha e Steinway são o mesmo instrumento).

**Proteção de regressão:** A/B/C inalterados; D v1.12.6 preservado; C4–C6 **não podem regredir auditivamente**. Nas medições, usar a mesma matriz Iowa 15/15 (ataque, decaimento, amplitudes por parcial), comparar evolução por blocos e rejeitar instabilidade, clipping, notas presas, vazamento de pedal, descontinuidade entre semitons ou custo exagerado de callbacks. Manter 32/48/64 apenas como *alocação comprovada* até aferição real Moto g04s/PC. A aprovação **depende da escuta do usuário**, inclusive do reconhecimento do grave como piano, e não de um valor universal inventado de dB.

**Estado comercial:** nenhuma alteração de licença, corpus ou PCM no produto; 65 arquivos originais de sete fontes previamente auditados, não embutidos; **0/7 R-GATEs integralmente fechados**. Este documento é **sinal verde para preparar experimentos**, não homologação nem decisão automática de publicar novo DSP.

## Fontes primárias utilizadas, sem ampliar a pesquisa genérica

- KTH, *Acoustics of the Piano — Introduction*: https://www.speech.kth.se/music/5_lectures/introd/introd.html (martelo não linear, cordas graves enroladas, radiação do tampo)
- KTH, Gabriel Weinreich, *The coupled motion of piano strings*: https://www.speech.kth.se/music/5_lectures/weinreic/motion.html (duas polarizações, aftersound, ponte)
- KTH, Klaus Wogram, *The strings and the soundboard*: https://www.speech.kth.se/music/5_lectures/wogram/decay.html (T20 inicial, dependência de impedância da ponte)
- Iowa MIS arquivo original & direitos: https://theremin.music.uiowa.edu/MIS.html ; fonte/15 hashes no manifesto `research/commercial_audio/iowa_steinway_b_verified_original_sha256.json`.
