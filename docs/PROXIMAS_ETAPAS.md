# Motor D — ações depois da integração experimental (23/11/2026)

1. **Prioridade imediata:** testar D em navegador real em PC e Moto g04s: inicialização do AudioWorklet, troca A/B/C/D, MIDI, sustain, sem estalos, uso de CPU e 32/64 notas simultâneas. Testes Node/callback simulado **não são homologação**.
2. Ouvir D em **C2/C3/C4/C5/C6** e acordes, com FX desligados e nível alinhado; comparar com A/B/C e as 65 amostras originais verificadas (incluindo 15 Iowa Steinway B), sem prometer fidelidade. Anotar *guitar-like*, martelo, corpo, graves e duplo decay, com notas de diagnóstico.
3. Avaliar fechamento de R-GATEs por evidência: parâmetros aproximados no D NÃO são dados físicos medidos; a reconstrução física e a licença do produto ainda precisam de revisão.
4. D permanece **experimental e não padrão** até teste auditivo e de hardware. A autorização do usuário (“Vamos gerar um motor com o que temos até aqui”) **é específica do novo D**, não licença para mexer A/B/C/FX/MIDI.

---

# PRIORIDADE ÚNICA — fechar lacunas, não ampliar a pesquisa (23/11/2026)

**Plano operacional vigente:** [PLANO_ENXUTO_FECHAMENTO_LACUNAS_2026-11-23.md](PLANO_ENXUTO_FECHAMENTO_LACUNAS_2026-11-23.md). **Sequência: (1)** **CONCLUÍDO** download/integridade 15/15 AIFF originais Steinway B/Iowa, somados aos 15 Yamaha C5 já verificados ([run 45111873583](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45111873583), hashes em `research/commercial_audio/iowa_steinway_b_verified_original_sha256.json`), pendente aferição f0; **(2)** resolver lacunas de pedal, release, direitos e hashes; **(3)** formalizar modelo passivo reduzido e parâmetros com origem explícita; **(4)** fechar aferição do analisador, matriz de avaliação e aceite para 32/64 vozes; **(5)** rever sete gates e exigir autorização expressa antes de novo DSP. A mobilidade 2×2 e a histerese medidas **não são exigências absolutas por padrão**, pois o R-GATE-2 já admite aproximação passiva justificada e calibrável. Não procurar outras bibliotecas nem adicionar motores/código agora. **0/7 gates integralmente aprovados até prova contrária.**

---

# Fontes de modelos numéricos e distinção de licenças — 23/11/2026

[Relatório H01–H04](MODELOS_NUMERICOS_DUSSEK_MF1_DRYAD_CC0_2026-11-23.md).

- [x] Auditar **Dussek** em GitHub: licença do MOTOR **AGPLv3**, preset **Grand B CC BY 4.0**, preset Upright C **CC BY-SA 4.0**; manifesto 88 notas, parâmetros derivados de gravações e arquivo `data.bin` de **514.040 bytes** com SHA256 **declarado**, não recalculado neste ciclo.
- [x] Auditar **MF-1** MIT e `piano_tables.inc`: 30 notas amostradas, 970 parciais, corpo de 32 modos e máximo de 384 osciladores; sem confundir limite de osciladores com 32–64 VOZES completas; lacunas de ressonância simpática e abafadores reconhecidas.
- [x] Corrigir classificação do **Dryad**: datasets publicados **CC0**, enquanto artigo publicado pode ser NC-ND; `Code_Data.zip` e `README.md` listados, mas não adquiridos/hashados devido a acesso 403; sensores documentados são de **movimento de tecla**, não força martelo–corda nem ponte.
- [x] Revisar riscos de novos corpora: Zenodo localização de tecla = **respostas de participantes**, não WAV de teclado; dataset 2026 pedal on/off baseado em **VST e MIDI de terceiro**, não em medição do sistema físico de abafadores.
- [ ] Antes de usar números de terceiros, conferir **hash original** do `data.bin` e autorização de derivados/atribuições, e medir acurácia para notas não amostradas; **não importar nem integrar enquanto bloqueio de DSP estiver ativo**.
- [ ] Resolver disputa de possíveis rótulos da série Iowa via **áudio original** e pitch detector aferido, sem presumir qual projeto externo está correto.
- [ ] Se útil para M09, adquirir e auditar somente dados Dryad CC0 de posição/gestos de tecla, descartando dependências de código não verificadas; não somar à biblioteca de 50 WAV.
- [ ] Seguir busca de **F_h(t)/δ(t)/H/V/Y_ponte 2×2 efetivamente medidos** em um piano com permissão comercial. PAPA/IRCAM e medições próprias continuam vias prioritárias.
- [ ] Manter **0/7 R-GATEs integralmente aprovados**; nenhum DSP/P1/P2 nem garantia de 32/64 vozes até referências essenciais, testes e autorização expressa.

---

# Investigação de acesso real aos dados físicos do piano — 23/11/2026

[Auditoria PAPA / IRCAM / força inversa](ACESSO_DADOS_FISICOS_PAPA_IRCAM_FORCA_INVERSA_2026-11-23.md).

