## FECHAMENTO RÁPIDO: Yamaha C5 + Steinway B com 15 fontes oficiais por piano (23/11/2026)

Novo [plano mínimo](PLANO_ENXUTO_FECHAMENTO_LACUNAS_2026-11-23.md), baseado nos sete R-GATEs e no fato de que **R-GATE-2 aceita uma aproximação de ponte passiva, justificável e calibrável**, sem exigir medição 2×2 para todos os casos. **Steinway B/Iowa:** 15 AIFF **originais**, C2/C3/C4/C5/C6 × pp/mf/ff, **90.184.430 bytes**, AIFF 44,1 kHz/16-bit/2 canais, origem institucional, SHA256 individual e mídia descartada após auditoria [run 45111873583](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45111873583). Hashes permanentes em `research/commercial_audio/iowa_steinway_b_verified_original_sha256.json`. **Yamaha C5 Salamander:** 15 FLAC originais já validados nas mesmas notas e 3 camadas. São 30 referências nominais com integridade/codec comprovados; **a afinação efetiva, soltura/pedal e equivalência de intensidade ainda NÃO foram validadas**.

**Total acumulado das fontes originais com hash: 65 arquivos / sete fontes instrumentais de piano, 264.127.566 bytes**, sem nenhum WAV/AIFF/FLAC no repositório ou no app. A origem permite uso em quaisquer projetos, mas condições comerciais/notice do produto exigem revisão. Nenhuma captura física F_h(t)/Y_ponte, nenhum novo motor, preset, UI, MIDI ou FX. **0/7 gates integralmente aprovados, 32–64 vozes sem homologação**. Próxima ação direta: conferir pitch dos 15 Iowa, completar prova de pedal/release, finalizar modelo físico passivo e os testes/aceites, sem novos papers genéricos.

---

## Modelos parametrizados de piano e correção de licença Dryad — 23/11/2026

**Auditoria documental verificada:** [MODELOS_NUMERICOS_DUSSEK_MF1_DRYAD_CC0_2026-11-23.md](MODELOS_NUMERICOS_DUSSEK_MF1_DRYAD_CC0_2026-11-23.md). O **Dussek** (código AGPLv3) possui preset independente **Grand B CC BY 4.0**, com **88 notas** e manifesto para **514.040 bytes** de dados numéricos (`data.bin`, SHA256 **declarado mas não conferido por transferência de bytes**). Seus parâmetros físicos foram **ajustados a partir de gravações**, não são série temporal medida de martelo ou ponte. O **MF-1** (MIT) descreve 30 notas amostradas, 970 parciais, 32 modos de corpo compartilhados e teto de 384 osciladores; reconhece ausência de ressonância simpática e tempos de abafador não medidos. Nenhum modelo/código externo foi copiado ou executado.

**Correção jurídica importante:** a política oficial **Dryad** publica datasets sob **CC0**, independentemente da licença do artigo *Motor origins of timbre in piano performance* (NC-ND). Os dois arquivos de depósito somam **32,54 KB listados**, mas download via pesquisa retornou **403**, portanto bytes/CRC/SHA e componentes de terceiro **não foram verificados**. O dado é para movimentos de tecla/percepção (M09), não F_h(t) nem Y_ponte. O Iowa MIS declara autorização para quaisquer projetos; não confundir licença da origem com direito de usar código AGPL ou preset CC BY-SA. Foi identificada divergência nos rótulos de notas dos arquivos Iowa relatada por autores independentes — **não resolvida por nova medição original**.

**Segurança:** só pesquisa; nenhum WAV, sensor, código, preset, DSP/UI/MIDI/FX alterado, e nenhuma nova referência física adquirida. Contagem Stage **50 gravações originais verificadas / seis pianos**, **0/7 R-GATEs completos**. A meta 32–64 notas não pode ser deduzida do número de osciladores de projetos externos; requer teste real e autorização para implementação. **Primeira validação do PR #17:** GitHub Actions [run 45110451775](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45110451775) concluído com sucesso: **95/95 testes Node aprovados** e **108/108 cenários offline secos A/B/C sem clipping ou não finitos**, conforme log `audio-regression`. A última alteração documental requer revalidação; CI não mede qualidade perceptiva nem capacidade real de 32–64 notas.

---

## Acesso a dados físicos PAPA / força inversa / IRCAM — 23/11/2026

