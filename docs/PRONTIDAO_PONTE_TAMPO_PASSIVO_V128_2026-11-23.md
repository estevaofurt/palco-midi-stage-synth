# Stage Synth — v1.12.8: base mecânica passiva de ponte e tampo (PESQUISA, sem DSP público)

**Data:** 23/11/2026. **Base pública protegida:** Stage v1.12.7, commit `a610e6d6fe6e803d86650a298611efcaf46e2b35`. **Feedback do titular:** quatro comparações D anteriores ficaram quase iguais; componente agudo parece ruído, falta impressão de madeira, som "redondo" de violão. **Não chamar este trabalho de novo timbre pronto.**

## Resumo executivo

**Avanço científico/engenharia:** Foi construído e testado um sistema **mecânico de acoplamento REAL no nível de equações**, com duas polarizações de corda por nota, força distribuída na ponte e **apenas dois modos de tampo compartilhados por todas as notas**. Usa o método de **ponto médio implícito**, com balanço discreto de energia calculável e não crescimento energético espontâneo. A otimização aplica complemento de Schur à estrutura em estrela de acoplamento, reduzindo solução de matrizes densas para **O(N)** no número de coordenadas de corda.

**Limite decisivo:** valores de massa, rigidez, amortecimento e frequências de placa são **normalizados e ilustrativos**. A saída `boardVelocity` **NÃO é pressão sonora [Pa]** e tampouco identificamos mobilidade real da ponte **velocidade/força**. Ainda não há timbre confiável ou domínio comercial identificado. **O motor D v1.12.7, UI, MIDI, FX, presets e A/B/C/Clássico NÃO foram alterados**. A PR #26 com "madeira" artificial permanece draft/não mesclada.

## Modelo e verificações formais

### Núcleo de referência 4DOF (`research/passive-string-bridge-cell.mjs`)

`M·x'' + C·x' + K·x = F_h(t)`, com **M diagonal positiva**, **C diagonal não negativa**, e K como soma de termos de mola aterrada positiva mais `k_ij (x_i-x_j)^2/2`, logo positiva definida. Quatro coordenadas: duas de cordas (fast/slow) e duas de placa/ponte.

O integrador é ponto médio implícito, com `A = M + Δt C/2 + Δt² K/4` (SPD), fatorização de Cholesky feita no construtor, nenhum array criado por amostra.

**Lei de energia verificável por bloco/amostra:**

```text
E(n+1) - E(n) = Δt * [ F_h(mid) * v_string(mid)
                      - Σ_i damping_i * v_i(mid)^2 ]
```

Com força nula, `E(n+1) ≤ E(n)`. Isso **é verificável numericamente** e evita simplesmente misturar ressonâncias que gerem energia arbitrária. Não resolve por si só afinação/sonoridade natural.

### Núcleo compartilhado O(N) (`research/shared-passive-piano-bridge.mjs`)

N notas * 2 polarizações de corda + **dois modos únicos de tampo**. As cordas só se acoplam umas às outras por meio dos dois estados compartilhados. Forma uma matriz de rigidez em estrela, e a integração implícita pode ser reduzida a um sistema 2×2 por **complemento de Schur**, evitando fatorização densa `(2N+2)×(2N+2)` por amostra.

**Condição física formal:** `E = Σ( m_i v_i²+k_i x_i² + k_c_i(x_i-X_ponte)²)/2 + E_tampo`. A ponte não pode irradiar quando nenhuma corda a excita e não há deslocamento inicial. Ao excitar uma corda, a ponte recebe energia e pode reexcitar outras notas por sua ligação mecânica. Testes incluem 44,1/48/96kHz, 0/.12/.8 de acoplamento, excitação externa e período sem força, mais 56 notas em comum.

**Limite para polifonia:** Um piano real tem cordas permanentemente ligadas à ponte, mesmo sem teclas acionadas. O experimento permite um subconjunto de cordas para medir custo; ao desenvolver o produto, será preciso tratar a carga da escala completa e o amortecimento seletivo pelas teclas/pedal. Não declarar `64 células` como `64 vozes homologadas`.

## Resultados de CI — fonte [run 45170997523](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45170997523)

- **139/139 testes Node** no projeto completo: 127 existentes + 12 testes novos. Testes dedicados **6/6 do núcleo 4DOF** e **6/6 do núcleo compartilhado**; passaram balanço de energia, dissipação, zero-input, chaveamento, transmissão simpática, matrizes SPD e 44,1/48/96kHz.
- Proteção obrigatória no workflow: `git diff --exit-code a610e6d... -- [motores públicos, UI, package.json]` — **sem diferenças**.
- **32 e 64 notas são benchmark Linux de solver isolado**, sem Piano D original, efeitos ou AudioWorklet real. Medidas `p95` em 128 amostras/48 kHz:

