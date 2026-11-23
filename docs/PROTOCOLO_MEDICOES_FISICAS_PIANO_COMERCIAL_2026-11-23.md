# Stage Synth — protocolo de aquisição de medições físicas para uso COMERCIAL

**Data:** 23/11/2026. **Estado:** especificação preparada para contratação/medição; nenhuma captação, parceria, licença adicional ou contrato foi efetivamente celebrado. **Nenhum DSP/P1/P2 será alterado** antes dos sete gates de referência e autorização explícita do titular.

## Objetivo e limites

Amostras WAV comerciais (CC0, CC BY, domínio público declarado) permitem estudar o **som que chega ao microfone**; não permitem separar sem hipóteses a força do martelo, as duas polarizações das cordas, a admissão da ponte ou o radiador da sala. Precisamos de medidas físicas independentes para a cadeia martelo → cordas 1/2/3 → ponte → tampo → som radiado, com energia, fase, modo e dinâmica. A modelagem e os testes posteriores poderão ser reduzidos/modal/híbridos: **não exigir FEM 3D em tempo real**.

Este documento deve orientar uma coleta com pesquisador/técnico/estúdio autorizado ou guiar uma medição própria. **Não enviar contato, baixar corpus NC, contratar alguém, acessar dados restritos nem alterar o app automaticamente.**

## Direitos comerciais e contrato de dados (R-GATE-3)

Antes de qualquer sessão, registrar por escrito:
- Identidade do proprietário do instrumento, operador/técnico, intérprete (quando houver) e captador do áudio; titularidade de gravações e dados.
- Permissão expressa para **copiar, armazenar, modificar, processar, extrair parâmetros, criar modelos DSP e explorar comercialmente software, presets e resultados derivados**, inclusive em países de distribuição previstos. Separar direitos de distribuir os WAV brutos, caso essa distribuição não seja necessária.
- Condições de uso, crédito, exclusividade, revogação e confidencialidade; eventual proibição de divulgar marca, número de série ou detalhes privados do proprietário. **Não alegar endosso da Yamaha/Steinway sem acordo.**
- Entregáveis originais com registro de direitos, não apenas arquivos mixados ou demos. Não aplicar material com licença NC a pipeline comercial por presunção de que resultados numéricos ficam liberados.

Revisão jurídica final obrigatória antes do lançamento. **Nenhum documento de contrato está assinado nesta etapa.**

## Planejamento de instrumentos e notas

### Pianos e controles mínimos

1. **Cauda de referência oriental**: modelo e número de série/documentação de um Yamaha real; **não denominar CFX se o piano medido for C5 ou Disklavier**.
2. **Steinway real** (Model B ou D, indicar exatamente qual); usar bitKlavier D CC BY 4.0 apenas para comparação de escuta/mics, não como captura não editada.
3. **Vertical convencional** (Kawai/Knight ou outro identificado).
4. **Mesmo instrumento com e sem feltro**, quando viável e autorizado, com microfone/ganho/afinação/temperatura e estado de pedal documentados para distinguir tratamento de outras causas.

**Piloto antes da coleta completa:** cinco regiões (MIDI 36/C2, 48/C3, 60/C4, 72/C5, 84/C6) + teclas próximas das transições reais de 1/2/3 cordas do instrumento. Se nota não for diretamente amostrada ou instrumentada, registrar isso. Três níveis **de velocidade física do martelo, se mensuráveis**, com pelo menos três repetições válidas por nível e tecla. Não confundir velocity MIDI 1–127 com m/s.

### Manter constantes

Estado da afinação e umidade, tampa, pedal, posição física do microfone, ganho, número de cordas do uníssono, abafadores, posição de batida, temperatura, tempo desde afinação; registrar eventuais alterações. Arquivar master PCM sem EQ, reverb, compressor, noise gate, normalização individual de notas ou fade destrutivo. Armazenar versões processadas separadamente, sem sobrescrever os originais.

## Mapa de ensaios e arquivos que devem ser entregues

