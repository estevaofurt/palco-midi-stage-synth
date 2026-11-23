# STAGE SYNTH — Piano V4.0: recomeço do zero, física verificável e escuta como gate

**23/11/2026 — decisão do titular:** o som da pesquisa E3.4 está **mais distante de um piano acústico** que os protótipos anteriores e lembra um sintetizador de piano elétrico. O titular pediu **recomeçar o motor do zero** e buscar referências científicas. Portanto, E3.4 e o conjunto E2/E3 **não serão promovidos como arquitetura do novo instrumento**. O objetivo continua **som gerado apenas por modelagem física**, sem reprodução de gravações, SF2, IR medidos em convolução ou impacto PCM.

## Ação tomada

- **Nova branch V4:** `research/piano-v4-restart-physical-20261123`, derivada diretamente do commit estável `626f5089aad95d22b63283b2b6babbfc8f7f17ad` (v1.12.8, **NÃO** da PR #37).
- Código independente `research/piano-v4/stiff-string-hammer.mjs` **sem imports** dos motores antigos.
- Testes independentes `tests/piano_v4_stiff_string_hammer.test.mjs` e diagnóstico `scripts/piano-v4/diagnose-single-string.mjs`.
- CI `.github/workflows/piano-v4-physical-restart.yml` executa `npm run check` (inclui regressões atuais), verifica diff em arquivos do aplicativo e publica resultados numéricos.
- **O motor Stage público não foi alterado**: A/B/C/D/Clássico, MIDI/CC64, interface, FX, presets e todos os arquivos da `main` estão preservados.

## O problema nos ciclos anteriores

1. **Meta equivocada:** dezenas de testes de estabilidade/energia e malhas maiores não demonstram que o áudio se parece com piano. O titular rejeitou E3.0 e E3.4 pela escuta. A aprovação do usuário é requisito, não detalhe.
2. **Geometria arbitrária:** massas modais enormes, poucos modos de corda, impedância ponte/tampo inventada, rigidez do feltro sem medições reais e modos de placa insuficientes não reproduziam uma estrutura física de piano.
3. **Saída acústica incorreta:** parte da E2.9/E3.0 irradiava *velocidade da ponte localizada* como se fosse *uma área inteira vibrante do tampo*.
4. **Ataque espúrio ou apagado:** a E3.4 aumentou a força mecânica mas quase não alterou a razão RMS ataque/corpo no áudio radiado. É preciso resolver a transferência real de forças, não sobrepor click ou exagerar a dureza.
5. **Polifonia fictícia:** demos de acordes E3.x somavam saídas de simulações independentes, sem múltiplos martelos não lineares conectados ao mesmo tampo.

## Referências técnicas que DEVEM orientar o projeto

1. **Chabassier, Chaigne & Joly (JASA, 2013), “Modeling and simulation of a grand piano”**: martelo–corda com compressão não linear dissipativa; corda rígida; tampo como placa ortotrópica dissipativa e efeitos de pontes e nervuras; comparação com gravações de Steinway D. https://pubmed.ncbi.nlm.nih.gov/23862839/
2. **Chabassier, Chaigne & Joly (ESAIM M2AN, 2014), “Time domain simulation of a piano, Part 1: model description”**: cordas 1D rígidas, vibrações transversais e longitudinais, perdas dependentes de frequência e acoplamento entre partes e propagação no ar. https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
3. **Anders Askenfelt & Erik Jansson (1990), “From touch to string vibration”**: duração real do contato martelo–corda determina parte importante do espectro; exemplos em ~1 ms mas varia conforme tecla e dinâmica; medir e calibrar por nota e velocidade, não escolher um único impulso arbitrário. https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html
4. **“A compact physics-based model of the piano”, DAGA (2016)**: separação auditável de blocos martelo/feltro, corda, acoplamento e tampo. https://pub.dega-akustik.de/DAGA_2016/data/articles/000537.pdf
5. **“Physical Modeling of Piano Sound” (2024)**: revisão de subsistemas incluindo feltro, haste do martelo, cordas, tampo, ar e recinto; usar para identificação dos graus de liberdade relevantes, não copiar código de terceiros. https://arxiv.org/abs/2409.03481
6. **Pianoteq/Modartt (apenas referência de produto, não código/áudio):** parâmetros de dureza de martelo, ressonância do tampo, uníssono e interação de cordas/pedal devem responder dinamicamente. https://www.modartt.com/pianoteq_features

Sem copiar código proprietário, software de terceiros ou sons gravados para o motor. Gravações existentes do usuário podem ser usadas **apenas externamente para medir semelhança de espectro, envelopes, batimentos e escuta A/B**, respeitando direitos de uso.

## Nova primeira implementação: UMA corda, SEM saída “piano” enganosa

`StiffStringHammerV4` representa mecanicamente uma corda de aço **com dimensões explícitas em SI** e **32 modos transversais dispersivos**, mais um martelo físico em movimento, compressão do feltro com potencial elástico unilateral e reação de mão dupla sobre a corda.

Equações:
- `μ=ρπr²` (massa linear), `EI=Eπr⁴/4` (rigidez de flexão de seção circular)
- `ω_n²=(T (nπ/L)²+EI (nπ/L)⁴)/μ`
- `m_modal=μL/2`, `F_contato = ∂[k max(δ,0)^(p+1)/(p+1)]/∂δ`
- O solver usa ponto médio implícito para cordas e gradiente discreto do potencial do feltro para energia, com amortecimento modal positivo e balanço `E_total + dissipação = E_inicial`.

**Parâmetros de demonstração (NÃO medidos em Steinway/Yamaha)**: C4 (261,625565 Hz); L=0,62m; raio=0,48mm; densidade=7850kg/m³; E=200GPa; martelo=8g; velocidade inicial 0–3,8m/s; 48kHz.

**CI [45245875334](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45245875334): 176/176 testes aprovados, baseline do aplicativo inalterada.**
Diagnóstico: tensão calculada ~597,79N, massa modal ~1,761g, inarmonicidade B~0,000358. A fundamental é 261,625565 Hz. Duração de primeiro contato aproximada **3,3ms a 0,8 m/s e 3,2ms a 2,5 m/s**. Esse contato precisa de calibração: é longo em relação a alguns exemplos acústicos e demonstra que ainda há muito a ajustar. Não afirmar que o timbre está correto.

**CRÍTICO:** a saída `bridgeShearForceN()` calcula uma força em uma extremidade com condição fixa, **não** representa a ponte móvel tampouco pressão no ar. Não gerar ou divulgar um WAV como piano nesta fase. A corda precisa ser acoplada a uma ponte de mobilidade calibrada e a um tampo físico antes de termos áudio de piano.

## Novo fluxo com gates auditivos e físicos explícitos

| Etapa | Hipótese e entrega | Gate obrigatório |
|---|---|---|
| V4.0 (agora) | Corda rígida em SI + martelo recíproco, sem código anterior | estabilidade, afinação, dispersão, contato e energia; nenhuma alegação de piano |
| V4.1 | Calibração de UMA nota C4: massa efetiva, contato e perdas por referência física; modelagem da haste se necessária | espectro e duração de contato com erro explicável; velocidades pp/mf/ff |
| V4.2 | Mobilidade/impedância de ponte e tampo com modos físicos excitados pelo ponto correto | saída radiativa a partir da *velocidade real do tampo*, nunca velocidade pontual de ponte |
| V4.3 | WAV original de uma nota C4 com ataque, corpo e decaimento completos | usuário reconhece piano acústico; comparar escuta e espectro/envelope contra referências, sem usar sample playback |
| V4.4 | Graves/agudos + 2–3 cordas por nota + batimentos e dupla inclinação do decaimento | validação auditiva C2/C3/C4/C5/C6 e dinâmica |
| V4.5 | Múltiplos martelos + uma ponte e um tampo compartilhados, pedal e abafadores | chords reais, CC64 e 32–64 notas; CPU/AudioWorklet sem underruns em hardware real |
| V4.6 | Integração opcional com fallback ao motor estável | regressão A/B/C/D/Clássico, FX, MIDI, presets, UI, dados, reversibilidade |

**Critério central:** qualquer alteração que piore a escuta **é rejeitada**, mesmo que haja economia de CPU ou mais modos e testes matemáticos verdes.

## Conclusão

O projeto não está abandonado; **o modelo anterior está rejeitado**. O avanço da V4 é sólido **somente na mecânica elementar**, sem afirmação de realismo sonoro. Recomeçar do zero significa preservar a estabilidade do aplicativo e reconstruir o mecanismo com propriedades e métricas verificáveis antes de complexidade. PR V4 permanecerá draft até uma nota reconhecível de piano passar na avaliação de escuta.
