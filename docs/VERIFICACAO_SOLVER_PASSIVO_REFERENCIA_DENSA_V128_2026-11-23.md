# Stage Synth — verificação independente do solver passivo de ponte/tampo

**23/11/2026. Base:** main v1.12.7, revisão posterior ao laboratório do PR #27.

## Objetivo

Conferir se a solução otimizada O(N) de `research/shared-passive-piano-bridge.mjs` realmente reproduz a discretização implícita de ponto médio de `M x'' + C x' + K x = F`, em vez de aceitar testes somente de balanço de energia (que podem não detectar erro de montagem do acoplamento). **Sem mudança no áudio público ou nos parâmetros de síntese.**

## Teste adicional

- `tests/piano_shared_bridge_dense_reference.test.mjs` constrói, de maneira independente, a matriz densa completa de massa, amortecimento, mola de cada corda–ponte e dois modos do tampo.
- Resolve `A v_mid = b` com **eliminação gaussiana com pivoteamento** a cada amostra, **sem reutilizar** o complemento de Schur, a fatorização ou arrays temporários da implementação otimizada.
- Compara saída do tampo, deslocamento e velocidade de cada polarização e dos dois modos de placa, amostra por amostra.
- Abrange 44,1/48/96 kHz, acoplamento zero/0,12/0,8, conjuntos de 1/3/5 notas e forças transientes em duas polarizações.
- Exercita o laboratório compartilhado com **88 teclas MIDI únicas (21–108)** e verifica energia não crescente em ausência de força, nas três taxas.

## Benchmark corrigido

`scripts/benchmark_shared_passive_bridge.mjs` anteriormente utilizava `21 + i % 28`, repetindo notas quando eram solicitadas 32 ou 64. Agora usa `21 + i` para **16/32/64 notas distintas**. O teste ainda representa somente o custo de equações mecânicas em Node/Linux, não a carga de um piano completo de 88 teclas, não o AudioWorklet, não a polifonia do palco com FX e MIDI, e **não compara qualidade acústica equivalente** entre os dois métodos.

## Critério de aceite

1. `npm run check` e testes originais passam no CI.
2. O novo teste de solução densa independente passa em todas as configurações.
3. O workflow confere que nenhum motor público, UI, FX, MIDI, preset ou `package.json` mudou frente ao commit público congelado `a610e6d6fe6e803d86650a298611efcaf46e2b35`.
4. A medição de CPU é reportada como Node/Linux **sem promover para hardware real**.
5. Mesmo com todos os testes aprovados, o laboratório continua **sem saída em pressão sonora [Pa], parâmetros medidos, licenças comerciais de dados de Plath/IR e testes ABX**. A validação matemática não dá autorização para integrar o laboratório ao motor D.

**Decisão:** esta etapa reforça a engenharia do protótipo isolado. O Stage público permanece v1.12.7 experimental D; a v1.12.6 continua para A/B, a PR #26 continua reprovada, e os 7 R-GATEs permanecem **0/7** até evidência física, perceptiva e em hardware.