- [x] Localizar relatório oficial **FWF PAPA**: cerca de seis instrumentos reais medidos, modelo global 3D, parâmetros martelo/corda/ponte/campo acústico; **arquivo bruto e direito comercial ainda não identificados**.
- [x] Verificar o método JASA 2016 de estimar `F_h(t)` por **vibrometria física de corda** e filtro inverso, não por amostra de microfone; inserir M01.2 com necessidade de comparação/erro.
- [x] Confirmar no estudo TU/e de **Bösendorfer 280VC-9** que tampo domina e que estrutura/aro no grave pode contribuir; planejar M05 estendido e futura ablação, não simulação automática de peça adicional.
- [x] Confirmar que o **IRCAM Modalys** documenta modelos de tampo baseados em medição, malha 13×13 e arquivos `.dat` distribuídos no programa; **bytes e licença comercial não verificados**.
- [x] Confirmar que Purdue apresenta `p/v_b` por posições e excitações normal/paralela, mas **não verificamos dados brutos**.
- [ ] Esclarecer com custodiante **PAPA/FPM2** existência de dados originais, unidades, sincronização, direitos e subconjunto comercial; **nenhum contato enviado**.
- [ ] Esclarecer com **IRCAM** uso independente de dados modais no Stage comercial, além da existência/atribuição do arquivo; **não extrair modelo não licenciado**.
- [ ] Se fontes históricas não forem licenciáveis, elaborar escopo e adquirir, por profissional, piloto M01.1/M01.2+M02–M05 do **mesmo instrumento**, inclusive mobilidade cruzada 2×2 e radiação do aro no grave.
- [ ] Manter R-GATE-1..7 sem aprovação; sem novo DSP/P1/P2 até dados, direitos e liberação expressa; sem garantia 32–64 vozes antes da homologação.

---

# Próxima lacuna P0: mobilidade cruzada de ponte e histerese do martelo — 23/11/2026

[Documento científico F01–F08](EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md) e [protocolo M01.1/M04.1 atualizado](PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md).

- [x] Conferir medições publicadas reais de contato F_h(t), compressão/rebote e movimento ortogonal do martelo (1984, 1991, 1998) sem confundir a figura de um Steinway com dados brutos reutilizáveis.
- [x] Identificar exemplo quantitativo de upright medido por Ege/Boutillon (2010): massa, densidade modal, perdas e mudança de regime estrutural; **somente referência do instrumento publicado**, nunca Yamaha/Steinway calibrados.
- [x] Confirmar que modelo de ponte para duas polarizações requer resposta complexa cruzada **2×2** para inferir transferência T↔P e double decay; esclarecer que M04 escalar inicial não basta para a alegação de física completa.
- [x] Verificar evidência de modelo reduzido de **cinco modos** no artigo JASA 2024, **sem afirmar equivalência sonora integral ou 64 vozes em Web Audio**.
- [x] Verificar direitos do comparador híbrido Simionato et al.: código externo **LGPLv3**, dataset Kaggle com direitos comerciais ainda não verificados; sem copiar código/treinar modelos.
- [ ] Contratar ou obter autorização comercial de **medidas originais do mesmo piano** para M01.1 (F(t), δ(t), histerese) e M02/M03 (H/V e uníssonos), M04.1 (mobilidade ponte 2×2) e M05 (radiador). Separar conteúdo próprio, permissões de divulgação e parâmetros derivados.
- [ ] Caso só exista mobilidade escalar normal, registrar explicitamente os termos Y_TP/Y_PT/Y_PP como desconhecidos e avaliar alternativa **offline** sem aprovar R-GATE-2 nem novos motores.
- [ ] Preparar E1.0 (cadeias A/B/C comparáveis) e E1.1 (estimador com B sintético conhecido), **ainda não implementados** pela regra de congelamento.
- [ ] Homologar, quando autorizado, comportamento auditivo e callback real com 32 mínimo / 64 meta no PC e Moto g04s, sem prometer resultado antes do teste.

**Situação:** teoria mais precisa; **nenhuma nova série original de martelo ou ponte licenciada**, 50 áudios originais previamente confirmados inalterados, **0/7 R-GATEs integralmente completos**, nenhum DSP/P1/P2 implementado neste ciclo.

---

# Preparação adicional de tampo, toque e nova referência Upright CC0 — 23/11/2026

Ver [relatório técnico N01–N06](RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md).

- [x] Conferir artigo de resposta espacial em **14 pontos do tampo**; não confundir T60 de percussão de tampo com decaimento de parciais de cordas.
- [x] Conferir captura em quatro posições **Yamaha C3 AudioLabs**, IR de alto-falante de contato → microfones que inclui sala; não equiparar a mobilidade mecânica v/F da ponte.
- [x] Identificar estudo PNAS 2025 sobre percepção do timbre e movimentos de tecla, com publicação NC-ND e direitos do dataset Dryad ainda não confirmados para uso comercial.
- [x] Auditar a fonte externa **Meta Piano CC0**: 352 nomes no manifesto / 88 pitches × quatro camadas, SFZ e CC0; não há hash dos WAV originais validado. **Conservar total Stage de 50**, sem incorporar amostras no app.
- [x] Delimitar N05 força tecla/base ≠ força ponte, e N06 resposta medida de rabāb ≠ piano. N06 pode orientar *formato* de ensaio, nunca calibração Stage.
- [ ] Obter pelo menos um piloto comercialmente autorizado de F_h(t), duas polarizações/1–3 cordas, Y_ponte(f) COMPLEXA e radiação no **mesmo piano**; registrar incerteza, fase, microfones, referência de tempo e condições.
- [ ] Especificação E1.1 atualizada: verificar f1/B até B=0,003 com misturas H/V, desaparição de parciais de ataque e relação de cadeias A/B/C. **Ainda não executada**.
- [ ] Somente se houver benefício real para Upright, validar WAV/ZIP, origem acústica e direitos do Meta Piano; não atribuir marca/modelo não declarado.
- [ ] Manter M01–M09 e R-GATE-1..7 congelados até documentação e dados físicos completos. Sem DSP/P1/P2, sem prometer 32–64 vozes livres de estalos antes dos testes no aparelho.