| Ensaio | Entrada e controle | Saída física necessária | O que nos permitirá identificar |
|---|---|---|---|
| **M01 Martelo** | velocidade real (m/s), nota, feltro, número de impacto | contato F_h(t) [N] e/ou deslocamento/compressão δ(t) [m], cinemática e rebote, com incerteza e método | Pulso de força, tempo de contato, não linearidade por intensidade; **medição por equipamento qualificado, não inferir só de WAV** |
| **M02 Corda única** | amortecer outras cordas do mesmo uníssono sem danificar instrumento, tocar nota | vibração em H/V (sensor óptico/laser), f1, modos, decaimentos, batimentos, erro | Inarmonicidade B e perdas por parcial; **double decay numa mesma parcial** e duas polarizações |
| **M03 Uníssono 1/2/3** | mutar uma ou duas cordas de forma controlada, manter demais estados | velocidade/pressão por estágio, frequência por corda, fase, decaimento | Acoplamento mútuo da ponte, modulação e aftersound vs cordas isoladas |
| **M04 Ponte/tampo FRF** | **martelo de impacto instrumentado diretamente na ponte** com força [N] conhecida (não força tecla-base) | aceleração [m/s²] e fase no mesmo ponto/região, força(t), frequência e coerência | **Mobilidade complexa \(Y_b(f)=v_\mathrm{ponte}(f)/F_\mathrm{ponte}(f)\)**; converter a→v por divisão \(j\omega\) com controle de ruído perto de DC |
| **M05 Radiador/posição** | mesmas regiões de ponte, microfones perto das cordas, do tampo e na posição do pianista | pressão L/R [Pa], transferência complexa por mic, coordenadas, ganho e resposta da sala | Diferenciar resposta física de tampo/ponte da resposta dos microfones e reverberação; H(f,x→L/R) |
| **M06 Damping/pedais** | tecla press/release; CC64 baixo/intermediário/alto; CC66/67, gravação de movimento se possível | estado real dos abafadores/pedal, formas de onda da nota e simpatias, contatos | Meio-pedal e ressonância simpática; comportamento de sostenuto e una corda por grand/vertical |
| **M07 Felt A/B** | MESMO piano, mesma nota, velocidade física, salas/mics, com e sem feltro | forças/ondas sem processamento; repetições com controle e identificação de mudanças de voicing | Isolar o que decorre do feltro e o que decorre do próprio vertical, mic ou intensidade |
| **M08 Música real** | MIDI e áudio com forte/leve, acorde, repetição, pedal e dinâmica | MIDI/tempo original mais referência estéreo não processada | Teste futuro em situação musical; sem substituir medições M01–M07 |

### Extensão metodológica M01.1 e M04.1 — carga/descarga do martelo e mobilidade CRUZADA

A auditoria [EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md](EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md) mostrou dois observáveis que o planejamento inicial tratava de forma insuficiente:

- **M01.1 — histerese do feltro:** captar simultaneamente `F_h(t)`, movimento da cabeça do martelo, movimento da corda, compressão `δ(t)` e separação/rebote, incluindo **carregamento e descarregamento**. Registrar nota, velocidade física e voicing, erro e repetições. O único pico de força ou pulso predefinido **não identifica** um martelo viscoelástico; medições publicadas (Yanagisawa & Nakamura, 1984; Russell & Rossing, 1998) não fornecem séries brutas próprias do Stage.
- **M04.1 — mobilidade 2×2 do ponto de ponte:** quando possível e seguro, medir excitação de força em dois planos transversais `T/P` e respostas de velocidade nos dois planos, formando `[Y_TT, Y_TP; Y_PT, Y_PP]` **complexa** por posição e frequência; registrar sinais originais, eixo/ponto, magnitude, fase, coerência e incerteza. Isto é exigência metodológica para **identificar o acoplamento cruzado H/V e o double decay**, sustentada por Miranda Valiente et al. (2022/2023). Para medição apenas normal ao tampo, declarar que a matriz 2×2 permanece desconhecida e não considerar R-GATE-2 físico integralmente concluído.
- **Interpretação:** densidade modal, fator de perdas e massa de um upright publicado por Ege/Boutillon (2010) são aproximação **estatística por instrumento**, não substituem os termos cruzados medidos nem podem ser aplicados sem validação a CFX, Steinway ou felt piano.
- **Contingência:** um piloto de mobilidade escalar `Y_TT` pode orientar estudo preliminar **offline**, mas jamais deve ser apresentado como matriz completa ou validação de uma nova implementação. A instrumentação da ponte deve ser executada por profissional apto para evitar danos.

Os ensaios com ponte e martelo **não devem ser improvisados**: exigir profissional habituado a instrumento acústico, sensores e pontos de toque, sem permitir danos.

### Prioridade para evitar uma coleta gigantesca