Pesquisa de [dados físicos completos](ACESSO_DADOS_FISICOS_PAPA_IRCAM_FORCA_INVERSA_2026-11-23.md): relatório institucional **FWF PAPA** documenta medições em aproximadamente seis pianos modernos/históricos e o estudo de **Chaigne 2016** propõe reconstruir a força do martelo a partir da velocidade *medida na corda* (não a partir de WAV estéreo). No **Bösendorfer 280VC-9** analisado por caminhos vibroacústicos, o tampo foi a fonte principal, mas a região grave também envolveu contribuição do aro esquerdo; estudar sem afirmar que é regra de todo piano. O **IRCAM Modalys** documenta modelo modal medido de tampo com malha 13×13 e dois arquivos-modelo, **sem licença confirmada para extrair ou usar comercialmente os dados fora do Modalys**. Purdue apresenta medidas p/v_b, sem séries brutas licenciadas localizadas.

**Nova etapa só de pesquisa:** M01.2 (reconstrução inversa de força, acompanhada de validação/erro) e M05 estendido (investigar radiadores além do tampo nos graves). **Nenhum arquivo de medição PAPA/IRCAM foi obtido, licenciado ou hashado**, nem foi enviado contato aos pesquisadores. Preservados 50 arquivos originais de seis pianos, versão de app v1.12.4, histórica v1.9.5 e **0/7 R-GATEs completos**; P1/P2/DSP/UI/MIDI/FX/presets congelados. **Testes da primeira revisão documental:** GitHub Actions [45109748603](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45109748603) concluído com sucesso: **95/95 Node**, **108 casos de áudio seco A/B/C, zero clipping ou amostras não finitas**, conforme logs do job `audio-regression`. O commit documental final será revalidado pelo CI antes de merge. Não há evidência de qualidade perceptual ou desempenho de 32–64 notas em hardware real.

---

## Audição física ainda bloqueada: martelo com memória e matriz de mobilidade cruzada — 23/11/2026

**Nova auditoria:** [EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md](EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md). Foram verificadas fontes científicas primárias sobre força/deformação do martelo e histerese (Yanagisawa/Nakamura 1984; Russell/Rossing 1998), movimento de cabeça do martelo em dois eixos (Askenfelt 1991), modelo de mobilidade estatística do tampo em upright (Ege/Boutillon 2010), efeito da mobilidade **cruzada 2×2** na vibração em dois planos/double decay (Miranda Valiente et al. 2022/2023), redução a cinco modos comparada a outros modelos de corpo (JASA 2024), medição de Fazioli publicada (2017) e arquitetura híbrida diferenciável (Frontiers 2024; código **LGPLv3**, dataset licenciado separadamente).

**Correção do planejamento:** o antigo ensaio M04 media apenas força/velocidade **perpendicular** à ponte. Novo **M04.1** pede matriz complexa `Y_TT/Y_TP/Y_PT/Y_PP` com amplitude, fase, coerência, geometria e origem; **M01.1** pede ciclo de compressão e recuperação do feltro, não apenas pico de força. Exemplo publicado de martelo Steinway não autoriza calibrar os instrumentos Stage. O protocolo comercial foi atualizado, mas **nenhum sensor/medição de piano foi adquirido ou executado**.

**Prontidão inalterada:** acervo de 50 gravações originais/seis pianos; `main` v1.12.4, referência histórica v1.9.5; **0/7 R-GATEs globais integralmente aprovados**, P1/P2 e DSP/UI/MIDI/FX/presets inalterados, 32–64 vozes sem homologação real. **Validação efetiva da primeira revisão documental:** [GitHub Actions 45109195066](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45109195066) aprovado; logs do job `audio-regression` mostram **95/95 testes Node aprovados** e **108/108 cenários offline de A/B/C sem clipping ou não finitos**. Não é validação de 32–64 vozes em hardware real nem demonstra realismo perceptivo. O commit final também requer CI antes de merge.

---

## Pesquisa de radiação por posição e gestos de tecla — 23/11/2026

Relatório: [RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md](RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md). Revisados **14 pontos de excitação** e T60 acústico do tampo em dois estágios na literatura (não T60 de corda); **quatro IRs Yamaha C3** medidas com alto-falante de contato (não uma FRF mecânica com força de ponte); resultados PNAS 2025 sobre movimentos de tecla e percepção. Auditado novo candidato **Meta Piano CC0** no GitHub: 352 nomes WAV A0–C8 × quatro layers, 352 entradas SFZ, manifestos e licença textualmente verificados, **mas nenhum áudio baixado ou hashado**; fabricante/captação/edição não determinados, sem inclusão no acervo Stage. Reconfirmado que o dataset Hamburgo mede força tecla–base, não ponte; exemplo de FRF de rabāb não oferece parâmetros de piano.

