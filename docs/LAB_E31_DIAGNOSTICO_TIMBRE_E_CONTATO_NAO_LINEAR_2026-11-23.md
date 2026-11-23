# Stage Synth E3.1 — Rejeição auditiva do E3.0 e correção de direção física

**23/11/2026. Status:** falha de fidelidade reconhecida pelo usuário — **"o som apresentado não tem timbre de piano"**. O sucesso numérico da E3.0 NÃO equivale a aprovação auditiva. **Não promover** E3.0, nenhuma mudança no DSP público D v1.12.8 ou em A/B/C/Clássico. Nenhum sample gravado usado para gerar áudio físico.

## Falhas identificadas no próprio modelo

1. **Muitas cordas são representadas com harmônicos insuficientes:** o modo padrão mantém apenas cinco parciais para notas até MIDI60 e dois acima. Uma nota percutida de piano acústico pode exibir numerosos harmônicos resolvíveis durante o ataque.
2. **Deficiência flagrante no espectro C3/Dó3:** auditoria E3.1 de sinal gerado via mesma mecânica da E3.0, pressão relativa sem calibração: segundo harmônico ≈ −1,82 dB, terceiro +4,17 dB, quarto −21,37 dB, **quinto −60,79 dB** (amplitudes relativas à fundamental). Inspeção offline anterior da gravação **fornecida pelo próprio usuário**, como referência *externa* e não motor, identificou o quinto perto de −8 dB. **Diferença aproximada de 53 dB**, sem equiparação de velocity, captação, nível RMS ou ambiente: evidência de deficiência de conteúdo harmônico, não comparação controlada de fidelidade.
3. **Erro conceitual na radiação E2.9/E3.0:** `piano.bridgeVelocity` é a velocidade da **ponte localizada** mas foi tratada como um modo seno simétrico que vibra em **toda a superfície** de 1,22×0,92m. `piano.boardPanelVelocity` foi projetada no modo antissimétrico. Isso não representa a geometria física real do piano. No teste C3 de 0,03–0,27s, a razão RMS `v_painel/v_ponte` foi **0,04690**, ou seja, a velocidade de painel modelada é ~21,3 vezes menor.
4. Se corrigirmos apenas a origem da radiação, usando exclusivamente `boardPanelVelocity` como primeiro modo seno simétrico, o **quinto harmônico cai ainda mais (−92,93 dB)**. Portanto, **a correção do roteamento sozinha NÃO resolve o timbre**; não mesclar `plate-only` isolado como se fosse uma melhoria.
5. Simulação tem **apenas dois graus mecânicos de ponte/tampo** e um pulso prescrito de impacto `sin²`, sem interação completa martelo-feltro-corda por compressão e realimentação dinâmica. Aumentar a malha de Rayleigh (48→192 patches) mostrou convergência numérica, mas não cria os modos físicos faltantes.

`research/diagnose-piano-source-e31.mjs` gera a prova por notas fisicamente sintetizadas, sem carregar WAV. `scripts/audit_piano_source_e31.mjs` grava `e31-physical-source-diagnostic.json`. `tests/diagnose_piano_source_e31.test.mjs` confirma os problemas como **falha de critério musical**, com cinco testes. São intencionalmente marcadas as duas variantes como **não aprovadas para promoção**, sem ocultar as limitações.

## Experiência de ajuste rejeitada

Uma varredura matemática local (não integrada) incluiu 18 combinações de contato do martelo (1,25/1,8/2,4 ms), expoente de acoplamento mecânico (−1,5/−0,9/−0,4) e projeção da força (−0,7/−1,1), com mais modos (12 graves/8 agudos); foi comparada externamente às notas C3/C4/C5 do WAV do usuário, **sem distribuir essas gravações**. A menor discrepância média entre os perfis normalizados de oito harmônicos (excluindo a fundamental) ficou **~26,8 dB RMS** nas três notas, e alguns candidatos exageravam fortemente os harmônicos 2–4. Não é um ajuste calibrado e não constitui um piano aprovado. **Nenhuma dessas variantes entra na versão pública.**

## Primeiro componente de física corrigida — E3.1

`research/nonlinear-felt-contact-e31.mjs` implementa um núcleo **isolado** com contato unilateral:
`F = k·max(δ,0)^p`, `E_contato = k·max(δ,0)^(p+1)/(p+1)`, com massa de martelo, massa modal simplificada da corda, mola e perda viscosa positiva. O impacto tem velocidade inicial de martelo e segue a compressão, em vez de prescrever um pulso arbitrário. **Ainda não acoplado a 88 cordas nem ao tampo, logo não produz piano**.

O núcleo de demonstração, com parâmetros **ilustrativos não medidos**, a 96kHz, apresentou:
- martelo a 1 m/s: força de contato máxima ~37,8 N, duração ~0,948 ms;
- martelo a 3 m/s: força máxima ~175,9 N, duração ~0,615 ms;
- energia (E + perdas) perto do valor inicial, erro relativo ~0,000005 em teste de 0,25 s com amortecimento positivo.

Os números são da configuração de teste, não propriedades comprovadas do feltro comercial de qualquer piano. `tests/nonlinear_felt_contact_e31.test.mjs` contém cinco verificações (não atração sem contato, relação força/velocidade, energia conservativa, dissipação positiva e entrada inválida). Os testes servem como ponto de partida para acoplar o impacto ao solver passivo.

## Redesenho aprovado como direção, não como produto acabado

1. **E3.2 — Contato martelo–cordas:** acoplar a força não linear ao conjunto de modos/ondas da corda com posição física de impacto, estabilização de energia e contato dependente de tecla e velocity.
2. **E3.3 — Corda dispersiva com perdas dependentes da frequência:** substituir os cinco/dois modos insuficientes por representação modal ou waveguide de corda rígida com número de modos, polarizações e amortecimento calibrados e controlados por custo.
3. **E3.4 — Tampo distribuído:** representar modos espaciais fisicamente ativos e excitação na linha da ponte; só radiação de **velocidade de superfície**, sem usar a velocidade localizada da ponte como uma placa inteira. Investigar realimentação de carga acústica.
4. **Portas objetivas de fidelidade:** análise harmônica C2/C3/C4/C5, dinâmica ataque/sustain, decaimento por parcial, ressonância CC64, aliasing e comparação de áudio nivelada contra gravações de referência **apenas no diagnóstico**. Requer aprovação auditiva do usuário; métricas não substituem a escuta.
5. **Performance:** testes de 32/48/64 notas com solver+radiação no AudioWorklet em Windows/Android. O benchmark Node/Linux não é homologação de produção.

**Pesquisas relacionadas (não usar áudio nem código de terceiros automaticamente):**
- Chabassier et al., [Modeling and simulation of a grand piano (JASA, 2013)](https://pubmed.ncbi.nlm.nih.gov/23862839/) — contato não linear dissipativo, transmissão onda–ponte–tampo.
- [Time domain simulation of a piano, Part 1 (2014)](https://www.numdam.org/item/M2AN_2014__48_5_1241_0/) — cordas rígidas com perda, não linearidades e sistema acoplado.

**CI E3.1:** [execução inicial do diagnóstico 45228386410](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45228386410) — **226/226 testes**, checagem do áudio/interface públicos e gerador de diagnóstico. A validação adicional do núcleo não linear será registrada no resultado da próxima execução.

**Decisão:** E3.0 rejeitado por qualidade sonora; PR #37 continua DRAFT; não gerar outra suposta 'versão de piano' até a arquitetura física mudar e um A/B externo indicar aproximação real. R-GATEs comerciais 0/7. Preservar `main` v1.12.8 e todas as funcionalidades existentes.
