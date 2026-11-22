# Stage Synth — referências externas para fidelidade acústica dos motores A/B/C
**Pesquisa pública: 22/11/2026** · **Status: análise e plano; sem alteração do DSP nesta etapa**.

## Escopo, base examinada e cautelas

Comparação sobre a raiz do repositório `estevaofurt/palco-midi-stage-synth` no estado **v1.12.4**, confirmada pela consulta direta a `patches.js`, `acoustic.js`, `physical-piano.js`, `physical-piano-legacy.js`, `piano-worklet.js`, `piano-resonance.js` e `docs/ESTADO_ATUAL.md`.

- **A — Claude (modal):** `piano-worklet.js`, parciais quase-harmônicos/inarmônicos com perfis por registro, **limite explícito de 32 vozes**. É a implementação modal adaptada que já consta no repositório, não uma cópia verificada do código original de Claude.
- **B — Stage físico anterior:** `physical-piano-legacy.js` é o código da v1.9.5 com identificador diferente de AudioWorklet, referência **relatada pelo usuário sem estalos no PC**.
- **C — Novo Stage mecânico:** `physical-piano.js` + `piano-resonance.js`, incorpora tampo, amortecedores, cordas simpáticas e reação de ponte limitada, sem comprovação perceptual de piano real.
- **Clássico:** síntese legada por Web Audio, manter como fallback.

**Falhas concretas ainda identificáveis:** `physical-piano.js` e `physical-piano-legacy.js` conservam ganhos de parciais arbitrários (por exemplo `japanese.partials[1]=8.0`), curvas de decaimento globais e dispersão baseada em allpass de primeira ordem; `piano-worklet.js` tem `MAX_VOICES=32`. Auditoria de v1.9.6 apontou inarmonicidade B aproximada ~4×10⁻⁷ em Dó4 (ordem de grandeza 1000× inferior ao alvo ~4×10⁻⁴ usado no scorecard), além de inversão de brilho por velocidade e decaimento excessivamente uniforme. **Esses alvos são hipóteses iniciais, não parâmetros universais de todos os pianos**.

Os WAVs `Japanese.wav`, `American.wav`, `Felt.wav` e `Upright.wav` são referências musicais com **efeitos originais**, não notas isoladas e secas; não podem medir isoladamente os parâmetros físicos das cordas. **Não incorporar os WAVs privados ao GitHub.**

## Fontes científicas prioritárias

### 1) Julius O. Smith III — *Physical Audio Signal Processing* (Stanford/CCRMA), especialmente "Piano Synthesis", "Commuted Piano Synthesis" e "Dispersion Filter-Design"

Fontes: 
- https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html
- https://www.dsprelated.com/freebooks/pasp/Commuted_Piano_Synthesis.html
- https://www.dsprelated.com/freebooks/pasp/Dispersion_Filter_Design_I.html

**Constatações sustentadas:** a rigidez exige filtros de dispersão allpass; técnicas de síntese comutada incorporam boa parte do filtro do tampo/carcaça na excitação, reduzindo o custo em tempo real; o martelo apresenta contato não linear e pulsos mais curtos/brilhantes com velocidades maiores. A dispersão pode ser aproximada eficientemente acertando os primeiros parciais audíveis. Existe referência a função Faust `piano_dispersion_filter`.

**Aplicação proposta:** base principal de B/C: cascata de allpasses calibrada por B(nota), perda espectral por parcial e excitações sintéticas multivelocidade. Para preservar ressonância dinâmica de pedal/teclas, usar síntese comutada **parcial** (parte fixa no ataque + poucos modos compartilhados de maior Q) e não eliminar totalmente o acoplamento vivo do tampo.

### 2) Bank, Avanzini, Borin, De Poli, Fontana & Rocchesso (2003) — "Physically Informed Signal-Processing Methods for Piano Sound Synthesis: a Research Overview"

Fonte pública: https://home.mit.bme.hu/~bank/publist/jasp03.pdf
Descrição bibliográfica em HTML: https://www.dafx.de/paper-archive/search?author%5B%5D=Bank%2C+B.&p=1&w=author

**Aplicação proposta:** arquitetura de guia de onda rígida, modelo de força martelo-corda, filtros de perda, acoplamento, projeto de tampo multirrate/multibanda. Não adicionar dezenas de modos do tampo por nota; reduzir ordem total com modelos compartilhados.

