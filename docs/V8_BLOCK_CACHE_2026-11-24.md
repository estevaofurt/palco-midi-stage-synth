# C3X V8 Web — cache de coeficientes por bloco (24/11/2026)

## Decisão e escopo
Base main: ff73ddc95e57e192ea8b65a03fae11ba132e0536. Blob do motor original: 2c5f93d2c70b9a90f8ea9bea174dd6e312d62802. Candidato offline: research/c3x-v8-block-cache.mjs (blob 073012593b46765b555d75a6fb7c09c1ce7d115a). Não é o V8 Python nem foi ligado ao AudioWorklet. Não alterar index.html, v8-preview.html, motores históricos, presets, MIDI, FX, UI ou versões. Candidato sem registro de processador. O ZIP original Stage_Synth_C3X_Etapa_08.zip continua não localizado na busca de arquivos; sem alegação de paridade.

## Hipótese
No render síncrono não chegam mensagens entre frames. Reutilizar por bloco filteredHammer, attenuation e bodyCoupling; conservar as expressões, ordem das operações, estados e Float64. Dois buffers Float64 por voz são criados no note-on, não por amostra. No máximo 30 modos por voz e 480 bytes adicionais por voz (até 30.720 bytes de dados para 64 vozes, sem overhead de objetos). Sem mudança de parâmetros acústicos, duração, dinâmica ou modelo de ponte.

## Testes executados
Comparação direta do código original obtido via GitHub e do candidato gerado em runtime JS isolado, buffers stereo Float32 de 128 frames. 1.969.152 valores comparados com Object.is, zero divergências, todos finitos, contagem de vozes e eventos done coincidentes.
- 22.050 Hz eco, 32 vozes, 48 blocos.
- 44.100 Hz balanced, 48 vozes, 48 blocos.
- 48.000 Hz studio, 64 vozes, 48 blocos.
- 96.000 Hz eco, 32 vozes, 48 blocos.
- 48.000 Hz eco, uma nota C4 speed .06 com pedal, 7.500 blocos/20 s.
- Mudanças de brilho/ressonância/amortecimento, release, CC64, redução de qualidade e panic incluídas. O trecho de 20 s verifica igualdade digital, não audibilidade ou sustain forte de 20 s.

Testes permanentes: node --test tests/v8_block_cache.test.mjs. O npm run check deve ser executado via CI ou clone com Node 22. Clone local indisponível por DNS neste ambiente; a suite completa não foi executada localmente. Não declarar CI aprovado sem evidência.

## Benchmark exploratório
Arquivos original/candidato relidos da branch. Runtime JS isolado, 48 kHz, 128 frames/bloco, 20 blocos de aquecimento, 100 medidos, três repetições em ordem original/candidato; vozes mantidas (notas 35+i%48, speed .75, hardness/brightness .55). Tempos brutos em ms:
| Vozes | Original | Candidato | Redução mediana aproximada |
|---|---|---|---|
| 32 | 2786 / 2802 / 2702 | 1974 / 2095 / 2078 | 25% |
| 48 | 6054 / 5869 / 5786 | 4229 / 4491 / 4461 | 24% |
| 64 | 9035 / 8675 / 8812 | 6757 / 6449 / 6568 | 25% |

Não são benchmarks Node nativo, AudioWorklet ou hardware físico. Tempos absolutos excedem o prazo de callback; apenas indicação relativa, sem certificação 32/64 notas real-time.

## Critério antes de integração
Executar suite completa e testes dedicados, repetir benchmark Node com distribuição de tempo por bloco, avaliar AudioWorklet em Chrome/PC e Moto g04s, confirmar 32 vozes mínimas e 64 como meta (sem estalos). Testar ataque suave/forte e cauda por escuta, controlar pedal e repetição de notas. Sem promoção à versão pública e sem alteração do timbre até aprovação. R-GATEs comerciais não avançam.
