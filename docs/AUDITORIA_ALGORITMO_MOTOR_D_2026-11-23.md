# Stage Synth D — auditoria técnica do algoritmo e otimização antes de v1.12.7
**23/11/2026 | revisão de fontes primárias e código `main` @ `8d2b6d759c3c89a36e652e1ae64206e1df05c294`.**

**Escopo:** o usuário confirmou avanço no médio-agudo de D v1.12.6, mas graves ainda com caráter de violão. Pesquisa técnica e otimização **antes** de novo DSP. Este PR produz somente **diagnóstico, benchmark e decisões; não altera som, motores A/B/C, UI, FX, MIDI, presets ou versão**.

## Decisão curta

**Preservar a síntese modal existente; não trocar tudo por waveguide/FDTD agora.** Melhorar o **grave** com **martelo de contato não linear**, **modo longitudinal/precursor do grave**, **evolução real de parciais**, e depois **acoplamento passivo ponte–tampo**, avaliando cada componente isoladamente. Primeiro eliminar desperdícios de CPU. **Sem incorporar código de terceiros** e sem declarar física medida onde só existe áudio de microfone.

## A. Achados confirmados no código atual

| Criticidade | Evidência verificável | Consequência e correção proposta |
| --- | --- | --- |
| P0 / timbre | `physical-piano-hybrid.js::noteOn`: `hybridContactTime` ajusta fator espectral `contact` no instante do note-on; o modo é inicializado por seno, e `v.impact` apenas decai exponencialmente. **Não existe estado integrando deformação/força do martelo F(t).** | Martelo é hipótese física importante para o caráter percutido. Comparar **pulsos de excitação causais de 0–12/12–36ms** em C2/C3 e escuta cega; não aplicar EQ global. |
| P0 / grave | Não há **variáveis de vibração longitudinal** ou ressonadores excitados por acoplamento transversal↔longitudinal nos graves, apesar da evidência acústica de parciais fantasmas. | Testar poucos ressonadores longitudinais em notas graves **apenas**; reconhecer que phantom partials também podem surgir no tampo/estrutura e não assumir causalidade exclusiva. |
| P0 / corpo | `render` usa `this.body.step(dryL*.65,dryR*.65)` e soma `wet` ao sinal seco; `PianoResonanceBody` calcula `reaction`, mas D **não o utiliza**. Além disso, o `dry` de D mistura osciladores irradiados e ruído, não é grandeza física calibrada de velocidade da ponte. | **Não simplesmente conectar `reaction` ao modo**: unidades/impedância/energia não estão identificadas. Desenvolver um adaptador passivo de força–velocidade e testar energia no caso extremo antes de habilitar retorno. |
| P0 / sustentação | `baseT60/(1+.052*n*n+.08*f/1000)` impõe decaimento por parcial estático, uníssonos com dois ressonadores/decays apenas nos `paired` iniciais. | Dados de C2 mf mostram relativo do 6º parcial +25,82→+22,12 dB no original vs +18,99→+12,33 dB em D nas quatro janelas temporais. A evolução do modo/ponte precisa de mais atenção que ganho instantâneo. Ver diagnóstico já aprovado [graves](PRONTIDAO_GRAVES_MOTOR_D_V127_2026-11-23.md). |
| P1 / descontinuidade e nível | `single=key<37` altera estrutura em MIDI 36→37 sem mapa de cordas verificado. Para cada `a` duplicado, o código usa `a*.63` e `a*.37`, mas contabiliza **`power+=a*a`**; a soma das potências das duas parcelas é `(.63²+.37²)*a² = .5338*a²`, **~−2,73dB**, desconsiderando interferência/coerência. | Há erro estrutural potencial de normalização e salto de timbre entre notas. Medir 35–49 e escolher normalização coerente para modos pareados, sem concluir que a divisão física correta seja C2/C#2. |
| P1 / controles | `updateVoice` altera `v.brightness`, porém `render` **não lê esse campo**; mudar brilho durante uma nota sustentada não recalcula o espectro. | Controle contínuo pode não agir sobre notas existentes. Criar teste de comportamento de parâmetro antes de corrigir, sem retocar modos A/B/C. |
| P1 / código morto | `HYBRID_QUALITY.eco.bodyDivisor=6`, mas o construtor fixa `PianoResonanceBody({divisor:4})`; `setQuality` ignora `q.bodyDivisor`. | A opção de economia **não reduz custo do corpo como sugerem seus metadados**. Corrigir ou remover parâmetro somente após avaliar aliasing e ressonância, não simplesmente baixar a taxa sem antialias. |