### 3) Bank & Sujbert (2002) — *On the Nonlinear Commuted Synthesis of the Piano*

https://www.dafx.de/paper-archive/details/yL8RbflysbijGmR3zFXxGg

**Aplicação:** relacionar o impacto não linear do martelo com síntese comutada de baixo custo e a identificação de respostas medidas. Atenção: não é um algoritmo pronto para copiar sem ajustes.

### 4) Zambon, Lehtonen & Bank (2008) — *Simulation of Piano Sustain-Pedal Effect by Parallel Second-Order Filters*

https://dafx.de/paper-archive/2008/papers/dafx08_37.pdf

**Aplicação:** ressonadores de segunda ordem compartilhados ajustados a respostas do registro de cordas e tampo, com diferentes coeficientes de acoplamento; a ressonância simpática não se resume a reverberação de sala. Serve para reavaliar o `piano-resonance.js`.

### 5) Frontiers in Signal Processing (2023) — *Physics-informed differentiable method for piano modeling*

https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full

**Aplicação:** duas etapas de decaimento (prompt e aftersound) resultam da interação entre modos/cordas e ponte; inarmonicidade e perda dependente da frequência; estimar parâmetros offline, sem exigir rede neural em tempo real. O artigo nota explicitamente que bom erro espectral, sem componentes ruidosos, não assegura fidelidade perceptiva.

### 6) International Audio Laboratories Erlangen (ISMIR 2023) — *Towards Differentiable Piano Synthesis Based on Physical Modeling*

https://audiolabs-erlangen.de/resources/MIR/2023-ISMIR-PianoSynth/

**Aplicação:** modelo modal + filtro de tampo, aprendizagem/ajuste *offline* da excitação por nota, com IR de tampo de Yamaha C3 medida em quatro pontos de excitação (apenas uma IR utilizada no modelo descrito). Interessante para construir uma camada de ajuste paramétrico do motor A; não indica que usaremos áudio de piano gravado como samples.

## Referências de produtos comerciais (recursos observáveis, não código-fonte)

- **Modartt Pianoteq:** https://www.modartt.com/pianoteq_features e https://www.modartt.com/pianoteq_whats_new — múltiplas cordas por tecla, batimentos, rigidez, martelo, ressonância simpática, tampo, propagação, controle de velocity; Pianoteq 9 divulgou modelo de tampo revisto com mais espacialização. **Não revela arquitetura privada completa.**
- **Roland V-Piano:** https://www.roland.com/global/products/v-piano/ — parâmetros públicos incluem unison tune, hammer hardness, cross/string/damper/soundboard/key-off resonance. **Não permite inferir o código DSP proprietário.**
- **Yamaha VRM:** https://faq.yamaha.com/ca/s/article/000025704?language=en_US — comportamento de cordas e tampo conforme teclas e profundidade do pedal. É um modelo de ressonância, **não prova que todas as vozes do sistema sejam geradas por modelagem física**.

## Projetos abertos para estudo e comparação, sem copiar código sem revisão de licença

1. **Daniel Podrazka, Physics-Based Piano Synthesis (2026):** https://github.com/danielpodrazka/piano e https://piano.daniep.com — no navegador, combina síntese modal, parciais inarmônicas, decaimento em duas etapas, martelo dependente de velocity, múltiplas cordas, respostas de tampo e comparação com referências. O próprio projeto declara limites em graves/agudos; **MIT no código**, mas arquivos de referência possuem licenças próprias (Salamander CC BY 3.0, Rhodes CC BY-NC 4.0). É o estudo de engenharia mais próximo da nossa UI/AudioWorklet, não uma solução homologada ao Stage.
2. **Dussek (Rust):** https://github.com/ccoors/dussek e https://ccoors.github.io/dussek/ — piano físico em Rust, CLAP/VST3/standalone; parâmetros de instrumentos derivados de várias bibliotecas de referência; código **AGPL-3.0**. Estudar arquitetura e testes, mas não copiar trechos diretamente para projeto sem decidir efeitos de copyleft.
3. **Unsampled Piano (Rust):** https://unsampled.mgth.fr/ — modelo físico com martelo/cordas rígidas/tampo, saída estéreo, **GPL-3.0**. Útil como demonstração de subsistemas e comparação auditiva independente.
4. **Open Piano (C++/JUCE):** https://github.com/michele-perrone/OpenPiano — código AGPL-3.0; o autor reconhece limitações de um fio por nota, ausência de tampo e problemas de afinação: útil para entender armadilhas, não como motor pronto.
5. **Faust Physical Modeling Toolkit:** https://faustlibraries.grame.fr/libs/physmodels/ — documentação e componentes DSP, incluindo dispersão e modelos modais. Conferir licença e eventuais exceções para código gerado antes de incorporar.
6. **Open-source browser comparison:** https://github.com/danielpodrazka/piano também mostra abordagem de Rhodes com FM física útil para etapa posterior dos elétricos.