**Primeira prioridade**: M01/M02/M04 com poucas notas representativas, porque o modelo atual usa impulsos heurísticos e resposta global de ponte. **Segunda prioridade**: M03/M05, incluindo fase/espacialidade. **Terceira prioridade**: M06/M07/M08 para expressividade e Felt. A ordem de aquisição não implica que o DSP deva começar antes de os R-GATEs necessários estarem aprovados.

## Especificação de entregáveis e integridade

Entregar, por sessão/instrumento:
- WAV master PCM (preferencialmente 96 kHz/24 bits; pode haver taxa de sensores diferente e sincronização explícita), canais físicos separados, sem edição destrutiva, tempo de início e corte de nota documentados;
- Séries brutas de força, aceleração, posição e/ou velocidade em CSV/NPZ ou formato aberto com coluna de unidade, identificação de sensor, ganho/calibração, relógio amostral e sincronização;
- FRF de **amplitude e fase** por ponto de ponte, frequência em Hz, unidade de mobilidade **(m/s)/N**, módulo, fase, coerência e número de impactos válidos, parâmetros do estimador; arquivar força(t)/aceleração(t) além da FRF processada;
- Mapa físico por instrumento: 88 notas, onde há 1/2/3 cordas, limite entre graves enrolados e notas lisas, comprimento/material/bitola quando possível; mapa de afinação medido f1 por nota, desvio em cents e estimativa B com incerteza;
- Folha de microfonação/geométrica: distância/ângulo, modelo e número de série dos sensores (se lícito), sala, temperatura, umidade, estado da tampa, amortecedores e pedal;
- Manifesto por arquivo contendo **SHA256**, direitos, instrumento/nota real/velocity física ou MIDI, camadas, microfone, condições, sensor/calibração, processamento e contato de origem; reportar arquivos ausentes (não preencher com inferências);
- Script ou metodologia para repetição dos experimentos (sem exigir cópia de código GPL no produto).

**Não usar uma taxa de rejeição/erro inventada**: determinar tolerâncias com dados piloto, equipamento e ruído. Para FRF, reportar coerência em toda banda útil e não aceitar apenas screenshot de gráfico. Em estudo recente, medições de mobilidade sobre a ponte atingiram coerência >0,9 entre 50 e 4000 Hz em seu próprio experimento; usar como referência metodológica, não garantia para qualquer sessão.

## Critérios de aceitação contratual e próximos gates

- **Recebido**: existem fontes, arquivo real acessível, tamanho/codec/unidades, direito comercial e hashes.
- **Medido**: dados físicos e incerteza não confundidos com processamento de microfone ou velocity MIDI.
- **Reproduzível**: possível reexecutar cálculo de f1/B/perdas, Yb e resposta acústica com dados e condições originais.
- **Aplicável**: valores físicos serão atribuídos ao instrumento exato, não ao fabricante inteiro ou ao Stage sem comprovação.
- **Aprovado para DSP**: somente após **R-GATE-1..7**, validação jurídica e autorização expressa do titular do projeto.

Mesmo a conclusão da coleta não validará por si só a experiência no navegador; o PC/Chrome/Moto g04s e 32–64 vozes deverão ser homologados depois em testes reais.

## Referências técnicas primárias

- Birkett et al., *Experimental investigation of the piano hammer-string interaction* (2013): https://pubmed.ncbi.nlm.nih.gov/23556611/ — medidas da dinâmica de impacto 1,06 a 2,98 m/s em ensaio experimental, **não parâmetros universais**.
- Weinreich, *Coupled motion of piano strings*: https://www.speech.kth.se/music/5_lectures/weinreic/motion.html .
- Miranda Valiente et al., *Influence of soundboard modelling approaches on piano string vibration*: https://eprints.soton.ac.uk/497574/1/Manuscript_revision_-_PURE.pdf — mede mobilidade força→vibração diretamente na ponte, compara modelos modais reduzidos e complexos; paper não fornece automaticamente arquivo de FRF numérica com licença para nosso produto.
- Bank et al., *Physically informed signal-processing methods*: https://home.mit.bme.hu/~bank/publist/jasp03.pdf .
- Plath/Hamburgo dataset: https://zenodo.org/records/3274772 — aceleração de ponte e pressão, mas força medida é na **base da tecla**, não driving-point da ponte.

**Status:** documento preparatório para aquisição legal e física, sem amostras/contratos externos firmados. **Não libera DSP.**