### B. Custo computacional: limites verificáveis (não benchmarks em hardware)

- **Cada ressonador é atualizado em 48.000 amostras/s.** `eco`: até 12 parciais + 3 duplicados (15 modos) × 32 vozes ≈ **23,0 milhões de atualizações modais/s**. `balanced`: 17+4=21 × 48 → **48,4 milhões/s**. `studio`: 23+5=28 × 64 → **86,0 milhões/s**. São **limites superiores**; a interrupção de parciais por Nyquist reduz o custo nas teclas agudas. Os números são contagens de iterações, **não FLOPS nem tempos medidos**.
- `render` chama `this.random()` **em todas as amostras de cada voz ativa**, mesmo depois de `v.noise` decair até praticamente zero. Com 64 vozes, até **3,07 milhões de chamadas de PRNG/s**, evitáveis sem mudar a resposta audível se o ponto de corte for medido e controlado.
- A carga do **ressonador simpático compartilhado** é aproximadamente 176 modos × 12kHz = **2,11 milhões de atualizações/s** (mais 12 modos de tampo) independentemente de quantas notas estão realmente soando. Melhorar silêncio/gates e descartar modos sem contribuição verificável; o sistema compartilha corpo, o que é uma escolha eficiente.
- `Math.tanh` estéreo por amostra equivale a **96.000 chamadas/s** a 48kHz. Só otimizar (aproximação monotônica/lookup) após **A/B com limite de erro e picos**, porque substituir `tanh` pode mudar cor e dinâmica.
- A alocação das matrizes de estado e blocos é antecipada, um acerto. Há alocação pontual com `done.splice(0)` / mensagem ao finalizar vozes; não é o principal gargalo, mas deve ser monitorada no AudioWorklet por picos de GC.
- Com blocos de 128 amostras/48kHz, o prazo teórico é **2,667ms** para a **cadeia de áudio completa**, não só o D. Medir custo **p50/p95/p99/worst** de 32/48/64 vozes em dois acordes sintéticos. `scripts/benchmark_piano_d_cpu.mjs` + workflow gravam baseline **Node/Linux** sem alterar DSP; **isso não homologa Chrome, Windows nem Moto g04s**. Repetir em Chrome DevTools WebAudio/Tracing no dispositivo real e observar capacidade de renderização/xruns/GC.

### B.1. Resultado medido em CI (somente Node/Linux, sem DSP alterado)

[Execução GitHub Actions 45154233484](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45154233484), `node scripts/benchmark_piano_d_cpu.mjs` a 48kHz, 128 amostras, 360 blocos medidos por cenário e 32/48/64 vozes. **Esta execução NÃO demonstra que a aplicação cumpre deadline no navegador ou no Moto g04s.**

| Perfil/cenário | Ressonadores ativos | Atualizações modais/s | p95 | p99 | Maior bloco observado |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eco 32 / graves repetidos | 417 | 20,0 milhões | 0,305 ms | 0,482 ms | **8,623 ms** |
| Eco 32 / teclado amplo | 431 | 20,7 milhões | 0,245 ms | 0,254 ms | 0,497 ms |
| Equilibrado 48 / graves repetidos | 904 | 43,4 milhões | 0,358 ms | 0,410 ms | 0,441 ms |
| Equilibrado 48 / teclado amplo | 874 | 42,0 milhões | 0,348 ms | 0,411 ms | 0,538 ms |
| Estúdio 64 / graves repetidos | 1.597 | 76,7 milhões | 0,546 ms | 0,560 ms | 0,715 ms |
| Estúdio 64 / teclado amplo | 1.487 | 71,4 milhões | 0,517 ms | 0,529 ms | 0,560 ms |