| Quantidade | Núcleos 4DOF independentes / nota | Um tampo com O(N) acoplamento | Ganho de desempenho na comparação |
| --- | ---: | ---: | ---: |
| 16 notas | 0,4122 ms | 0,0418 ms | 9,86× |
| 32 notas | 0,7777 ms | 0,0788 ms | 9,87× |
| 64 notas | 1,4939 ms | 0,1556 ms | 9,60× |

**Comparação NÃO é entre áudios equivalentes:** a primeira versão teria uma placa independente por voz (fisicamente impróprio); a segunda tem placa compartilhada. Estes números mostram viabilidade do **custo mecânico**, não ganho de performance completo do app nem melhora perceptiva. Janela teórica de 128 amostras @48kHz = 2,667 ms para **toda a cadeia**, e ainda não medimos PC/Android.

## Evidência física e direitos — leitura primária

1. **Bank & Karjalainen**, *Passive admittance synthesis for sound synthesis applications*, em https://dsp.mit.bme.hu/eng/userfiles/publikaciok/bank_acoust08.pdf . Combina pesos não negativos em modos passivos e alerta que encaixar um filtro arbitrário na terminação pode produzir sistema ativo/instável. **Nossa formulação M/C/K e ponto médio implícito foi escrita de forma original; não copia o artigo nem usa dados da guitarra em vez de piano.**
2. **Julius O. Smith**, *Digital Waveguide Theory* / *Piano Synthesis*, https://www.dsprelated.com/freebooks/pasp/Digital_Waveguide_Theory.html e https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html . Uma corda não é automaticamente uma saída de alto-falante; ponte/tampo/radiação formam caminho causal importante.
3. **Yamaha** (explicação pública de engenharia), https://www.yamaha.com/en/tech-design/research/technologies/piano-simulation/ . A fabricante resolve interações martelo/cordas/ponte/tampo/estrutura/ar, mas o custo de uma simulação completa não implica que seja viável no AudioWorklet em 64 vozes.
4. **AudioLabs Erlangen** (2023), https://audiolabs-erlangen.de/resources/MIR/2023-ISMIR-PianoSynth/ . IRs de tampo Yamaha C3 medidos por alto-falante de contato e microfones em sala. Não são mobilidade ponte força/velocidade nem o som de um único piano isolado da sala. **Licença comercial dos IRs ainda não auditada**.
5. **Niko Plath**, https://zenodo.org/records/3271370 e https://zenodo.org/records/3274772 : colunas sincronizadas de **força no leito da tecla (N)**, **aceleração da ponte (m/s²)** e **pressão em microfones (Pa)**; 50kHz, conjunto grande. **A página pesquisada mostra campo de licença sem valor explícito; não supor CC BY por padrão do Zenodo**. Não baixar, importar, redistribuir, publicar áudio ou usar parâmetros comercialmente sem direitos específicos do proprietário.

## GATE do próximo avanço: identificar a transferência física, não EQ

1. **Obter permissão comercial explícita** ou medir os próprios dados: aceleração da ponte e pressão binaural/estéreo, mesma execução, nota/velocidade e posição. Separar `a_ponte(t)` de `F_tecla(t)`. Aceleração→pressão pode estimar transferência radiativa relativa `H_{p,a}(f)`; **não é mobilidade mecânica** `Y(f)=v_ponte/F_ponte` porque não se mediu `F_ponte`.
2. **Identificar condições iniciais do martelo e excitação da corda**, mapear velocidade/força e força real da ponte quando possível. Estimar filtros positivos reais e ajustar `M/C/K`/modos com passividade e tratamento das duas polarizações, usando notas de validação **fora** das âncoras de calibração.
3. Converter **pressão radiada como saída** do modelo passivo: `F_martelo -> corda -> reação ponte <-> placa -> H_(pressão/velocidade)`. A eventual via direta do som da corda exige uma física e um ganho justificáveis. Sem confundir `plateVelocity` e `Pa`.
4. Validar ataques (0–12ms) e trajetórias de parciais (171/341ms), comb de posição do martelo, taxa de decaimento, comparações ABX por registro/velocidade, e **depois** executar no navegador PC/Android a 32–64 vozes sem xrun.
5. **Não aumentar parciais agudos inventados** nem introduzir "som de madeira" por modos fixos/ruído. A primeira melhoria real audível exige que o usuário reconheça um piano em vez de violão. Som atual D v1.12.7 continua inalterado e disponível para comparação.

**Decisão: física estrutural validada; timbre NÃO aprovado.** Este PR pode entrar como **infraestrutura de pesquisa autônoma**, mas não deve ser apresentada como v1.12.8 implementada nem homologada. R-GATEs **0/7 integralmente fechados**.
