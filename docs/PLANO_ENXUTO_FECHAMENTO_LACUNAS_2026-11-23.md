# Stage Synth — plano ENXUTO de fechamento de lacunas (23/11/2026)

**Objetivo:** parar a expansão bibliográfica e fechar os sete R-GATEs existentes por **três frentes de execução e evidências testáveis**. O projeto é **comercial**. Este documento **não muda os requisitos, não libera DSP nem autoriza dados NC**. Base consultada: `main 7869bc3d95a8e4b0dde25cac5989f2c85e41e143`; Stage v1.12.4, referência histórica de estabilidade relatada v1.9.5. Continuam **0/7 R-GATEs integralmente aprovados**.

## Regra de foco

- **Congelar novas buscas genéricas, motor de terceiros, listas de artigos e novos protótipos**. Nova fonte só entra se preencher um campo ausente da matriz abaixo **com arquivo/licença/medição verificável**. Não abrir uma sequência de PRs bibliográficos.
- **Não exigir 3D FEM, matriz de ponte 2×2, medição de todos os componentes, todos os fabricantes ou seis pianos como condição obrigatória.** O texto de **R-GATE-2 já permite expressamente uma aproximação passiva justificada e calibrável** da ponte. Histerese medida e mobilidades cruzadas ficam como **caminhos de escalonamento quando as comparações objetivas/auditivas apontarem falha**, não desculpa para manter pesquisa infinita. Não afirmar acoplamento H/V integralmente medido onde não foi.
- **Tudo medido, estimado ou inferido deve ser rotulado**; não usar tabelas físicas de terceiros como “martelo Yamaha real”. Não importar código AGPL, datasets NC ou processamento de amostras de licenças desconhecidas.
- **Sem alterar DSP, UI, FX, MIDI ou presets** até revisar integralmente os R-GATEs e receber a autorização expressa do titular. A v1.9.5 permanece protegida. Meta de **32 mínimo/64 desejado** ainda exigirá teste de callback real, PC e Moto g04s.

## Frente A — FECHAR O CORPUS, não aumentar a bibliografia (R-GATE-1, 3, 4)

**Dois instrumentos identificados, cinco notas, três dinâmicas, sem inventar velocidade física:**

1. **Yamaha C5 Salamander**: **15 FLAC originais C2/C3/C4/C5/C6 × layers v1/v8/v16**, com hash/codec/fonte/licença CC BY 3.0 já confirmados em `research/commercial_audio/verified_source_sha256.json`. *Status: 15/15 amostras originais verificadas*; notas são C2–C6, não CFX; v1/v8/v16 **não é m/s**. O corpus pode conter fades finais/ambiente: identificar janela de medição.
2. **Steinway Model B — University of Iowa MIS, fonte oficial**: https://theremin.music.uiowa.edu/MISpiano.html e https://theremin.music.uiowa.edu/MIS.html . O acervo publica **C2/C3/C4/C5/C6 × pp/mf/ff**, 15 arquivos AIFF individuais, 16-bit/44,1k estéreo, com microfones Neumann KM84, DAT, sala **não anecoica** e declaração oficial de uso em **quaisquer projetos sem restrições**. *Status: 15/15 endereços/nomes identificáveis na página original, **0/15 conferidos por SHA256 neste piloto**.* Endereços devem ser obtidos dos links da página institucional; não usar espelho quando a origem estiver disponível.
3. **Lacuna de estado**: em cada fonte discriminar quais arquivos são notas sustentadas, soltura, pedal baixo/alto, ruído de ação, posição de mic, processamento e dados **não informados**; o catálogo de notas isoladas **não comprova** pedal/release conhecido. Complementar condições faltantes com fontes originais legalmente comprovadas já existentes (por exemplo VCSL Sus/NoSus com *normalização explicitada*) ou documentar ensaio próprio pequeno. Felt exige par controlado ou **escopo reduzido formal**; vertical/Felt **não viram automaticamente quatro presets fisicamente calibrados**.
4. **Aceite A:** 30 arquivos-fonte no conjunto mínimo com formato real, hash SHA256 de bytes originais, pitch detectado contra rótulo, dinâmica *nominal* sem confundir com velocidade de martelo, mic/room/nota/licença/status de pedais documentados; no mínimo um par pedal ou release com estado comprovado por fonte adicional. Nenhum áudio de terceiro precisa ser armazenado no GitHub/app.
5. **Risco conhecido:** implementadores externos relatam rótulos incorretos em algumas notas Iowa **próximas de A0/B0**: não considerar relato comprovado no nosso corpus; medir pitch de C2–C6 diretamente e registrar desvios reais. Não acrescentar os 15 à contagem Stage de 50 até a integridade e origem serem verificadas.

## Frente B — FECHAR A HIPÓTESE FÍSICA MÍNIMA, sem laboratório obrigatório (R-GATE-2, 6)

