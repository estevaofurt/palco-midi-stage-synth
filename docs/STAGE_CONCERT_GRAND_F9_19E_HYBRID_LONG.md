# F9.19e — sustain dos híbridos D e E

Base e4700f2884074eeaebcb35811aa8cb08b5bbdb56. F9.19c e F9.19d concluídas. Modelo C global4 continua única referência confirmada pelo titular sem vibração. D global3 com cinco modos em 4× e E global2 com cinco modos em 4× apresentam redução de energia fora de bandas comparável ou próxima a C; D priorizado para escuta. A fração de energia não determina limpeza do ataque. Testar D/E em MIDI76 20s, MIDI127 40s, reutilizar renderHybridRattle sem mudar parâmetros. Mesmo ganho .36767023440034063, PCM16/24, invariantes, análise de ressonâncias e queda relativa e limiar contextual histórico. Comparar F9.19c e original felt150; não inferir duração auditiva, não promover sem avaliação de ataque, timbre, sustain e dinâmica. Quatro renders e repetição dos testes híbridos configurados, execução pendente. Nenhuma alteração de C ou main; F10 definitiva bloqueada.

## F9.19e — resultados completos confirmados

CI [45472486673](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45472486673), commit d90ee1715d1253b2432b21506b8fabc035800b21: smoke (10 verificações híbridas) e quatro renderizações concluídos com sucesso. Todos PCM16/24 a 48 kHz, sem clipping e com os gates de energia e exportação do renderer aprovados. Dados obtidos dos logs F919E_LONG e F919C_LONG; WAVs não reanalisados localmente.

| Modelo | Limiar médio (s) | Limiar forte (s) | RMS2 médio | RMS2 forte | Artefatos médio/forte |
|---|---:|---:|---:|---:|---|
| C global4 | 13 | 19 | .00768860965745 | .02176135862591 | 14957391937 / 14957612721 |
| D global3 | 13.5 | 19.5 | .00879029155763 | .02493373729888 | 14958985443 / 14958407122 |
| E global2 | 14 | 20 | .01033669167834 | .02925150492552 | 14956353900 / 14958871858 |
| Seletivo4 | 14 | 20 | .01274284741938 | .03570465909528 | 14956642415 / 14955959994 |

RMS2 é a janela 2–2.5s. Limiar absoluto histórico .0006518758466381057 FS, janelas de 0.5 s; não é duração perceptiva. Original felt150 médio 14 s, forte 20.5 s (referência anterior). D ganha 0.5 s e cerca de 14.6% RMS2 forte vs C; E ganha 1 s e 34.4%. C permanece único aprovado por escuta, sem promover D/E.

## F9.19f — revisão de energia absoluta e comparação para escuta

Preservado o ganho .36767023440034063, mesma nota C4, janelas e bandas. O código f9-rattle-spectrum.mjs calcula rmsBand = sqrt(total) e wideOffFraction = wideOff/total. Logo potência fora das bandas (FS², estimativa Hann na banda 30–6000 Hz) = rmsBand² * wideOffFraction. Não confundir com vibração mecânica medida, ruído isolado ou percepção auditiva. Fração menor pode decorrer de denominador maior.

| Modelo | Janela .025–.525 s médio / forte (potência relativa a C) | Janela .525–1.025 s médio / forte | Janela 1.025–1.525 s médio / forte |
|---|---:|---:|---:|
| C | 1 / 1 | 1 / 1 | 1 / 1 |
| D | 1.040 / 1.048 | 1.189 / 1.185 | 1.769 / 1.231 |
| E | 1.120 / 1.146 | 2.402 / 2.443 | 11.922 / 4.241 |
| Seletivo4 | 1.291 / 1.361 | 12.179 / 13.418 | 228.021 / 73.700 |

D é compromisso prioritário, não mais limpo que C em potência absoluta. A primeira janela exclui 0–25 ms e não certifica o ataque. Não extrapolar para outras notas ou polifonia.

Dados persistidos em audio/analysis_f9_19e_long_comparison.json (oito casos, 32 janelas, IDs de jobs/artefatos). Implementados f9-rattle-comparison.mjs e f9-rattle-comparison-demo.mjs: teste de fórmulas, rejeição de casos incomparáveis, PCM24 estéreo 48k, preservação dos primeiros 2.95 s dos trechos originais, fade de 50 ms, silêncio de 1 s, sequência C/D/E de 11 s por dinâmica, sem normalização e com SHA256 dos WAVs fonte. Self-test do núcleo executado com os dados reais de logs e PCM sintético no runtime JS isolado: aprovado. Workflow concert-grand-f919f.yml configurado para baixar os seis WAVs existentes e gerar o artefato; execução ainda não confirmada no momento deste registro. Sem alteração do DSP, parâmetros, renderers, C, main ou F10. Homologação auditiva e 32–64 vozes reais pendentes.

### F9.19f — CI confirmado e pacote disponível

[Run 45481513367](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45481513367), commit 226df6772d809278b537aa6b4c2d299587b67406: todos os passos concluídos com sucesso, inclusive Node 22 self-test, download dos seis WAVs de origem, validação de metadados/frames, montagem das duas sequências e upload. [Artefato 14960354446](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45481513367/artifacts/14960354446), 4.755.506 bytes: WAVs C4 MIDI76 e MIDI127, 11s cada, C de 0–3s / D de 4–7s / E de 8–11s, mais comparison.json e manifest.json. Sem ajuste de ganho e com fade editorial apenas nos últimos 50ms de cada trecho. Não é teste cego nem validação auditiva; aguardar avaliação do titular. F10 não iniciada, main permanece ff73ddc95e57e192ea8b65a03fae11ba132e0536.