**Sem liberação técnica:** `main` v1.12.4, referência de estabilidade relatada v1.9.5; **50 originais verificadas/seis pianos** inalteradas, **0/7 R-GATEs completos**, P1/P2 e DSP congelados. Não foram executados novos estudos acústicos ou medições reais nesta etapa documental. **CI do PR #14:** [GitHub Actions 45108589481](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45108589481) concluído com sucesso: **95/95 testes Node** e **108 cenários de áudio seco A/B/C sem clipping ou não finitos**, conforme log do job `audio-regression`. Isso valida regressões lógicas/offline da branch, **não** realismo perceptivo ou estabilidade de 32–64 vozes em hardware físico.

---

## Pesquisa industrial Yamaha 2026 e ação de tecla DAFx25 (23/11/2026)

**Validação efetiva da branch documental:** GitHub Actions [run 45108088429](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45108088429), job `audio-regression` concluído com sucesso: **95/95 testes Node**, **108 renderizações secas A/B/C, zero cenários com clipping ou amostras não finitas**, conforme logs. Não houve teste acústico/perceptivo em PC ou Moto g04s nesta rodada; CI não libera os R-GATEs nem prova 32–64 vozes livres de estalos em hardware. Mudança limitada aos arquivos documentais.

**Somente pesquisa:** [auditoria específica](AVANCO_PESQUISA_YAMAHA_2026_ACAO_TECLADO_2026-11-23.md). Preprint Yamaha Corporation de 06/04/2026 descreve martelo viscoelástico, cordas 3D com apoios anisotrópicos, retorno bidirecional ponte/cordas, corpo+ar reduzidos e sons suplementares de Yamaha CFX real; os dados físicos completos não são públicos, o paper não certifica tempo real e **nenhum WAV CFX foi adquirido ou verificado** neste ciclo. O estudo DAFx25 de ação de tecla/martelo fornece quatro CSV públicos (229.397.740 bytes listados), mas sem licença identificada no repositório de origem: **não baixados nem liberados para calibração comercial**. Projeto aberto de síntese Rust GPLv3 consultado só conceitualmente, sem copiar código. Proposto M09: mapeamento da ação/velocity de teclado para velocidade real do martelo e repetição.

**Status inalterado:** biblioteca original 50 arquivos/seis pianos; `main` v1.12.4, referência histórica v1.9.5, A/B/C experimentais, P1/P2 congelados, **0/7 R-GATEs globais integralmente aprovados**. Sem alterações de DSP, UI, MIDI, FX, samples ou presets. Testes Node/CI neste ciclo devem ser anotados conforme execução efetiva, não presumidos a partir de commits anteriores.

---

## Felt original comercial preparado: 15 arquivos íntegros (23/11/2026)

