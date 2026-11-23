# Stage Synth — laboratório E2.0: ponte compartilhada passiva com 88 cordas e abafadores

**Data:** 23/11/2026. **Problema observado pelo titular:** não há evolução audível convincente nos sucessivos D v1.12.7–v1.12.9. Não promover microvariantes como piano mais realista. Motor D público v1.12.8 é preservado.

## Avanço proposto e testável
O solver anterior `research/shared-passive-piano-bridge.mjs` provou por equações a troca bilateral de energia, mas considerava apenas um subconjunto fixo de teclas, sem ação de abafadores/pedal. Este laboratório cria `research/damper-aware-shared-bridge.mjs`: mantém **as 88 teclas e suas 176 polarizações ligadas a uma única ponte de dois graus de liberdade**, inclusive cordas não acionadas, e adiciona `noteOn/noteOff/CC64`. Abafadores elevam apenas os coeficientes de amortecimento `C >= 0`, sem apagar a carga elástica da escala. Atualizações refatoram o complemento de Schur na hora do evento, não por amostra. A rede segue passiva e `step()` não aloca objetos.

**Isto NÃO modifica o DSP publicado**. O laboratório é uma alternativa mecânica para avaliar a lacuna real `body.reaction` ignorada pelo D; não somamos `boardVelocity` ao áudio existente nem chamamos a saída de pressão acústica. Não existe transfer function medida para ponte→ar, nem martelo fisicamente parametrizado; a excitação `strike` é um deslocamento inicial normalizado.

## Medições e controles
- `tests/damper_aware_shared_bridge.test.mjs`: rede de 88 teclas, variação de damping tecla/pedal/nota repetida, balanço energético 44.1/48/96 kHz com mudanças de estado, zero-input, transmissão entre cordas por ponte com teste desacoplado, estresse de 32/48/64 teclas, entradas inválidas.
- `scripts/benchmark_damper_aware_shared_bridge.mjs`: perfil de 128 quadros com 88 cordas permanentemente conectadas e 32/48/64 teclas pressionadas, 180 blocos medidos após warmup. Apenas Node/Linux; não certifica callback AudioWorklet no PC ou Moto g04s.
- A substituição de damping só acontece nos eventos MIDI, mantendo a prova discreta `∆E = trabalho - dissipação` válida por trecho, pois amortecimento nunca é negativo. A energia não recebe um impulso por mudar de damper.
- **Gates comerciais 0/7**; licenças de dados Plath/Yamaha IRs seguem sem autorização verificada.

## Próximo critério, antes de criar som
1. Rodar regressão completa Stage + testes do laboratório + benchmark; preservar todos os arquivos de som/UI/FX/MIDI/presets byte a byte.
2. Desenhar uma interface *passiva* e causal entre ressonadores do D e a ponte, evitando duas cordas virtuais redundantes por nota. Confirmar que a energia não cresce no sistema acoplado — não basta usar `body.reaction` como ganho arbitrário.
3. Obter/medir radiatividade `aceleração`/pressão com direitos comerciais, ou rotular qualquer proxy de saída apenas como sinal mecânico experimental.
4. Separar notas de calibração/validação, exigir mudança perceptiva útil versus piano real em C2/C3, manter C4–C6, e depois aferir 32/48/64 vozes no AudioWorklet real.

**Decisão:** preparar infraestrutura física que responda ao pedal e acoplamento compartilhado; não anunciar nova versão sonora enquanto a escuta continuar sem melhoria.

## Execução reproduzível — GitHub Actions 45192238684
[Workflow de validação passiva](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45192238684) com **173/173 testes Node aprovados**, incluindo sete novos. A comparação de arquivos públicos por `git diff` passou: nenhum motor distribuído nem UI/FX/MIDI/presets/package foi alterado.

Benchmark isolado Linux/Node após warmup, 128 amostras a 48 kHz, **88 teclas sempre ligadas à ponte**, independentemente de quantas estão acionadas:

| Teclas acionadas | Mediana do bloco | p95 do bloco | Parcela do orçamento de 2,667ms (p95) |
|---|---:|---:|---:|
| 32 | 0,21704ms | 0,22583ms | 8,47% |
| 48 | 0,21676ms | 0,22559ms | 8,46% |
| 64 | 0,21570ms | 0,22775ms | 8,54% |

Os números são apenas do núcleo passivo, **sem o D, sem o trabalho do navegador, sem FX, sem áudio real**. Não provaram capacidade de 64 vozes no dispositivo. Tampouco validam melhora perceptível ou licenciamento. A versão em produção continua D 1.12.8 experimental; a PR E2.0 permanece em avaliação.

## Continuação E2.1 — interface causal martelo → cordas → ponte (23/11/2026)

A sequência D v1.12.7–v1.12.9 foi considerada sem avanço timbral perceptível pelo titular. Em vez de alterar a produção pública, foi criado `research/hammer-driven-passive-piano.mjs`, que dirige a rede **mecânica compartilhada e passiva** existente com um pulso de força suave, de comprimento limitado e velocidade MIDI, distribuído entre as duas polarizações mecânicas da mesma tecla. O cálculo emprega o mesmo solver por ponto médio implícito, portanto a saída `boardVelocity` e o retorno da ponte são consequências dos estados acoplados — não um som de madeira sintetizado por senoides adicionais.

**O que a prova numérica demonstra:** para excitação externa com estados inicialmente nulos, vale `E_final - (trabalho_externo - dissipação) ≈ 0`, inclusive após CC64 e soltura das notas. Quando a força do martelo termina, o sistema livre perde energia e não produz energia espontânea. Uma corda não golpeada recebe energia pela ponte apenas com acoplamento diferente de zero. Amortecimento não remove rigidez nem desconecta as demais teclas.

**Testes:** `tests/hammer_driven_passive_piano.test.mjs` cobre 44,1/48/96 kHz, forças finitas, ledger energético, pedal, transferência simpática causal sem martelo na corda receptora, renderização em blocos idêntica a amostras individuais, estresse 32/48/64 notas e rejeição de entradas inválidas.

**CI:** [execução 45193185780](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45193185780) registrou **179/179 testes Node aprovados**, benchmark de ponte isolada e comparação `git diff` dos módulos públicos aprovada. Benchmark do solver anterior E2.0, **não** do motor completo E2.1: 32 teclas p95 0,22709ms; 48 teclas 0,25293ms; 64 teclas 0,24089ms por bloco de 128 amostras @48kHz, com rede física completa de 88 teclas.

**Limitações importantes:** `peakForce` está em unidade normalizada, não newtons; duração do contato é uma hipótese, não uma medição. O protótipo mantém uma coordenada por polarização por tecla, não representa todas as ~230 cordas físicas de um piano real. `boardVelocity` é velocidade mecânica generalizada, **não pressão sonora radiada**. O laboratório não está interligado aos modos do D e nenhum WAV novo deve ser apresentado como melhora de timbre. A v1.12.8 continua pública, A/B/C/Clássico/MIDI/FX/presets intactos, 0/7 R-GATEs e nenhuma certificação de 32–64 notas em PC/Android.

**Próximo gate real:** identificar e calibrar a radiação do tampo; projetar uma integração que substitua a antiga soma modal por uma rede passiva, em vez de apenas misturar mais um corpo como wet FX; comparar C2/C3 em arquivos de referência independentes e escuta nivelada antes de alterar som distribuído.