**Interpretação correta:** há margem **na média e p99 deste runner**, mas o pico 8,623 ms (>3× o orçamento teórico de 2,667 ms/bloco) surgiu apenas no primeiro cenário, possivelmente devido a JIT/GC/escalonamento — **causa não medida**. Não atribuir a falha à síntese nem garantir que haveria glitch em Chrome. Medições devem incluir **cold start/recompilação do JIT**, aquecimento, trocas de qualidade e notas, e perfil navegador real com ruído ambiental e FX.

**Otimização adicional confirmada pela literatura:** sistemas não lineares podem simplificar gradativamente o modelo quando a vibração perde energia; não há necessidade de calcular todos os parciais acima do limiar audível durante toda a sustentação. Primeiro implementar uma estratégia **sem degraus/estalos** (crossfade e testes) que elimine ressonadores apenas quando sua contribuição ao som esteja inequivocamente desprezível; em modelo futuramente bidirecional, considerar reexcitação. Referência: Julius Smith, *Nonlinear Piano Strings*, https://www.dsprelated.com/freebooks/pasp/Nonlinear_Piano_Strings.html .

### C. Pesquisas que mudam o caminho do algoritmo

1. **Banco modal/transversal/longitudinal é uma arquitetura válida em tempo real.** Bank, Zambon e Fontana, *A Modal-Based Real-Time Piano Synthesizer*, IEEE TASLP 18(4), 809–821 (2010), https://home.mit.bme.hu/~bank/publist/taslp10.pdf. Physis Piano comercial emprega técnicas modais e waveguides **customizadas**, não um único algoritmo universal: Zambon, Gabrielli e Bank (AES 2013), https://aes.org/publications/elibrary/elibrary-page/?id=16678 . **Não migrar o Stage a C++/Rust/FDTD automaticamente.**
2. **Vibrações longitudinais nos graves são audíveis.** Bank & Sujbert, *A Piano Model Including Longitudinal String Vibrations*, DAFx-2004, https://www.dafx.de/paper-archive/details.php?id=ouFQlPrPh-wW3ku1hJcTjg . Modelo misto: corda transversal + poucos ressonadores longitudinais não lineares. Pesquisa perceptiva até aproximadamente A3: https://pubmed.ncbi.nlm.nih.gov/20815427/ . **Limite causal:** parciais fantasmas também ocorrem com cordas abafadas e excitando apenas o tampo; ver https://pubmed.ncbi.nlm.nih.gov/29092614/ .
3. **Martelo não linear e redução de custo são compatíveis.** Chabassier, Chaigne e Joly, modelagem integral acoplada, https://juliettechabassier.perso.math.cnrs.fr/public/focus/2023/piano/ ; força de contato não linear. Balázs Bank & László Sujbert, *On the Nonlinear Commuted Synthesis of the Piano*, DAFx-2002, https://www.dafx.de/paper-archive/details/yL8RbflysbijGmR3zFXxGg : calcular pulsos físicos de martelo num modelo auxiliar e aproximá-los por filtro digital de baixa ordem **em vez de simular toda a malha por voz**. Fonte de princípio, **não copiar código ou parâmetros sem direitos**.
4. **Pontes/uníssonos e duas fases de decaimento importam mais que chorus arbitrário.** Weinreich (KTH), https://www.speech.kth.se/music/5_lectures/weinreic/motion.html ; Bank, *Accurate and efficient modeling of beating and two-stage decay*, https://dsp.mit.bme.hu/eng/userfiles/publikaciok/bank_mosa01a.pdf . Preferir modelo reduzido estável, com energia e estágios fast/slow observáveis.
5. **A não linearidade muda a afinação durante notas fortes.** Bank, *Energy-based synthesis of tension modulation in strings*, DAFx-2009, https://www.dafx.de/paper-archive/details/UT_LgR-mKR3hBlOyJx1WXw . Glide de pitch controlado por energia é um experimento futuro de baixo custo, **após** resolver ataque e parciais essenciais; não adulterar tuning sem referência.
6. **Somboard e processamento eficiente.** Smith, *Commuted Piano Synthesis*, https://www.dsprelated.com/freebooks/pasp/Commuted_Piano_Synthesis.html : filtragem comutada separa partes do sistema e pode trocar resposta de alta ordem por poucos filtros + excitação; como o som de Iowa inclui sala/microfones, não afirmar IR de ponte medida. A v1.12.7 não exige convolução longa nem novos arquivos no produto.
7. **Medir CPU no lugar certo.** Google Chrome, *Profiling Web Audio apps in Chrome*, https://web.dev/articles/profiling-web-audio-apps-in-chrome : deadline ~2.67ms, métricas de render capacity, GC, `about://tracing` categorias `audio`, `webaudio`, `blink_gc`, `v8.execute`. Nenhum benchmark Node/Linux de CI substitui aparelhos reais.