---

# Pesquisa Yamaha 2026 / ação de tecla — prioridades adicionais (23/11/2026)

Relatório: [AVANCO_PESQUISA_YAMAHA_2026_ACAO_TECLADO_2026-11-23.md](AVANCO_PESQUISA_YAMAHA_2026_ACAO_TECLADO_2026-11-23.md).

- [x] Auditar estudo de pesquisadores da Yamaha (preprint 2026): martelo viscoelástico, polarizações com apoios anisotrópicos, cordas ↔ ponte/tampo ↔ radiação, redução CMS, CFX real suplementar mas dados físicos proprietários.
- [x] Verificar existência de dados públicos DAFx25 de ação de tecla/martelo (quatro CSV, 229.397.740 bytes listados), **sem licença confirmada de uso comercial** e sem baixar.
- [x] Identificar limite jurídico da implementação aberta Unsampled Piano (**GPLv3**); somente referência conceitual, sem importar código.
- [ ] Esclarecer direitos e efetiva disponibilidade do suplemento WAV CFX de Yamaha; não somar às 50 fontes validadas antes de integridade/hashes/direitos.
- [ ] Preparar **M09** (evento MIDI → tecla → let-off → velocidade real do martelo e repetição) e autorização de dados de ação se fizerem parte do produto.
- [ ] Prosseguir M01–M08 medidos e licenciados, E1.0/E1.1 e sete R-GATEs. **Não iniciar DSP/P1/P2 antes da liberação expressa.**

**Invariantes:** main v1.12.4; v1.9.5 preservada; 50 arquivos originais/seis pianos; **0/7 R-GATEs liberados**; objetivo 32–64 vozes ainda não homologado.

---

# Preparação autoral Felt concluída para 15 WAVs; física comercial ainda pendente (23/11/2026)

**Fontes e protocolo:** [PREPARACAO_FELT_ORIGINAL_COMERCIAL_2026-11-23.md](PREPARACAO_FELT_ORIGINAL_COMERCIAL_2026-11-23.md) · [PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md](PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md).