O ZIP **original** \`FuchsUndMoehrSamplesWAV16bit.zip\`, publicado como **Public Domain** pelo criador **Tom Guder**, foi lido seletivamente via HTTP Range da origem Google Drive, sem baixar os 649 MB completos. Seus 264 WAVs estão organizados por **88 notas × 3 camadas**. **15 WAVs originais** de MIDI nominal 36/48/60/72/84, camadas piano/mezzo/forte, foram verificados integralmente (**CRC32, WAV 48kHz/16bit/2 canais e SHA256**), com **36/36 testes aprovados**: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105332553 . Os SHA256 estão em research/commercial_audio/felt_original_verified_sha256.json. Não há áudio em GitHub nem no app.

**Acervo comercialmente elegível acumulado: 50 gravações originais de seis pianos acústicos distintos, 173.943.136 bytes conferidos**, sem ganho em R-GATE físico. A declaração PD e direitos de terceiros serão revisados no lançamento. Continuam faltando par com/sem feltro no mesmo piano, força martelo–corda real, duas polarizações e mobilidade complexa da ponte por região. Plano concreto de medição/contratação em docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md.

**Bloqueio expresso permanece: 0/7 R-GATEs integralmente satisfeitos.** Não modificar DSP, A/B/C/P1/P2, FX, MIDI, UI ou presets. Relatório: docs/PREPARACAO_FELT_ORIGINAL_COMERCIAL_2026-11-23.md.

---

## Preparação comercial ampliada — 35 gravações ORIGINAIS verificadas (22/11/2026)

**Novo:** sete WAVs originais do **Steinway Model D de Princeton (bitKlavier Grand, CC BY 4.0)** foram obtidos INDIVIDUALMENTE de três coleções do Archive.org, PCM 44,1k/16bit, verificados integralmente com SHA256 e apagados após a verificação. Correspondem a C2v8, C4v1/v8/v16 e C6v8 do Piano Bar, além da mesma C4v8 Binaural e Harp Omni. Teste https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45103239343 — 22/22 testes; SHA256 preservados em research/commercial_audio/steinway_d_verified_wav_sha256.json. Os ZIPs completos **NÃO** foram transferidos; dados de áudio **NÃO** estão no GitHub.

**Total acumulado de referências comerciais originais:** 28 WAV/FLAC anteriores + 7 Model D = **35 arquivos / 103.753.348 bytes / cinco pianos acústicos diferentes**. Os três ZIPs Princeton têm metadados oficiais de tamanho/MD5/licença registrados; os WAVs originais são **denoised, cortados e reequilibrados**, não parâmetros físicos diretos. Fonte do Felt Tom Guder Public Domain e link do ZIP WAV autoral confirmados, mas o ZIP original ainda NÃO foi baixado ou conferido.

**Status de liberação permanece 0/7 gates prontos.** Não alterar timbre, DSP, A/B/C, P1/P2, interface, MIDI ou FX. Referências e limites: docs/PRINCETON_STEINWAY_D_FELT_FONTES_COMERCIAIS_2026-11-22.md .

---

## Preparação comercial — 28 fontes sonoras ORIGINAIS verificadas (22/11/2026)

A auditoria comercial passou a possuir **dados efetivamente adquiridos e conferidos**, não só links: **8 WAV VCSL (Steinway Model B + Knight Upright) CC0, 15 FLAC Yamaha C5 Salamander CC BY 3.0 e 5 FLAC Kawai KW FreePats CC0**. Quatro pianos acústicos distintos, 28 arquivos originais e **64.396.672 bytes** totais, 24 bits (WAV 44,1 kHz ou FLAC 48/44,1 kHz). Os arquivos foram validados contra commits e Git blob SHA1 de origem, SHA256 por arquivo e decodificação original; **10/10 testes da verificação aprovados** em https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45101876490 . Os 28 SHA256 estão em research/commercial_audio/verified_source_sha256.json. **Nenhum áudio foi incluído no repositório, no app ou nos artifacts.**

**Cuidado:** VCSL Steinway teve dinâmica normalizada; Yamaha C5 não é CFX, layers v1/v8/v16 não são velocidade física de martelo; Kawai tem loops nos graves e C4vH ausente. Dados são candidatos acústicos comercialmente compatíveis, **não parâmetros físicos calibrados**, e R-GATEs permanecem **0/7 aprovados**. P1/P2 e DSP continuam congelados. Documentação: docs/PREPARACAO_FONTES_COMERCIAIS_PILOTO_2026-11-22.md.

---

## Mudança de requisito: Stage Synth será produto COMERCIAL (22/11/2026)

O usuário esclareceu que **o Stage Synth tem finalidade comercial**. A pesquisa científica deve separar leitura de artigos de uso comercial dos datasets. **BiVib (NC-SA), RWC (NC), MAPS (NC) e MAESTRO (NC-SA)** não são fontes aprovadas para calibração do produto sem autorização específica. **Candidatos legalmente mais promissores:** VCSL (CC0), Kawai KW FreePats (CC0), Salamander Yamaha C5 (CC BY 3.0), Princeton bitKlavier Steinway D (CC BY 4.0), Felt Tom Guder (domínio público declarado) e University of Iowa Steinway B (permissão expressa para quaisquer projetos, sem licença CC identificada). Os candidatos ainda precisam de arquivos e direitos específicos conferidos.

Não há arquivo LICENSE na raiz; a licença de distribuição do código Stage e atribuições de terceiros precisam ser definidas pelo titular/revisão jurídica. **Motor P2 e experimento P1 permanecem bloqueados**, nenhum DSP/preset/UI/MIDI/FX alterado. Matriz legal: docs/POLITICA_COMERCIAL_DADOS_LICENCAS_2026-11-22.md.

---

## BLOQUEIO DE IMPLEMENTAÇÃO — auditoria de referências (22/11/2026)

**Situação: NÃO PRONTO. O usuário solicitou não prosseguir com a implantação de novos motores físicos até estarem preparadas todas as referências essenciais.** Foram verificadas 22 fontes/famílias primárias e as 18 lacunas anteriores. A teoria física é ampla, porém **0/7 critérios de prontidão integralmente comprovados**: originais de BiVib/RWC/bitKlavier e medidas da ponte/martelo ainda não estão adquiridos/alinhados; há restrições de licenças NC, incertezas de parâmetros e o medidor E0 precisa de validação sintética. Nova fonte Plath/Hamburgo reúne força tecla–base, aceleração da ponte e pressão binaural a 50 kHz, mas NÃO mede força martelo–corda/força aplicada na ponte. Liang/QMUL tem posição contínua de pedal e som real. P1 permanece experimental e **a programação do P2 está congelada**.

Auditoria principal: docs/PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md. Não houve mudança em DSP, UI, MIDI, FX, presets ou arquivos de áudio; somente documentação.

---

## E1 — auditoria das lacunas físicas antes de nova implementação (22/11/2026)

A pesquisa verificou **18 lacunas P0/P1/P2** no Stage Synth a partir do código do main commit ba224226 e de Smith/Bank/Weinreich/Chabassier. Os P0 são martelo–corda não linear, uníssonos e polarizações, ponte/tampo passivos, perdas/rigidez por parcial, **falha de faixa da análise de B**, identificação de parâmetros e validação auditiva/CPU em hardware. **O medidor E0 procura apenas ±2,5% em n×f_ET**, ao passo que B=0,0012 desloca a oitava parcial +3,707%; os números relativos de 33 referências não autorizam calibrar um novo motor. CC64 perde valores intermediários antes da camada mecânica; CC66/67 ainda não são modelados. **Não houve mudança de DSP, UI, presets, MIDI nem FX nesta auditoria.** O P1 permanece isolado no PR #2.

Rastreabilidade, bibliografia e gates de implementação: docs/AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md. Experimentos E1 separados podem começar, mas P1/P2 não devem ser promovidos sem validação.

---

**Complemento Steinway D (2021/2026):** bitKlavier Grand/Princeton disponibiliza 16 camadas em notas amostradas a cada terça menor, 9 posições estéreo, WAV até 96k/24 bits **CC BY 4.0**, mas o áudio foi denoised/recortado e seus níveis reequilibrados; serve para timbre e radiação, **não** velocidade física do martelo. A Vienna Symphonic Library disponibiliza demonstrações de Yamaha CFX verdadeiro, produto comercial com ressonâncias/FX, referência perceptiva e **não** WAV aberto. CCMusic apresenta 1.320 notas e 29 avaliadores humanos de pianos variados, com licenças restritivas para distribuição.

## Qualificação científica das referências sonoras (22/11/2026)

A comparação E0 de 33 amostras foi revisada: falta sincronização de dinâmica física, mic, sala e condições de gravação; **não tratar seus valores em dB como nota de realismo nem usar como único alvo de DSP**. Foram localizadas fontes experimentais mais apropriadas: **BiVib Yamaha cauda/vertical, 10 velocities × 88 notas, WAV 96k/24b e metadados binaurais/calibração**; **RWC Yamaha/Steinway/Bösendorfer reais, 3168 sons com estilos/pedal e três dinâmicas**; **MAPS Yamaha Disklavier real com close/ambient**; **MAESTRO** para desempenho musical e pedais. Todas exigem respeitar licença de uso não comercial e restrições próprias; nenhum novo áudio foi baixado nem incorporado.

Catálogo com fontes, critérios e o plano E1: docs/AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md. A P1 continua isolada; v1.9.5 está preservada, sem mudanças nos motores A/B/C.

---

## E0 — comparação de áudio real dos quatro pianos (22/11/2026)

Na branch de pesquisa E0 foi implementado um procedimento de CI que **baixou e analisou efetivamente 33 gravações isoladas** de Yamaha C5, Steinway B, Felt Fuchs & Möhr e Upright Knight (amostras AIFF/WAV/AAC em /tmp somente). Nenhum sample foi incorporado ao GitHub, à aplicação ou ao artifact: somente proveniência e métricas JSON. A análise foi comparada a todos os motores A/B/C em 48 kHz, sem FX, mantendo DSP original e a v1.9.5. O resultado aponta forte diferença de amplitude relativa de parciais nos graves B/C, mas não é uma avaliação subjetiva de realismo; pp/mf/ff e níveis AAC não representam um velocity MIDI comum. Notas com menos de três parciais detectáveis têm estimativa de B nula. A nova observação espectral curta de ataque busca reduzir falsos negativos em C6 sem tratá-la como rigidez de corda.

Detalhes e cautelas: docs/ANALISE_AUDIO_REAL_E0.md. A meta 32/64, áudio real em PC/Moto g04s e o experimento isolado P1 permanecem sem homologação.

---

## Referências sonoras verificadas para os quatro pianos (22/11/2026)

Catálogo detalhado em [REFERENCIAS_SONORAS_YAMAHA_STEINWAY_FELT_UPRIGHT_2026-11-22.md](REFERENCIAS_SONORAS_YAMAHA_STEINWAY_FELT_UPRIGHT_2026-11-22.md).

- Yamaha: Salamander Grand Piano **Yamaha C5 real**, 16 intensidades CC BY 3.0; **CFX** GSi Venice Grand apenas para referência perceptiva até conseguir arquivos brutos licenciados.
- Steinway: Universidade de Iowa **Model B**, notas AIFF individuais pp/mf/ff e site de permissão sem licença SPDX; Ivy Piano in 162 com 5 camadas, 2 posições e pedal up/down, uso de amostras limitado aos termos da biblioteca.
- Felt: Fuchs & Möhr felt upright de Tom Guder, 3 camadas WAV estéreo, declarado domínio público pelo autor.
- Upright: FreePats Kawai KW, 2 intensidades, CC0 1.0; graves editados com loop, **não adequados para T60 real**.
- [ ] Adquirir e verificar localmente pequenos subconjuntos de notas, medir metadados e licenças. NENHUM arquivo de som foi incluído no GitHub.
- [ ] Alinhar C2/C4/C6 e intensidades reais dos bancos, sem atribuir velocities MIDI fictícias a pp/mf/ff. Medir canais, ataque, parciais, B e decaimentos, verificando reverb e loops.
- [ ] Comparar A/B/C com áudio nivelado e laboratório de CPU antes de qualquer modificação de timbre.

**Nenhum DSP, interface, módulo, preset, áudio de terceiros ou conteúdo privado do usuário foi alterado/publicado nesta pesquisa.**

---

## Pesquisa aprofundada de física de piano (22/11/2026)

Estudo científico/arquitetural de martelo, cordas rígidas e acopladas, ponte/tampo, radiador e amortecedores: docs/FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md. **Sem alterações do DSP ou do aplicativo.** O experimento P1 de duas seções allpass continua isolado no PR #2 e não é versão integrada. A próxima implementação exige calibração com notas secas licenciadas e comparação auditiva, preservando v1.9.5/32–64 notas.

---


## Resultados P0 verificados no GitHub Actions (22/11/2026; UTC da execução em 23/11)

- Commit de diagnóstico: 2b27cf51ed921ab2254ed3a5af2b26126752c063.
- Workflow: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45094083550 — **90/90 testes Node aprovados, 0 falhas**.
- Matriz completa: **108/108 combinações renderizadas**, sem clipping ou amostras não finitas no sinal seco médio (FX desligados). JSON disponível como artifact do workflow por 14 dias.
- Japanese / velocidade 80: estimativa B por FFT em C2, C4, C6:
  - A modal: 0,00024496; 0,00035775; 0,00148165.
  - B waveguide v1.9.5: 0,00005294; 0,00010944; 0,00027679.
  - C acoplado: 0,00005478; 0,00011025; 0,00027700.
- B e C têm estimativas de inarmonicidade e níveis RMS muito semelhantes nessa condição; **o acoplamento mecânico não resolveu a dispersão original das cordas**. Isso não prova que os sons sejam perceptualmente idênticos.
- Não declarar B-alvo universal com base nesses números: FFT finita, ajustes de modelo, perfis de registro, batimentos e sinais fracos podem enviesar a estimativa. É necessário comparar com referência seca autorizada e escuta nivelada.
- **Recomendação P1:** modificar dispersão e perdas dependentes de frequência **em branch experimental isolada**, mantendo B v1.9.5 e A/C atuais como referência. Atingir 32/64 vozes em hardware continua pendente.

---

## Pesquisa P0 — baseline acústica A/B/C (branch experimental, 22/11/2026)

Na branch research/piano-acoustic-metrics-v124, derivada do main bcfb40a8, foram adicionados analisador FFT/inharmonicidade/decaimento, testes unitários, diagnóstico reproduzível de 108 casos A/B/C e workflow CI; consultar docs/BASELINE_ACUSTICA_V124.md. **Não há alteração de DSP, interface, presets nem publicação do aplicativo.** Os 5 testes locais isolados do analisador passaram; a suíte integrada, artefato de diagnóstico e teste em hardware dependem de conferência do workflow. A v1.9.5 permanece a referência relatada sem estalos; não promover a branch automaticamente.

---

# Atualização do aplicativo principal — Stage Synth v1.12.4 (22/11/2026)

**Confirmado no código publicado:** o módulo Piano Acústico possui três implementações selecionáveis em **Motor do piano**, sem módulos ou links extras.

- **A · Claude (modal):** implementação modal adaptada já presente em `piano-worklet.js`. O código externo original do Claude não foi recuperado independentemente.
- **B · Stage físico anterior (v1.9.5):** arquivo histórico de DSP `experimental/physical-v1.9.5/physical-piano.js`, incluído como `physical-piano-legacy.js` num AudioWorklet próprio (somente o identificador do processador mudou). É a base com estabilidade relatada no PC.
- **C · Novo Stage mecânico:** motor integrado v1.12.3, com ponte/tampo/cordas simpáticas. Seleção `physical` antiga continua apontando para C.
- A síntese clássica continua disponível para compatibilidade.

**Não confundir B com o Novo Stage original v1.11.0 de outra conversa:** a fonte exata da v1.11.0 continua ausente deste repositório. A inclusão de B fornece uma comparação verificada, não reproduz a versão externa.

Testes locais: **84 testes Node aprovados**, testes de seletor em navegador simulado desktop/Android aprovados, sem novo módulo. O ambiente de Chromium bloqueou navegação localhost para validar os três AudioWorklets reais. O desempenho e a fidelidade ainda exigem validação no PC e Moto g04s.

Os WAVs de referência permanecem privados. As versões experimentais anteriores não foram apagadas.

---

# ATUALIZAÇÃO CONFIRMADA — 22/11/2026: v1.12.3 integrada ao aplicativo principal

O código da **raiz de main** agora é **v1.12.3**, com seleção A/B no **módulo Piano Acústico → Motor do piano**. Substitui o diagnóstico anterior de raiz v1.8.4 (mantida no histórico Git). A, modal derivado da linha Claude; B, motor físico **baseado na v1.9.5 + mecânica v1.12.2**. Não se trata da fonte original da linha separada Novo Stage v1.11.0.

A v1.9.5 experimental permanece a **referência estável comprovada pelo usuário sem estalos**. A nova v1.12.3 exige verificação auditiva e de latência no PC e Moto g04s. Nenhum novo módulo ou link externo foi acrescentado; atalhos anteriores removidos. 79 testes de lógica aprovados e interface testada em Chromium simulado, sem homologação do AudioWorklet real.

---

# Stage Synth — estado real do projeto

**Última conferência:** 22/11/2026. Verificar novamente o GitHub antes de começar qualquer nova tarefa; este documento não é uma consulta automática ao HEAD.

## Mapa das linhas de desenvolvimento

| Linha | Local no repositório | Estado |
|---|---|---|
| Site principal | raiz de `main` | `package.json` = **v1.8.4**; app principal publicado pelo GitHub Pages a partir da raiz. Perfil móvel originalmente limita a 8 vozes nesta linha. |
| Piano físico estável para o usuário | `experimental/physical-v1.9.5/` | O usuário relatou **eliminação dos estalos no PC**. É estabilidade **relatada em campo**, não garantia de desempenho em todos os dispositivos. |
| Piano físico v1.9.6 | `experimental/physical-v1.9.6/` | Novo ataque de martelo experimental; a fidelidade ainda foi considerada insuficiente. Auditoria acústica apontou problemas fundamentais. |
| Pesquisa acústica posterior | `experimental/mechanical-resonance-v1.12.1/` | **Protótipo independente**, com ponte/tampo/cordas simpáticas e retorno limitado às cordas. Não é um piano completo nem foi integrado ao Novo Stage. |
| "Novo Stage v1.11.0" de outra conversa | **Fonte ainda não localizada neste repositório** | Há relato de tampo estéreo com duas zonas de escuta/excitação, mas o código-fonte daquela linha precisa ser obtido/identificado antes de integrar módulos. Não inventar uma integração. |
| Outras versões de piano | `experimental/physical-v1.9.0/` a `physical-v1.9.4/` | Histórico de experimentação e comparações. Não substituir nem apagar. |

**Distinguir:** "versão principal" (raiz), "versão sem estalos segundo o usuário" (v1.9.5 experimental) e "experimento de DSP mais recente no repositório" (v1.12.1). Não há uma v1.12.1 pronta para tocar neste momento.

## Escopo funcional conhecido

O aplicativo possui seis módulos: Piano Acústico (Japanese, American, Felt, Upright), Piano Elétrico, Órgão, Synth, Leitor SF2 e rack de FX, além de recursos MIDI e controles de performance. Histórico e diferenças por versão estão nos respectivos `README.md` e `CHANGELOG.md`. **A presença de uma função numa pasta experimental não prova sua presença no site principal.**

## Requisitos de áudio confirmados

- **O problema prioritário atual é a falta de fidelidade dos quatro pianos acústicos.**
- Os estalos do PC foram relatados como resolvidos na v1.9.5; preservar essa base enquanto novos modelos são comparados.
- **Mínimo desejado: 32 notas. Meta: 64 notas.** São critérios de aceitação, não capacidades confirmadas em todos os modos.
- O Moto g04s é alvo de otimização; o desempenho do AudioWorklet completo ainda exige validação nesse dispositivo real.
- O usuário considera o som de corda isolada insuficiente: faltam martelo, mecanismo, amortecedores, interação entre cordas, ponte/tampo e caixa/radiação.

## Evidências técnicas disponíveis

- `docs/VERIFICACAO_CLAUDE_PIANO_V196_2026-11-22.md`: auditoria externa reproduzida; v1.9.6 físico **2/5** no scorecard acústico aproximado, modal **5/5**, mas o modal nessa implementação fica limitado a 32 vozes; critérios não provam realismo.
- `docs/PLANO_FIDELIDADE_PIANOS_APOS_V195.md`: diagnóstico do motor e orçamento de desempenho.
- `docs/CAPTURAS_QUATRO_PIANOS_2026-11-22.md`: WAVs sincronizados Japanese/American/Felt/Upright, **com efeitos originais**, usados para referência do som final; não são medições secas de notas isoladas.
- `docs/CAPTURAS_NOVE_PIANOS_ELETRICOS_2026-11-22.md`: referências de 9 elétricos, também sem publicar os WAVs.
- `experimental/mechanical-resonance-v1.12.1/README.md`: limitações e testes do acoplamento. Os benchmarks representam **cordas de teste simplificadas**, não 64 vozes reais do aplicativo.

## Últimos fatos confirmados nesta organização

- A raiz de `main` possui `package.json` **1.8.4** e a pasta `experimental/` contém as versões 1.9.0 a 1.9.6 e o protótipo 1.12.1.
- Workflow do GitHub Pages da versão anterior a esta organização concluído com sucesso; confirmar novamente os próximos deploys.
- Não foi feito merge do núcleo mecânico v1.12.1 para o sintetizador principal.
- Estes documentos de governança **não alteram o DSP**, o visual, presets ou MIDI.

## Como atualizar este arquivo

Após uma entrega, acrescentar: **versão/pasta + commit SHA + mudança real + testes executados + teste em hardware (se houver) + link de publicação confirmado + limitações abertas**. Não apresentar benchmark offline como desempenho garantido no celular.

## Atualização experimental v1.12.2 — 22/11/2026

- **Novo experimento executável:** `experimental/physical-mechanics-v1.12.2/`. É uma integração do núcleo `mechanical-resonance-v1.12.1` no AudioWorklet físico **baseado na v1.9.5**, não um merge no Novo Stage v1.11 de outra conversa (fonte ainda ausente do repositório).
- **Integração:** feedback mecânico limitado devolvido à corda no próximo sample, 88 estados de amortecedores, CC64, corpo estéreo, cordas simpáticas e seletor A/B `Acoplamento mecânico`.
- **Validação:** 76 testes automatizados de lógica passaram; interface validada em desktop e Android simulado. Testes de 32 e 64 notas sem clipping offline; bypass A/B com saída original idêntica quando desligado. Benchmark Node offline aproximado: 32 vozes 77→91 ms/1s; 64 vozes 219→246 ms/1s. São números de computador de testes, **não** homologação em hardware do usuário.
- **Pendente:** Chrome AudioWorklet real bloqueado neste ambiente (localhost `ERR_BLOCKED_BY_ADMINISTRATOR`), comparação auditiva com as quatro referências, testes reais no PC/Moto g04s e obtenção do código do Novo Stage v1.11.
- **Não houve substituição da raiz v1.8.4 nem da base estável relatada v1.9.5.**


## Correção de acesso ao experimento v1.12.2 (22/11/2026)

O aplicativo principal na raiz ainda é v1.8.4; a implementação do acoplamento mecânico **não está incluída nesse motor**. Para eliminar confusão, foi adicionado na página principal um link explícito para `experimental/physical-mechanics-v1.12.2/acesso-motor-v1.12.2.html` e, no experimento, um botão **Ativar piano mecânico** que seleciona a síntese física, ativa acoplamento, abre o editor do piano e tenta iniciar o AudioWorklet.

O endereço separado também evita reutilizar a página anterior do navegador. A existência do botão e o estado selecionado foram testados em Chromium simulado; a inicialização real do AudioWorklet ficou bloqueada pela origem de teste. A ativação em Chrome real e a audição no PC/Moto g04s continuam pendentes de confirmação do usuário.