## D. Ordem e portões objetivos para a v1.12.7

| Etapa isolada | Critério de progresso | Critério de reprovação/rollback |
| --- | --- | --- |
| **G0 — medir antes** | CI 118 testes + matriz 15/15 com hashes, gravar CPU atual Node, preparar perfil no dispositivo. Congelar PCM de C4/C5/C6 do D v1.12.6 como comparação. | Sem benchmark/rastreabilidade; tentar alterar 3 subsistemas simultaneamente. |
| **G1 — martelo** | Sintetizar pulso causal proporcional a velocidade em baixo C1–C3; revisar transiente 0–12/12–36/36–100ms e usuário ouvir corpo de piano. | Estalo/clipping, nota soa como corda dedilhada, diferenças positivas só no FFT longo, C4–C6 pioram. |
| **G2 — longitudinais** | Acoplar 2–4 modos longitudinais por nota grave com excitação quadrática limitada, característica de instrumento auditivamente reconhecível; analisar componentes adicionais sem atribuir física não medida. | Metálico artificial, energia crescente sem entrada, excesso de ressonância e CPU incompatível. |
| **G3 — caudas/uníssono/ponte** | Ajustar relações por parcial em janelas 20/220/520/850ms, garantir prompt + aftersound, sem saltos MIDI 36→37, possível retorno passivo da ponte **com unidades/ganho estudados**. | Instabilidade energética, desafinação, notas presas, perda do médio-agudo, vazamento CC64. |
| **G4 — desempenho/escuta** | 32 vozes Moto g04s / 64 PC sem xruns sob sustain e troca de motor em navegador; testes auditivos A/B sem FX, incluindo notas fora das cinco âncoras para separar treino de avaliação. | Browser real falha, C4–C6 perdem qualidade, CPU/GC ultrapassam orçamento; ausência de avaliação auditiva. |

**Proteger e manter:** A/B/C/Clássico e v1.12.6 histórica; **motor D só no módulo Piano**, nunca novos menus. Dados numéricos derivam de 15 AIFF Steinway B com SHA256 já auditado; **sem gravações no pacote ou código AGPL/NC de terceiros**. Gates globais de pesquisa física/comercial **0/7 integralmente aprovados**; limites de alocação 32/48/64 ainda não são desempenho certificado.

**Decisão:** **pesquisa geral encerrada para esta etapa**. Apenas um roteiro de experimentos rastreáveis e banco de CPU, mantendo módulo médio-agudo intacto. A v1.12.7 só será lançada como nova experiência após passar pelos portões e ter avaliação de escuta.