## Bases de áudio para validação independente

- **MAPS** (Yamaha Disklavier + pianos sintetizados): https://adasp.telecom-paris.fr/resources/2010-07-08-maps-database/ e https://zenodo.org/records/18160555 — notas isoladas e MIDI de referência. Licença indicada **CC BY-NC-SA 2.0 FR**; uso restrito ao escopo da licença, sem republicar no Stage ou incorporar a produtos comerciais sem análise de direitos. Não é captura do Yamaha CFX solicitado.
- **MAESTRO:** https://magenta.withgoogle.com/datasets/maestro — performances sincronizadas de Disklavier e eventos MIDI (velocity, pedal etc.), útil para comparar fraseado/pedal/polifonia, **não substitui notas secas para ajuste de B/T60**. Licença **CC BY-NC-SA 4.0**.

## Orçamento de execução no navegador

- AudioWorklet processa blocos normalmente de 128 amostras; em 48 kHz ~2,67 ms para o *grafo inteiro*, incluindo FX e camadas. Não usar o tempo total de 1 segundo offline para alegar desempenho no Moto g04s.
- Mover parâmetros complexos/identificação e geração de kernels para fora do callback de áudio; prealocar tabelas/buffers; evitar GC e mensagens de alto volume dentro do processo.
- Experimentar módulo DSP compartilhado em **WebAssembly** (C++ ou Rust) após medir um perfil real. O Chrome recomenda WebAssembly como complemento de AudioWorklet, não é garantia automática de velocidade; comparar wasm vs JS em hardware real.
- Referências: https://developer.chrome.com/blog/audio-worklet-design-pattern e https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Using_AudioWorklet

## Plano técnico recomendado e verificações antes de editar o DSP

| Prioridade | Base | Mudança | Evidência necessária |
|---|---|---|---|
| P0 | A/B/C | Criar suíte acústica com notas C2/C4/C6 e 32/80/120 de velocity, mais sustain, release e cordas em uníssono | B por nota, desvios cents por parcial, envelopes por banda, T60 em duas fases, brilho ↑ com velocity, clipping |
| P1 | B e C | Substituir dispersão insuficiente por allpass em cascata e perdas dependentes da frequência; retirar reforço arbitrário de H2 | B próximo ao **medido** (não um único B global), espectro e brilho por velocity melhores em C2/C4/C6 |
| P2 | A | Calibrar perfis de parciais, ganho e decaimento (prompt/aftersound) de fontes autorizadas e elevar polifonia 32→64 com alocação adaptativa | 32/64 vozes audíveis sem perda de som, comparação A/B nivelada |
| P3 | B/C | Excitação de martelo curta, física e sensível a velocity com síntese comutada parcial; eliminar duplicação de pulsos/interferência destrutiva | Ataque forte mais rico que fraco; instrumentos não soam dedilhados; regressão de fase |
| P4 | C | Refinar tampo/ponte e amortecedores usando bancos reduzidos de ressonadores medidos/identificados e ressonância simpática ligada ao estado real do pedal | Mudanças audíveis on/off, níveis controlados, mono e estéreo estáveis, sustain crível |
| P5 | A/B/C | Adicionar comparação auditiva cega com notas em várias regiões e acordes de 32/64, mantendo a v1.9.5 de rollback | Relatório de preferência, CPU/estalos no PC/Moto g04s, sem regressão |

**Decisão de engenharia proposta:** não escolher um motor vencedor antes de testes. A é forte em controle explícito de B e decaimento, porém limitado em polifonia; B tem estabilidade relatada, mas ainda falha em inarmonicidade e espectro; C adicionou interação mecânica, mas não resolve os problemas de cordas. Melhor evolução provável: um **motor híbrido original** com modos/ressonadores calibrados onde forem mais eficientes, excitação comutada, cordas rígidas dispersivas quando couberem, e tampo/pedal compartilhados. A combinação precisa ser testada: não é garantia de fidelidade.