**Referencial reduzido e audível para UM motor de piano:** (i) martelo/contato não linear parametrizado por nota/dinâmica, rotulado *modelo da literatura a calibrar*; (ii) cordas rígidas com `B` e perdas por parcial observadas no áudio; (iii) 1/2/3 cordas conforme registro com desafinação e dupla cauda explícitas, sem reivindicar H/V medida; (iv) **ponte/tampo passivos** com modos compartilhados e radiação L/R, ajustáveis com referência acústica e fase/estabilidade física quando houver dados; (v) abafadores e CC64 como teste funcional obrigatório. Cada parâmetro terá unidade, faixa, origem, marca **M**edido / **I**nferido / **H**ipótese e limitação.

**Aceite B (somente no plano, não realizado):** ficha curta de parâmetros, equations/referências já auditadas, passividade/limite de energia e estabilidade numérica para módulos, testes discriminantes de batimento/duplo decaimento, ausência de confusão corda × sala, sem supor que IR de som equivale à FRF mecânica da ponte. **Não marcar aprovado** antes de demonstrar que a aproximação é *calibrável e validável*. **Escalonar para M01.1/M04.1** (medição de histerese e Y2×2) **somente se** a hipótese reduzida falhar nos observáveis relevantes, houver discrepância persistente ou atribuição de parâmetros se mostrar impossível.

## Frente C — FECHAR MÉTRICAS, ACEITE E CUSTO (R-GATE-5, 6, 7)

**Reusar o código atual**, nunca iniciar outro analisador do zero: `tests/piano_acoustic_metrics.test.mjs` já testa FFT/A440, B ideal vs B esticado, decaimento, RMS, clipping/NaN; `tests/reference_audio_analysis.test.mjs` cobre ataque, janelas curtas e descarte de comparação insuficiente; `tests/measure_piano_engines.mjs` cobre **108** casos secos A/B/C. Porém isso **não cobre** R-GATE-5 completo.

**Aceite C antes do DSP (design/testes isolados somente após liberação pertinente):**
- Fixar suíte de verdade conhecida de `B=0/0,0004/0,0012/0,003`, C2/C4/C6, caudas H/V, uníssonos, ataques de alta frequência e ruído, com margens obtidas do ensaio, sem fabricar tolerâncias.
- Fixar protocolo A/B/C com normalização de ganho, ataque, brilho por intensidade, decaimentos por parcial e áudio estéreo, separando núcleo seco e FX; **escuta cega** de C2/C4/C6 com referência real e testes de pedal/repetição.
- Especificar e registrar teste **32 e 64 vozes** com acordes e CC64, bloqueio/carga do callback, clipping/estalos/notas presas em PC e Moto g04s. **Só homologar em aparelhos reais**, não pelo resultado de Node.
- R-GATE-6 e 7 podem ter seu **protocolo textual fechado antes do novo DSP**; execução/aceite auditivo do modelo acontece **depois de autorização** e nunca é confundida com o gate de preparação.

## Checklist de execução em ordem fixa — sem novas frentes

| Ordem | Ação que efetivamente reduz uma lacuna | Critério de encerramento | Situação verificada |
| --- | --- | --- | --- |
| 1 | **Validar os 15 AIFF Iowa originais** C2–C6 pp/mf/ff por URL oficial e pitch, preservar SHA256/metadados e apagar bytes no final | 15/15 com hashes e integridade, ou lista nominal de falhas | **PENDENTE** (nomes confirmados) |
| 2 | **Fechar pedal/release e direitos** de 30+ arquivos, com observação explícita de valores faltantes e eventual controle VCSL/medição própria | Planilha de evidência por arquivo + licença, sem colunas inventadas | **PARCIAL** |
| 3 | **Ficha curta do modelo físico PASSIVO** com fontes que já temos; distinguir hipótese vs inferência | Requisitos/falhas falsificáveis, sem exigir medição 2×2 por padrão | **PENDENTE** |
| 4 | **Consolidar testes conhecidos e protocolo de avaliação** dentro de R-GATE-5/6/7 | Matriz de experimentos, tolerâncias justificadas e plano auditivo/32–64 | **PARCIAL** |
| 5 | **Revisar os sete R-GATEs com evidência específica**, sem “percentual” inventado | Passa / não passa / motivo + autorização expressa antes do motor | **0/7 integralmente aprovados hoje** |

**Regra de parada:** depois do item 1, não abrir mais artigos genéricos; executar apenas o próximo item pendente. Se um dado não puder ser obtido/licenciado, registrar a limitação, definir substituto físico/perceptivo e seu teste de reprovação — não perseguir corpus interminavelmente.

**Resultado imediato da presente etapa:** escopo reduzido e **fonte exata para fechar o segundo piano**; **nenhum AIFF novo foi validado ou adquirido**, nenhuma modificação de áudio/motor. Esta é uma substituição de prioridades, não aprovação tácita dos R-GATEs.