- [x] Confirmar declaração original **Public Domain** de Tom Guder para Fuchs & Möhr Felt (WAV estéreo 16bit, três camadas), diferenciando-a de arquivos de espelhos.
- [x] Acessar o ZIP original por HTTP Range sem transferir o pacote inteiro (**648.995.046 bytes**).
- [x] Indexar **264 WAVs no ZIP original = 88 notas × 3 layers**; auditar os nomes f21–f108, m21–m108, p21–p108.
- [x] Verificar **15 WAVs originais** MIDI nominais 36/48/60/72/84, camadas piano/mezzo/forte, **CRC32, PCM 48 kHz/16bit estéreo, SHA256** e integridade; **36/36 testes** em https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105332553 .
- [x] Preservar 15 hashes SHA256 apenas como metadados; nenhum WAV/ZIP enviado ao repositório, app ou artifact.
- [x] Formalizar **M01–M08 ensaios físicos** com medições de martelo, corda H/V, uníssonos, ponte mobilidade complexa, radiador, pedal e Felt A/B com direitos comerciais.
- [ ] Confirmar juridicamente a cadeia de direitos da declaração PD e condições de comercialização com créditos apropriados, além dos CC BY/CC0.
- [ ] Obter **mesmo piano com e sem feltro** com mic/dinâmica/afinação controladas; as 15 gravações originais não isolam a física do feltro.
- [ ] Obter/parar de procurar e contratar medições autorizadas **F_h(t), δ(t), corda H/V e Y_ponte(f)=v/F complexa** em instrumentos-alvo, com incerteza e procedência.
- [ ] Verificar direitos do arquivo \`tests/fixture_minimal.sf2\`, licença de distribuição do código Stage e notices de terceiros antes de comercializar.
- [ ] Completar os **sete R-GATEs** e só então solicitar liberação de implementação; permanecem **0/7 integralmente aprovados**.

**Total de fontes sonoras de referência verificadas:** 50 originais de seis instrumentos reais, sem alteração em DSP, MIDI, UI, FX, presets ou P1/P2.

---

# Continuidade da preparação comercial Steinway D / Felt (22/11/2026)

Documento: [PRINCETON_STEINWAY_D_FELT_FONTES_COMERCIAIS_2026-11-22.md](PRINCETON_STEINWAY_D_FELT_FONTES_COMERCIAIS_2026-11-22.md).

- [x] Conferir em fonte autoral o **Steinway Model D de Princeton**, CC BY 4.0, 16 layers em amostras a cada terça menor, nine microphone positions, denoise e rebalancing.
- [x] Localizar e validar no Archive.org **três ZIPs Model D** com MD5 e tamanho oficial de Piano Bar/Binaural/Harp Omni (**2.978.146.922 bytes somados**); ZIPs não baixados.
- [x] Encontrar **17/17 nomes de membros WAV** nos índices e comprovar extração direta de uma nota sem baixar ZIP grande.
- [x] Conferir integralmente **sete WAVs Model D originais**, PCM 44,1kHz/16bit, SHA256 permanente; **22/22 testes da preparação**, sem publicar áudio. Subconjunto de cinco pianos agora 35 arquivos originais / 103,75 MB.
- [x] Localizar no fórum do criador Tom Guder o ZIP WAV stereo 16bit, três layers, Felt Fuchs & Möhr, com **declaração Public Domain** e link autoral Google Drive.
- [ ] Obter e validar **ZIP original Felt** (tamanho, bytes, SHA256), confrontando a proveniência com os nove WAVs CueHarbor E0; não afirmar pares com/sem feltro.
- [ ] Avaliar se ampliar Model D para 48k/24bit e mais notas/velocity é necessário; nenhum ganho de fidelidade física pode ser alegado apenas por mais WAVs.
- [ ] Preparar curva de martelo/massa/F(t)/δ(t), mobilidade complexa da ponte por região, two polarizations e captura própria Felt pareada com direito comercial.
- [ ] Revisar LICENSE do código, notices para CC BY e autoria do fixture mínimo SF2; não assumir distribuição automaticamente permitida.
- [ ] Completar **os sete R-GATEs** antes de qualquer DSP/P1/P2 e obter autorização expressa para retomar.

**Regra:** preparação e documentação somente, áudio de terceiros fora do repositório e do app.

---

# Preparação concreta de fontes originais comerciais (22/11/2026)

[Relatório do piloto](PREPARACAO_FONTES_COMERCIAIS_PILOTO_2026-11-22.md) e hashes em research/commercial_audio/verified_source_sha256.json (sem gravações).

- [x] Fixar versão de origem por commit e arquivo Git blob para VCSL CC0, Salamander C5 CC BY 3.0 e Kawai KW CC0.
- [x] Validar **8 WAV VCSL originais**, **15 FLAC Yamaha C5** em C2–C6 (5 regiões, 3 layers) e **5 FLAC Kawai KW**; 28 arquivos / 64,4 MB com tamanho, integridade e codec confirmados, sem armazenar samples nos artifacts.
- [x] Executar **10 testes offline** e decodificação FLAC integral em runner; guardar SHA256 em manifesto permanente não reversível.
- [x] Verificar que **VCSL Steinway é normalizado**, Knight amostra cada tom inteiro e que **C4vH Kawai não existe**, sem inventar velocidade física.
- [ ] Preparar audio de Princeton bitKlavier Steinway D CC BY 4.0 por mic; download é ZIP grande e arquivos têm denoise/ajuste de níveis.
- [ ] Verificar áudio Felt do autor e uma captação controlada com/sem feltro; reconhecer repacotamento anterior.
- [ ] Obter e documentar **medidas físicas próprias autorizadas** de martelo, mobilidade da ponte, uníssonos e polarizações; o sinal de microfone não basta para identificá-las.
- [ ] Revisar ATTRIBUTIONS, direitos dos assets existentes e LICENSE do código antes de comercialização.
- [ ] Validar os sete R-GATEs e pedir autorização explícita para retomar o motor.

**Continuar sem DSP, UI, FX, MIDI ou P1/P2.** A fonte original comercialmente elegível não é automaticamente física calibrada.

---

# Critério comercial obrigatório para todas as referências (22/11/2026)

**O Stage Synth é comercial.** Documento: [POLITICA_COMERCIAL_DADOS_LICENCAS_2026-11-22.md](POLITICA_COMERCIAL_DADOS_LICENCAS_2026-11-22.md). Nenhuma implantação de novo DSP até haver corpus e parâmetros fisicamente adequados **E legalmente utilizáveis para esse fim**.

- [x] Confirmar regras autorais CC0, CC BY e CC BY-NC por fonte oficial, e inventariar acervos e licenças.
- [x] Classificar VCSL CC0, Salamander CC BY 3.0, bitKlavier Grand CC BY 4.0, Kawai KW CC0, Felt PD declarado e Iowa com permissão de uso em quaisquer projetos como **candidatos**, não datasets já preparados.
- [x] Retirar BiVib/RWC/MAPS/MAESTRO NC do pipeline comercial autorizado, mantendo-os apenas como literatura científica consultável sem uso dos áudios, salvo licença comercial escrita.
- [ ] Revisar licenças por arquivo original, EULA, direitos de terceiros e marcas; preservar manifestos com hashes, versões, autores, condições, aviso de modificação e atribuição.
- [ ] Priorizar obtenção de WAV/FLAC originais dos candidatos e **capturas próprias de piano real com autorização contratual comercial**, inclusive martelo, pontes e antes/depois de feltro quando viável.
- [ ] Solicitar autorizações comerciais separadas a titulares de dados NC apenas se realmente necessários.
- [ ] Decidir a licença de distribuição do **código Stage Synth** e preparar THIRDPARTY/ATTRIBUTIONS antes da venda: não há LICENSE na raiz atualmente.
- [ ] Validar R-GATE-1..7 com foco **comercial**, sem liberar o novo motor enquanto os demais critérios estiverem pendentes.

---

# BLOQUEIO: aguardar referências científicas completas antes de continuar o DSP (22/11/2026)

**Não programar P2, modificar timbre ou promover P1** enquanto o status de prontidão estiver pendente; solicitação expressa do usuário. Registro detalhado: [PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md](PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md).

- [x] Auditar as 18 lacunas anteriores contra **22 referências científicas/datasets/especificações** com fonte, objetivo, direitos, arquivos disponíveis e limitações.
- [x] Verificar tamanho de **BiVib 33,1 GB multipartes**, **RWC 14,2 GB ZIP**, **Plath/Hamburgo 4,6 GB** e **Liang/QMUL pedal 222,7 MB**. Metadados de acesso encontrados, mas nenhum conjunto completo baixado ou validado.
- [x] Localizar Plath/Hamburgo: força tecla–base, aceleração da ponte e pressão binaural; **não confundir keybed force com bridge driving-point force**.
- [x] Localizar métodos de **admitância passiva** (Bank), acoplamento tampo/string (Miranda Valiente 2024), modelagem de colisão com energia estável (Bilbao), parâmetros de instrumentos (Euphonics/Chabassier) e métodos ITU para escuta.
- [x] Confirmar que **RWC/BiVib/MAESTRO contêm condições NC** e requerem revisão do uso pretendido; bitKlavier Model D é CC BY 4.0, mas tem edição e normalização.
- [ ] R-GATE-1 — aquisição/validação local de subconjunto original por instrumento, pitch, velocity e mic com estados conhecidos; 2 instrumentos reais e felt com escopo claro.
- [ ] R-GATE-2 — parâmetros físicos de cordas, martelo e ponte; obter FRF de ponte por região ou uma aproximação passiva quantitativamente justificável.
- [ ] R-GATE-3 — revisar licenças e permissões efetivas do uso pretendido, inclusive dataset Plath e QMUL.
- [ ] R-GATE-4 — manifesto de gravações por arquivo com hashes, limites de edição, pitch gravado, velocity e microfone/sala/pedal.
- [ ] R-GATE-5 — validar estimador com verdade conhecida e metodologia A/B/C de núcleo seco versus som completo sem comparar cadeias diferentes.
- [ ] R-GATE-6 — planejar cada experimento físico de uma nota, 1–3 cordas H/V, ponte/radiação, meio-pedal/CC66/67 com critérios objetivos.
- [ ] R-GATE-7 — definir protocolo auditivo padronizado e critérios de 32–64 vozes, callback/latência, FX e PC/Moto g04s para homologação futura.

**Até liberação:** somente estudo e preparação das referências, sem DSP/P2. Não declarar trabalho concluído só porque links foram encontrados.

---

# Auditoria P0/P1/P2 de modelagem física antes de P2 (22/11/2026)

Documento: [AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md](AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md).

- [x] Inspecionar o DSP real de A/B/C, ponte compartilhada, camada de teclas/pedal, presets, analisador E0 e metas de 32/64 notas.
- [x] Confrontar martelo não linear, two polarizations, double decay, impedância de ponte, som radiado, perda por parcial e modos longitudinais com Bank, Smith, Weinreich e Chabassier.
- [x] Classificar **18 lacunas**, incluindo sete condições P0 para promover nova arquitetura, requisitos P1 (pedal CC64/66/67, escala e afinação, alias) e itens P2 (mecânica e detalhes auxiliares).
- [x] Documentar viés da busca de harmônicos: ±2,5% em torno de n×f_ET falha se B=0,0012 para n=8 (+3,707%), invalidando inferências de B em condições extremas; **os 33 resultados E0 não são ranking de realismo**.
- [ ] **E1.0/P0:** separar benchmark de núcleo seco e saída acústica final; A modal envia saída auxiliar a convolução de cordas/corpo no aplicativo, ausente no E0, e C inclui corpo interno. Controlar FX e os ganhos antes de alegar comparação justa.
- [ ] **E1.1/P0:** validar medidor f1/B/envelopes com sinais sintéticos B=0..0,003, ruído, 2 cordas e parciais transitórios; manter histórico E0 e reprocessar as referências.
- [ ] **E1.2/P0:** obter subconjuntos científicos licenciados BiVib/RWC/bitKlavier com velocity, mic e estados documentados; não copiar samples terceiros para repo ou distribuição.
- [ ] **E1.3/P0:** martelo-corda e uma corda H/V resolvidos offline; medir duração de contato e double decay por parcial.
- [ ] **E1.4/P0:** múltiplas cordas e ponte reduzida passiva; testar energia, batimento e acoplamento em posição de excitação variável.
- [ ] **E1.5/P1:** radiação por região, filtro antialias de corpo 4:1 e testes isolados de alias; separar som de tampo de reverb da sala.
- [ ] **E2:** comparar A/B/C/P1/P2 em condição nivelada, com diferentes dinâmicas e registros, registrar hipóteses fracassadas.
- [ ] **E3:** PC/Chrome/Moto g04s, 32–64 vozes, MIDI/pedal/FX e xrun, latência, p95/p99 dos callbacks; **não homologar sem hardware**.

**Decisão:** protótipos de pesquisa isolados são permitidos, **não integrar P1/P2 à main** até evidência física/perceptual e performance. Nenhum DSP, UI, MIDI, FX ou preset alterado nesta rodada.

---

## Atualização: Steinway Model D aberto e CFX comercial (22/11/2026)

- [x] **bitKlavier Grand**, produzido em Princeton: piano acústico Steinway Model D real, **16 camadas**, **9 pares de microfones**, WAV até 96k/24bit, **CC BY 4.0**, com arquivos separados de pedal, martelo e ressonância. **Processados e nivelados na pós-produção** — usar para timbre American, release e radiador, não curva física de hammer velocity.
- [x] **Vienna Synchron Yamaha CFX**: piano CFX real capturado por sistema robótico com sensores de tecla, pedal e martelo, porém **amostras comerciais/processadas**; referência para escuta comparativa **sem extrair/republicar áudio**. Yamaha C5 e Disklavier DC3 M4 **não** são CFX.
- [x] **CCMusic Piano Sound Quality Dataset**: 1.320 gravações individuais de 7 grupos de pianos Kawai, Steinway, Young Chang, Hsinghai e Pearl River e avaliações humanas; possível controle externo de tipos acústicos, mas não física de martelo calibrada.
- [ ] Antes de priorizar o American Stage, obter subconjunto **Steinway D bitKlavier original WAV** com documentação do microfone, analisar tratamento da camada e escolher registros gravados fisicamente (a cada terça menor). Não afirmar que toda tecla possui gravação própria.
- [ ] Continuar sem alegar referência científica calibrada **felt vs no-felt no mesmo instrumento**; solicitar/gravar par controlado se esse efeito precisar ser identificado.

Detalhes: [AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md](AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md).

---

# Auditoria de referências científicas de piano acústico (22/11/2026)

**Documento técnico atualizado:** [AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md](AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md).

- [x] Identificar **BiVib** (88 notas × 10 velocities em dois Disklavier reais, cauda/vertical, 96 kHz/24 bit PCM, binaural e vibrações calibráveis): melhor referência pública verificada para dinâmica e radiação; dataset ~33 GB, licença CC BY-NC-SA.
- [x] Identificar **RWC** (Yamaha, Steinway, Bösendorfer reais; 3 × 88 × 4 articulações × 3 dinâmicas = 3.168 sons; WAV mono); reedição 2026 CC BY-NC 4.0: melhor comparação independente de fabricantes e releases.
- [x] Verificar **MAPS**: usar **somente** ENSTDkCl/ENSTDkAm como piano Yamaha Disklavier real, close/ambient. Outros sete grupos são instrumentos **virtuais**, não pianos reais.
- [x] Verificar MAESTRO v3 (MIDI velocities/pedal com alinhamento ~3 ms, performance musical, não notas secas) e KRAISLER 2026 (piano separado dry/studio/hall e MIDI, **licença descrita com restrições potencialmente conflitantes**).
- [x] Revisar qualidade das 33 amostras E0: os espectros obtidos **não comprovam realismo, nem uma vantagem perceptual objetiva do A sobre B/C**; velocity, microfones, ambiente e formatos não foram alinhados.
- [ ] **E1:** obter subconjunto BiVib autorizado, verificar documentação de origem, número MIDI, velocity, estado da tampa, hashes, amplitude e captação. Planejar armazenamento antes de adquirir ~33 GB.
- [ ] **E1:** obter segmento de **piano Steinway RWC** para comparação por nota e articulação; respeitar CC BY-NC (nenhuma distribuição comercial de samples).
- [ ] **E1:** implementar rastreamento de parciais por múltiplas janelas e estimativas de incerteza; emparelhar velocidades e microfones antes de comparar motores.
- [ ] **E2:** derivar martelo/corpo de medidas isoladas, testar B/decay/duas fases e ouvir motores em níveis compatíveis, mantendo 32–64 vozes/CC64/FX e PC/Moto g04s para validação.
- Nenhuma amostra adicional de terceiro foi baixada nesta auditoria; nenhum DSP, UI, MIDI, FX ou preset alterado.

---

# E0 — aquisição e medição de quatro famílias de pianos (22/11/2026)

- [x] Consultar as licenças e obter 33 gravações individuais: Steinway Model B / Iowa (9 AIFF), Yamaha C5 Salamander (9 AAC), Felt Fuchs & Möhr / Tom Guder (9 WAV) e Knight Upright VCSL (6 AAC).
- [x] Validar a nota e a camada pelo SFZ no Felt, registrar SHA-256, codec, tamanho, captação e fonte.
- [x] Converter arquivos **exclusivamente em disco temporário de CI**, medir ataque/FFT/partials/B com limiar de parciais fortes, comparar com A/B/C e eliminar arquivos externos após gerar artifact JSON.
- [x] Detectar que B/C divergem na distribuição relativa dos harmônicos especialmente nos graves e que o A é mais próximo em várias observações; **não** interpretar como certificação auditiva.
- [x] Tratar C6 e pp com menos de três parciais como inconclusivos; instrumentar FFT curta de ataque separada de B para avaliar agudos rapidamente amortecidos.
- [ ] E1: rastrear parciais em múltiplas janelas, buscar contato físico do martelo e amortecimento individual, avaliar batimentos/direcionalidade e descontar ambiente/edição.
- [ ] Conferir fontes **originais sem perda** Yamaha e Upright para medir física (AAC é só triagem); obter referência isolada CFX antes de alegar fidelidade ao CFX.
- [ ] Validar experimentalmente microfones, intensidade real e pedais; escuta com nivelamento de loudness.
- [ ] Validar 32/64 notas, CC64 e ausência de estalos em PC/Chrome e Moto g04s. **Preservar a v1.9.5.**

Detalhes: [ANALISE_AUDIO_REAL_E0.md](ANALISE_AUDIO_REAL_E0.md). Só pesquisa: **sem alteração em motor, UI, MIDI, FX ou presets**.

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

# Estudo aprofundado de modelagem física — pesquisa, sem DSP (22/11/2026)

Documento: [FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md](FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md).

- [x] Revisar literatura fundamental sobre colisão do martelo, rigidez/damping da corda, duas polarizações, acoplamento de uníssono, prompt/aftersound, ponte, tampo, abafadores, ressonância simpática e radiação acústica.
- [x] Analisar arquitetura modal de Bank (2010), simulação acoplada de Chabassier (2014) e documentação do Unsampled Piano (2026); diferenciar código aberto GPL de informações públicas comerciais.
- [x] Auditar lacunas existentes nos motores A/B/C; confirmar que o P1 em PR #2 permanece fora de main.
- [ ] **E0:** obter referência seca autorizada por nota, velocidade e estado dos pedais; as capturas atuais com FX não são suficientes para identificar constantes físicas.
- [ ] **E1:** medir por nota B, cents, amplitudes e decaimentos por parcial com método mais robusto que uma FFT fixa.
- [ ] **E2:** prototipar contato martelo-corda com solução offline e famílias **sintéticas** de força por velocity, medindo custo e dinâmica.
- [ ] **E3:** testar 1–3 cordas, duas polarizações e ponte compartilhada em pequena prova física, com diagnóstico de energia/passividade e double-decay.
- [ ] **E4:** comparar tampo/radiação por regiões e localização de microfones, separando corpo e reverb de sala; validar controles CC64/release.
- [ ] **E5:** comparar arquiteturas modal, waveguide e híbrida em áudio nivelado, sem promover motor por um único scorecard.
- [ ] **E6:** homologar 32/64 notas em Chrome real, PC e Moto g04s, com efeitos, MIDI, pedal, picos e estabilidade.
- Nenhum novo link, módulo, motor ou preset foi integrado ao aplicativo. Nesta etapa, **apenas pesquisa e documentação**.

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

# P0 em implementação isolada — baseline acústica (22/11/2026)

- [x] Criar branch separada sem modificar os DSPs estáveis.
- [x] Adicionar medidas FFT de cents, B estimado, parciais, ataque, decaimento, clipping e amostras não finitas; 5 testes unitários locais passaram.
- [x] Preparar comparação reproduzível de 108 casos A/B/C × 4 pianos × C2/C4/C6 × velocity 32/80/120.
- [x] Conferir workflow de regressões: 90/90 testes; 108/108 renders concluídos; 0 clipping/NaN no sinal seco, artifact preservado.
- [ ] Examinar números do JSON por registro e dinâmica; B é estimativa e não alvo universal.
- [ ] P1: corrigir dispersão/perdas por frequência **somente num experimento isolado**, reexecutar regressões e comparação sonora nivelada.
- [ ] Testes em Chrome real, PC e Moto g04s, com 32/64 vozes, MIDI/CC64 e FX; não anunciar homologação antes.

Documentação: docs/BASELINE_ACUSTICA_V124.md. Não há alteração de motor/presets no aplicativo.

---

# Pesquisa externa concluída — 22/11/2026

- [x] Referências científicas/comerciais/código aberto reunidas e mapeadas para os motores **A (modal), B (físico v1.9.5) e C (mecânico)**.
- [x] Documento: [`REFERENCIAS_EXTERNAS_FIDELIDADE_MOTORES_2026-11-22.md`](REFERENCIAS_EXTERNAS_FIDELIDADE_MOTORES_2026-11-22.md).
- [ ] **Próxima implementação P0:** suíte acústica de múltiplas notas/velocities com B, cents, dois tempos de decaimento, ganho por parcial, brilho por força e teste de clipping.
- [ ] **P1 B/C:** corrigir inarmonicidade insuficiente com dispersão allpass calibrada e filtro de perda por frequência; não compensar H2 apenas com ganho artificial.
- [ ] **P2 A:** ampliar capacidade modal 32→64 vozes somente se os testes de realismo/desempenho justificarem.
- [ ] **P3–P4:** modelo de ataque comutado + tampo/pedal compartilhados; validar benefícios audíveis e custo de CPU.
- [ ] Não promover novo DSP antes de comparação A/B nivelada e teste real no PC/Moto g04s. A v1.9.5 continua disponível para regressão.
- **Nesta entrega foi feita apenas pesquisa/documentação; nenhum DSP, seletor ou preset foi alterado.**

---

# Atualização da comparação v1.12.4 (22/11/2026)

- [x] A modal, B Stage físico histórico v1.9.5 e C Stage mecânico selecionáveis no mesmo módulo Piano Acústico.
- [x] B usa arquivo DSP independente recuperado, sem duplicar o motor C.
- [x] Manter preferência salva e disponibilizar alternativa clássica.
- [x] 84 testes automatizados e regressão de interface PC/celular simulados.
- [ ] Recuperar **código exato do Novo Stage v1.11.0**, original de outra conversa; não confundir com v1.9.5.
- [ ] Testar AudioWorklets reais, troca de motores e MIDI em Chrome do usuário, com FX e sustain.
- [ ] Calibrar inarmonicidade, contato do martelo e ressonância com notas isoladas; não promover apenas por scorecard.
- [ ] Medir 32 notas no Moto g04s e 64 no PC, sem estalos.

---

# Atualização de execução — v1.12.3 integrada (22/11/2026)

- [x] Integração do motor B físico + acoplamento mecânico ao app principal, selecionável no módulo Piano Acústico.
- [x] Comparação A (modal derivado da linha Claude) / B (Novo Stage mecânico) no mesmo editor.
- [x] Retirados novos banners e links externos; sem módulos adicionais.
- [x] Testes automatizados (79) e testes do seletor em navegador simulado.
- [ ] Testar **AudioWorklet real**, estabilidade e latência no PC e no Moto g04s; não confundir simulação com homologação.
- [ ] Recuperar e comparar código original da linha Novo Stage v1.11.0, que não foi usado nesta implementação.
- [ ] Corrigir inarmonicidade, decaimento espectral e realismo do timbre, mantendo estabilidade comprovada da v1.9.5.

---

# Stage Synth — prioridades e próximos passos

**Atualizado em:** 22/11/2026. Este arquivo é um plano, não confirma implementação.

## Prioridade 0 — Preparar integração correta entre conversas e código

- [x] Adotar GitHub como referência central.
- [x] Criar `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md` e este plano.
- [ ] Identificar onde está o **código completo da linha "Novo Stage v1.11.0"**, caso exista fora do repositório. Não assumir que o protótipo pode ser integrado diretamente na raiz v1.8.4.
- [ ] Verificar diferenças entre linhas `main`, `physical-v1.9.5`, `physical-v1.9.6` e a fonte verdadeira do Novo Stage; escolher e documentar uma **base concreta** para a próxima implementação.
- [ ] Criar rotina de atualização dos quatro documentos após cada commit relevante, com verificação de HEAD e testes.

## Prioridade 1 — Estabelecer baseline que não volte a estalar

- [ ] Rodar testes de lógica e navegador da v1.9.5; guardar configuração de áudio e referência de desempenho.
- [ ] Medir áudio real no PC e no Moto g04s, incluindo 32 e 64 vozes, sustain, reverb e camadas; registrar o limite observado.
- [ ] Identificar eventuais diferenças de latência entre navegador, motor e configurações.
- [ ] Preservar revert/backups ao introduzir mudanças.

## Prioridade 2 — Recuperar fidelidade acústica

- [ ] Integrar seletivamente o acoplamento mecânico de v1.12.1 na **base escolhida**, após revisar a estabilidade numérica e a API de voz existente.
- [ ] Evitar adicionar o novo tampo como reverb paralelo sobre outra simulação de tampo; medir ganho, caudas e feedback por nota.
- [ ] Implementar rigidez/dispersão adequada e inarmonicidade B em vários registros; comparar com auditoria de v1.9.6.
- [ ] Fazer ataque de martelo responsivo a velocity e amortecimento espectral independente por parcial.
- [ ] Modelar 1–3 cordas acopladas por tecla conforme registro e orçamento de CPU, com ressonância simpática condicionada a abafadores/sustain.
- [ ] Calibrar Japanese, American, Felt e Upright separadamente. As quatro referências atuais incluem efeitos originais: não usar caudas reverberantes como constantes de corda.
- [ ] Fazer comparação A/B nivelada e auditiva; se o modelo soar como violão, sino ou órgão, não promover para a versão estável.

## Prioridade 3 — Testes mensuráveis antes de nova versão

- [ ] Reusar ou aperfeiçoar `timbre_scorecard.py` e `piano_partials.py` da auditoria Claude disponível no projeto; validar inarmonicidade, brilho por velocity e decaimento por parcial.
- [ ] Cobrir graves/médios/agudos e toque suave/médio/forte com notas isoladas **quando existirem referências secas confiáveis**; as capturas de apresentação não são equivalentes.
- [ ] Medir RMS, picos, clipping, notas presas, mensagens MIDI (incluindo CC64), CPU por bloco e estouros de prazo de áudio.
- [ ] Passar pelos testes existentes e testar em PC/Moto g04s real.
- [ ] Publicar versão experimental isolada para avaliação, com URL/commit verificados; promover apenas se estabilidade e timbre forem melhores.

## Trabalho posterior (não prioritário até estabilizar piano)

- [ ] Recalibrar Rhodes MK I/II, Wurly 140B/200A, Clavinet, CP70 e E. Piano 1/2/3 com as nove capturas.
- [ ] Confirmar migração da nomenclatura dos elétricos em qualquer eventual atualização do app principal.
- [ ] Instrumentação de desempenho visível ao usuário (redução de ganho, carga de áudio/voz), desde que não piore a CPU.

## Como fechar uma etapa

Registrar em `docs/ESTADO_ATUAL.md`: **commit, pasta, mudança real, testes executados, resultado em hardware, risco restante e local de publicação**. Se faltar uma evidência, declarar pendência, não marcar como concluída.

## Próxima ação técnica recomendada

**Localizar a fonte exata do Novo Stage e comparar sua arquitetura com o protótipo mecânico v1.12.1 antes de fazer merge**, mantendo a v1.9.5 como regressão de estabilidade. Se a fonte não estiver disponível, estudar/adaptar a integração em uma nova pasta experimental baseada em código realmente acessível, sem chamá-la de integração ao Novo Stage.

## Execução em 22/11/2026 — acoplamento em base acessível

- [x] Criar experimento **v1.12.2** baseado na v1.9.5 com ponte, tampo e cordas simpáticas processados no mesmo AudioWorklet, com realimentação limitada e bypass A/B.
- [x] Integrar CC64, estados de amortecedores e testes de notas repetidas; rodar 76 testes e benchmark offline com 32/64 vozes.
- [ ] Validar Audioworklet real no navegador do usuário e ouvir A/B em PC e Moto g04s; confirmar que não surgiram novos estalos.
- [ ] **Recuperar a fonte exata do Novo Stage v1.11.0** para portar a integração sem quebrar seu comparador Claude/Stage.
- [ ] Corrigir inarmonicidade e decaimento dependente da frequência; pontuação do scorecard anterior não demonstra realismo.
- [ ] Calibrar auditivamente com notas secas e os quatro WAVs disponíveis como referência final (efeitos originais inclusos).
