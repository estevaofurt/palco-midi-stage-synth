# PIANO V4 — BIBLIOGRAFIA ANOTADA PARA AS 18 LACUNAS (K01–K18)

**Data:** 23/11/2026 · **Objetivo:** localizar fontes de várias disciplinas para **todas** as lacunas da auditoria da V4, sem reproduzir samples no motor. **PR:** #39 (draft) · **Main:** Stage Synth v1.12.8 preservada.

## Método e confiabilidade

- A seleção abaixo foi feita por pesquisas direcionadas e conferência de **páginas de resumos/indexadores ou documentação pública de fabricantes e instituições**, verificando títulos, autores quando disponíveis, escopo e tipo de medida. **Não afirmar que todos os textos completos foram estudados integralmente**; parte dos papers é paga, livros precisam de aquisição e certos PDFs são apenas material de consulta futura.
- Artigo experimental de um piano **não representa todos** os pianos; instruções de fabricante descrevem aquele fabricante; patente histórica é evidência de projeto, não de vantagem acústica demonstrada.
- Cada lacuna contém **fontes primárias ou técnicas**, a contribuição que pode oferecer, seu limite e um **experimento que falta**. Classificações P0/P1/P2 são do projeto, não conclusões dos autores.
- **Tipos:** EXP = experimental revisado por pares; MOD = modelagem acadêmica com comparação ou medição; FAB = fabricante; TEC = técnico/profissional; DATA = conjunto de dados; PSI = percepção; STD = norma API/documentação; HIST = arquivo histórico/organologia.
- Gravações externas: **somente análise/validação e escuta sob direitos autorizados**, nunca WAV/SF2/ataques/IR gravados como excitadores ou som do motor. **Não foi baixado nenhum áudio de terceiros nesta auditoria.**
- "Referência encontrada" NÃO significa "parâmetro da nossa V4 identificado". O estado de cada K01–K18 continua **aberto** até ensaio e aceitação do piano-alvo.

## P0 — nove lacunas que bloqueiam uma nota C4 convincente

### K01 — Qual instrumento específico é nosso alvo e quais condições de referência?
1. **Niko Plath, _Influence of Playing on the Tonal Characteristics of a Concert Piano — Dataset_** (Zenodo, 2019) — **DATA**, https://zenodo.org/records/3271370. Fornece força do impacto **tecla–keybed**, aceleração na região da **ponte**, pressão sonora nos dois canais de cabeça artificial, com tempo sincronizado a 50kHz. **Não** é força martelo–corda, nem caracteriza todas as dimensões do piano.
2. **Papetti, Avanzini & Fontana, _BiVib Audio-Tactile Piano Sample Library_** (Zenodo, 2019) — **DATA**, https://zenodo.org/records/2573232. Dois Yamaha Disklavier (cauda e vertical), áudio binaural + vibração do **teclado**, 10 camadas de MIDI velocity. **Não** trata vibração do teclado como vibração do tampo; conteúdo de gravação NÃO será usado no motor.
3. **University of Iowa — _Musical Instrument Samples: Piano_** — **DATA**, https://theremin.music.uiowa.edu/MISpiano.html; origem institucional https://theremin.music.uiowa.edu/mis.html. Gravações de Steinway B e dinâmicas conhecidas; ressalva: piano gravado **fora** de câmara anecoica, mics/sala influenciam.
4. **Yamaha — _How a Piano is Made / Making the Body_** — **FAB**, https://br.yamaha.com/pt/musical-instruments/pianos/explore/musical-instrument-guide/piano/manufacturing/. Sequência do projeto e montagem da ação/tampo, não dados geométricos de escala de um piano específico.
**Falta medir/documentar:** fabricante/modelo/estado, piano de cauda ou vertical, condições de sala/mic, pitch e uníssono, geometria C4, licenças e repetibilidade. Nenhum dos WAV privados "American/Japanese/Felt/Upright" deve ganhar metadados presumidos.

### K02 — Relação da execução com velocidade de martelo e cronologia da ação
1. **Goebl, Bresin & Galembo, _Touch and temporal behavior of grand piano actions_**, JASA 2005 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/16158669/. Teclas/martelos captados por acelerômetros, áudio por microfone; tempos de trânsito e tipos de toque comparados.
2. **Askenfelt & Jansson, _From touch to string vibrations. II: The motion of the key and hammer_**, JASA 1991 — **EXP**, https://cir.nii.ac.jp/crid/1362825893849331584. Aceleração/escapamento/trajetória do martelo após soltura.
3. **Askenfelt & Jansson, _Piano touch, hammer action, and string motion_** — **EXP**, https://doi.org/10.1121/1.2019638. Medições simultâneas de velocidade de tecla, aceleração do martelo e velocidade de corda; não representar velocity MIDI como m/s universal.
4. **Yamaha, _Making the Keyboard and Action_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing002.html. Materiais/montagem do mecanismo, não curva MIDI para nosso instrumento.
**Falta:** curva MIDI/key displacement→velocidade de martelo, massa efetiva, estágio de escape, regulagem da ação e dispersão pp/mf/ff do C4 do instrumento-alvo.

### K03 — Viscoelasticidade/histerese do feltro, contato real e flexão da haste
1. **Giordano & Winans, _Piano hammers and their force compression characteristics: does a power law make sense?_**, JASA 2000 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/10790050/. Testes de força/deformação e flexão da haste; confrontar o único expoente do V4 com dados reais.
2. **Anatoli Stulov, _Hysteretic model of the grand piano hammer felt_**, JASA 1995 — **MOD/EXP**, https://www.etis.ee/portal/publications/display/9008dc53-ab9b-41ce-ad41-34bc84501d16. Histerese dependente do histórico, não um simples potencial elástico conservativo.
3. **Stulov, _Dynamic behavior and mechanical features of wool felt_**, Acta Mechanica 2004 — **EXP/MOD**, artigo DOI 10.1007/s00707-004-0104-3, documento institucional https://www.ioc.ee/~stulov/Acta2004.pdf. Estuda característica dinâmica/histerese e materiais; não transferir valores de outro feltro.
4. **_Experimental investigation of the piano hammer-string interaction_**, JASA 2013 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/23556611/. Métodos para força e deformação em contato com **cordas reais**; problemas de sincronização e derivação dos sensores.
5. **_Dynamic compression characteristics of piano hammer felt_**, J-STAGE 1984 — **EXP**, https://www.jstage.jst.go.jp/article/jasj/40/11/40_KJ00001453633/_article/-char/en. Força no tempo e deslocamentos da corda e do núcleo da cabeça.
**Falta:** força–tempo–deformação C4, dissipação por ciclo, haste e massa efetiva medidas em martelo e cordas específicos, teste de previsão fora da amostra.

### K04 — Geometria, rigidez, dispersão, perdas e posição do golpe
1. **_Inharmonicity of Plain Wire Piano Strings_**, JASA 1952 — **EXP**, https://pubs.aip.org/asa/jasa/article-abstract/24/3/267/660100/Inharmonicity-of-Plain-Wire-Piano-Strings. Inarmonicidade **medida** em diferentes pianos, não valor fixo universal.
2. **Askenfelt & Jansson, _From touch to string vibrations. III: String motion and spectra_**, JASA 1993 — **EXP**, https://cir.nii.ac.jp/crid/1362262945887736832. Movimento, espectro, múltiplos contatos no grave; análise do impacto e do movimento efetivo das cordas.
3. **Harold Conklin, _Piano design factors: Where should the hammer strike?_**, KTH Five Lectures — **ENG/FAB**, https://www.speech.kth.se/music/5_lectures/conklin/whereshould.html. Posição relativa do golpe varia por registro, afeta parciais e depende do martelo; não aplicar 1/8 a 88 teclas.
4. **Yamaha, _Stringing and Mounting the Keyboard and Action_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing003.html. Construção/encordoamento e escala em vez de uma única corda ideal em todo teclado.
**Falta:** L, diâmetro, enrolamento, material, tensão, B, posição de impacto, decaimentos por parcial e geometria de terminação do C4 real.

### K05 — Mobilidade/impedância complexa da ponte e apoio da corda
1. **P. Miranda Valiente, G. Squicciarini & D. J. Thompson, _Influence of soundboard modelling approaches on piano string vibration_**, JASA 2024 — **MOD**, https://pubmed.ncbi.nlm.nih.gov/38742965/. Compara apoios/flexibilidade de placa e mede consequências na força e no decaimento; inclui duplex.
2. **Corradi et al., _Modal analysis of a grand piano soundboard at successive manufacturing stages_**, Applied Acoustics 2017 — **EXP/MOD**, https://www.sciencedirect.com/science/article/pii/S0003682X17303444; versão de repositório https://re.public.polimi.it/handle/11311/1022091. Fazioli F278, placa antes/depois de pontes e montagem, análise de mobilidade no ponto da ponte; não parâmetro pronto para nosso C4.
3. **KTH, Harold Conklin, _How does a soundboard work?_** — **ENG**, https://www.speech.kth.se/music/5_lectures/conklin/howdoes.html. Mobilidade medida em condições de montagem diferentes.
4. **_Roving Wire-Breaking Technique_** (Applied Acoustics 2018) — **MÉTODO**, https://www.sciencedirect.com/science/article/abs/pii/S0003682X17309908. Procedimento de mobilidade em cordofones **não específico de piano**: útil conceitualmente, não dados prontos para ponte.
**Falta:** mobilidade medida Y(f)=V/F complexa, direcional e com fase no ponto da ponte C4, mais incerteza e resposta em várias dinâmicas/posições.

### K06 — Estrutura e vibração distribuída do tampo
1. **Ege, Boutillon & Rébillat, _Vibroacoustics of the piano soundboard: (Non)linearity and modal properties in the low- and mid-frequency ranges_**, JSV 2013 — **EXP/MOD**, https://www.sciencedirect.com/science/article/pii/S0022460X12007936. Regimes modais e confinamento entre nervuras; transição depende de desenho.
2. **_Dynamical properties of piano soundboards_**, JASA 2013 — **EXP/MOD**, https://pubmed.ncbi.nlm.nih.gov/23556610/. Estruturas com nervuras e irregularidades, vibração localizada, medidas em tampo vertical; não extrapolar sem ensaio.
3. **_A modal approach to piano soundboard vibroacoustic behavior_**, JASA 2017 — **MOD**, https://pubmed.ncbi.nlm.nih.gov/28253680/. Formulação de placa **ortotrópica com nervuras**, modos na faixa 0–3kHz.
4. **_Modal analysis of a grand piano soundboard at successive manufacturing stages_**, Applied Acoustics 2017 — **EXP**, https://www.sciencedirect.com/science/article/pii/S0003682X17303444. Papel do aro/estrutura/montagem na mobilidade.
5. **Yamaha, _How a Piano is Made: Making the Body_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/; documenta abeto, nervuras, curvatura e pontes.
**Falta:** desenho de nervuras, crown, espessura, fibras, contorno, perdas e mapa modal/radiativo do tampo do piano-alvo, não uma placa de seno abstrata.

### K07 — Transferência tampo→pressão sonora, diretividade, tampa e microfone
1. **_Radiation Characteristics of Grand Piano Soundboards in Different Stages of Production_**, ISMA 2017 — **EXP**, https://isma2017.cirmmt.mcgill.ca/proceedings/pdf/ISMA_2017_paper_16.pdf. Mede resposta e diretividade em estados de produção, microfones em arranjo espacial; não modelo universal.
2. **_Sound Radiation from a Grand Piano_**, AES (1990s) — **EXP**, https://aes.org/publications/elibrary/elibrary-page/?id=7613. Distingue parciais e excitação de modos estruturais como componentes do som radiado.
3. **Ege & Boutillon, _Vibroacoustics ... reduced models, mobility synthesis, and acoustical radiation regime_**, JSV 2013 — **MOD/EXP**, https://www.sciencedirect.com/science/article/pii/S0022460X13002472. Condições para radiação/modalidade.
4. **_Operational transfer path analysis of a piano_**, TU Eindhoven 2018 — **EXP**, https://research.tue.nl/en/publications/operational-transfer-path-analysis-of-a-piano/. Bösendorfer 280VC-9: estuda tampo, tampa e outras superfícies; na faixa alta analisada **tampa pode dominar nesse piano**.
**Falta:** posições de mic e ouvinte fixadas, transferência de velocidade/força da placa até pressão em Pa, diretividade e separação de sala/corpo.

### K08 — Diagnóstico de onde se perde a "percussão" do martelo
1. **Plath, _Influence of Playing ... Concert Piano — Dataset_** — **DATA**, https://zenodo.org/records/3271370. Alinhamento temporal de **força tecla–fundo**, **aceleração junto à ponte** e **Pa binaural**, a 50kHz; não confundir o impacto no fundo da tecla com o choque feltro–corda.
2. **_Experimental investigation of the piano hammer-string interaction_**, JASA 2013 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/23556611/. Medição local do evento martelo/corda, força/compressão e cuidado de sincronização.
3. **_Radiation Characteristics ... Stages of Production_**, ISMA 2017 — **EXP**, https://isma2017.cirmmt.mcgill.ca/proceedings/pdf/ISMA_2017_paper_16.pdf. Complementa com transmissão estrutural/acústica em estágios.
**Falta:** registrar simultaneamente **força martelo–corda**, velocidade no ponto de impacto, mobilidade da ponte, campo de velocidade de tampo e pressão no ar para a mesma nota C4. O Plath NÃO mede diretamente a primeira força — combinação entre estudos não equivale a uma medição conjunta.

### K09 — Teste perceptual que não confunde pitch/loudness/duração com fidelidade
1. **_Preparation of stimuli for timbre perception studies_**, JASA 2013 — **PSI**, https://pubmed.ncbi.nlm.nih.gov/23967955/. Adverte que variação de loudness, pitch, duração e covariação entre propriedades interferem na comparação.
2. **_Motor origins of timbre in piano performance_**, PNAS 2025 — **PSI/EXP**, https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/. Movimentos/gestos, pistas auditivas e atributos percebidos, testes com pianistas e não treinados; não significa que todo ruído será positivo.
3. **_Influence of pitch, loudness, and timbre on the perception of instrument dynamics_**, JASA 2011 — **PSI**, https://pubmed.ncbi.nlm.nih.gov/21974491/. Variação de pitch/loudness altera percepção do gesto e não pode ser ignorada.
4. **Iowa MIS piano** — **DATA**, https://theremin.music.uiowa.edu/MISpiano.html. Comparação externa de notas pp/mf/ff com cadeia de gravação descrita, mas não uma medição neutra sem ambiente.
**Falta:** protocolo A/B/X com controle de nível, referência única, julgamento cego, C4 em três dinâmicas com escuta e relatório de erro/semelhança; subjetividade do titular é gate de produto.

## P1/P2 — sete lacunas de caráter de piano completo (K10–K15 P1 ou P1/P2, K16 P2)

### K10 — 2/3 cordas por nota, batimentos, aftersound e polarizações
1. **Gabriel Weinreich, _Coupled piano strings_**, JASA 1977 — **EXP/MOD**, https://cir.nii.ac.jp/crid/1361699993945382016. Relação entre admitância da ponte, estado de afinação, batimentos, aftersound e duas polarizações.
2. **Weinreich, _The coupled motion of piano strings_**, KTH lectures — **MEC/EDU**, https://www.speech.kth.se/music/5_lectures/weinreic/strings.html. Explica modo simétrico/antissimétrico e dissipação diferente; notas reais não são WAVs superpostos de sistemas isolados.
3. **_A necessary condition for double decay in piano strings_**, JASA, referência https://euphonics.org/wp-content/uploads/2022/03/Double_decays_JASA.pdf — **MOD**; confirmar edição/DOI e condições lendo estudo antes de usar números.
**Falta:** mapas de acoplamento e formas modais/uníssono, afinamento entre cordas, polarizações/forças na ponte e regimes de dupla cauda por dinâmica/registro.

### K11 — Ruídos da ação/teclado, batidas auxiliares e sensação de martelo
1. **_Motor origins of timbre in piano performance_**, PNAS 2025 — **PSI/EXP**, https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/. Percepção de peso, brilho e clareza com pistas auditivas do movimento do toque.
2. **Plath Concert Piano Dataset** — **DATA**, https://zenodo.org/records/3271370. Força de impacto da **tecla no fundo** pode servir para cronometrar ação, não é som direto de martelo/corda.
3. **Piano Technicians Guild — _Piano Servicing and Voicing_** — **TEC**, https://www.ptg.org/piano/care/servicing. Preparação/ruído de peças/voicing e regulagem, sem audioteca de clicks isolados.
4. **Piano Technicians Guild / Museum of Making Music, _Unseen Artists_** — **TEC**, https://www.museumofmakingmusic.org/exhibits/past/ptg. Documenta importância de ajustes, inclusive encontro do martelo com todas as cordas.
**Falta:** mic/câmera/sensores nos pontos corretos para separar ruídos de fundo de tecla, escapamento, martelo retornando e abafador; proibir gerador genérico de click ou ruído aleatório sem origem física.

### K12 — Regulagem, alinhamento, estado técnico, harmonização, tuning stretch
1. **Piano Technicians Guild — _Piano Care / Servicing_** — **TEC**, https://www.ptg.org/piano/care/servicing. Distingue afinação, regulagem da ação, ação de abafadores e voicing por agulhamento/forma/endurecimento/amaciante.
2. **PTG — _Piano Care FAQs_** — **TEC**, https://www.ptg.org/ptgmain/piano/care/care-faqs. Estado técnico, repetição e variações por ambiente.
3. **Yamaha — _Making Keyboard and Action_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing002.html. Processo industrial de conformação/montagem de teclas e martelos.
4. **KTH Conklin — _The hammers_** — **ENG**, https://www.speech.kth.se/music/5_lectures/conklin/thehammers.html. Relação entre posição, massa, rigidez e impacto simultâneo em uníssonos.
5. **_Piano action regulation_**, manual técnico Steinway via capítulo de serviço histórico — **TEC**, https://www.indyptg.org/PTG/SteinwayServiceManuals/Chp1.pdf. **Requer leitura integral e conferência de edição/modelo antes de usá-lo operacionalmente.**
**Falta:** estado de regulagem/mating, trilhas de martelo, key dip, let-off, pedais e curva real de stretch tuning do piano-alvo. Não operar ação real sem técnico habilitado.

### K13 — Sustain, amortecedores, una corda e ressonância simpática
1. **Lehtonen, Penttinen, Rauhala & Välimäki, _Analysis and modeling of piano sustain-pedal effects_**, JASA 2007 — **EXP/MOD**, https://pubmed.ncbi.nlm.nih.gov/17927438/. Efeito do pedal sobre decaimento parcial e ressonância, com dependência de registro; não é simplesmente manter tecla ligada.
2. **Miranda Valiente et al., _Modelling the una-corda effect in pianos_** (2024) — **MOD**, https://eprints.soton.ac.uk/499445/. Modelo tridimensional de cordas e tampo e ação de una corda; não generalizar automaticamente para verticais.
3. **Yamaha — _Mechanism and Pedals_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/. Comparação de funções de pedais e abafadores.
**Falta:** tempos de liberação, zonas mortas e contato dos dampers, meio-pedal, CC64, sostenuto e una corda por instrumento/região.

### K14 — Trechos secundários (duplex scaling), comprimento não vibrante e terminação
1. **Miranda Valiente, Squicciarini & Thompson, _Influence of soundboard modelling approaches on piano string vibration_**, JASA 2024 — **MOD**, https://pubmed.ncbi.nlm.nih.gov/38742965/. Inclui explicitamente trecho duplex na dinâmica da corda e efeitos da terminação.
2. **Smithsonian Institution — _Steinway Patents that Deal with Scales_** — **HIST**, https://americanhistory.si.edu/steinwaydiary/annotations/?id=2043&print=1. Antecedentes de projeto/terminação, **não prova de ganho sonoro**.
3. **Theodor Steinway, _Improvement in Duplex Agraffe Scales for Piano-Fortes_**, patente US126848A (1872) — **HIST**, https://patents.google.com/patent/US126848A/en. Geometria histórica e propósito de projeto, não valores de vibração modernos.
4. **Smithsonian Institution — _Scale of a Piano_** — **HIST**, https://americanhistory.si.edu/steinwaydiary/annotations/?id=2042. Define escala como geometria de cordas, suportes e ponto de golpe.
**Falta:** verificar se o piano-alvo possui segmentos efetivamente livres/dampados e se participam energeticamente; medir com e sem amortecimento sem danos (técnico).

### K15 — Vibrações longitudinais, phantom partials e componentes não harmônicos
1. **Bank & Sujbert, _Generation of longitudinal vibrations in piano strings: from physics to sound synthesis_**, JASA 2005 — **EXP/MOD**, https://pubmed.ncbi.nlm.nih.gov/15898667/. Acoplamento transversal→longitudinal explica parte dos phantom partials.
2. **Etchenique, Collin & Moore, _Coupling of transverse and longitudinal waves in piano strings_**, JASA 2015 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/25920829/. Investiga dependência quadrática em experimento controlado.
3. **_The production of phantom partials due to nonlinearities in the structural components of the piano_**, JASA 2017 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/29092614/. Mostra que a **estrutura de madeira pode gerar componentes mesmo com cordas abafadas** — logo, fenômeno NÃO exclusivamente longitudinal da corda.
4. **_Structural contributions to phantom partial generation in the piano_**, JASA 2018 — **EXP**, https://pubmed.ncbi.nlm.nih.gov/30424657/. Demonstra contribuições tanto das cordas quanto dos componentes estruturais.
**Falta:** identificar espectros C2/C3 com força/placa/camada longitudinal separados; evitar classificar todo pico extra como defeito de modelo.

### K16 — Tampa, aro, quadro, outras superfícies e sala
1. **_Operational transfer path analysis of a piano_**, TU Eindhoven, 2018 — **EXP**, https://research.tue.nl/en/publications/operational-transfer-path-analysis-of-a-piano/. Análise em um **Bösendorfer 280VC-9** da contribuição tampo/tampa/corpo. Importância da tampa nas altas frequências **do ensaio**, não em todos os pianos.
2. **_Sound Radiation from a Grand Piano_**, AES — **EXP**, https://aes.org/publications/elibrary/elibrary-page/?id=7613. Radiação de modos do tampo além de parciais sonoros.
3. **_Radiation Characteristics ... Stages of Production_**, ISMA 2017 — **EXP**, https://isma2017.cirmmt.mcgill.ca/proceedings/pdf/ISMA_2017_paper_16.pdf. Diretividade/estágio e posição do ouvinte; estudar outros instrumentos antes de generalizar.
4. **Yamaha — _Making the Body_** — **FAB**, https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/. Construção do aro, quadro e tampa.
**Falta:** mapa de transferência e radiação por partes do piano-alvo sob tampa aberta/fechada, condições de sala e microfone; não somar uma reverb de gravação no motor físico.

## P2 — duas lacunas de estabilidade e implementação

### K17 — Umidade, temperatura, envelhecimento, desgaste e manutenção
1. **Piano Technicians Guild — _Piano Care FAQs_** — **TEC**, https://www.ptg.org/ptgmain/piano/care/care-faqs. Umidade afeta estabilidade da afinação e condições de madeira/ação. Sugestões de climatização são guias práticos e não constantes de um modelo.
2. **_Influence of Humidity on the Tuning of a Piano_**, JASA 1949 — **EXP**, https://pubs.aip.org/asa/jasa/article-abstract/21/6/580/717920/Influence-of-Humidity-on-the-Tuning-of-a-Piano. Observações longas de afinação e umidade.
3. **Plath, _Influence of Playing on the Tonal Characteristics of a Concert Piano — Dataset_**, Zenodo 2019 — **DATA**, https://zenodo.org/records/3271370. Medições antes/depois de uso intenso em um piano; atribuir alterações apenas ao envelhecimento sem controles seria indevido.
4. **Yamaha Premium Quality** — **FAB**, https://usa.yamaha.com/products/contents/pianos/premium_pianos/quality/index.html. Processos de escolha/secagem e tratamento de madeira/feltro de determinados modelos, não prova de melhoria em qualquer piano.
**Falta:** condições de UR, temperatura, histórico de manutenção, repetição de medição e mudanças de afinação, rigidez/histerese e resposta da placa no tempo.

### K18 — 32–64 martelos e processamento físico em tempo real no navegador
1. **Bank, Zambon & Fontana, _A Modal-Based Real-Time Piano Synthesizer_**, IEEE TASLP 2010, DOI 10.1109/TASL.2010.2040524 — **MOD/SISTEMAS**, https://iris.univr.it/handle/11562/342223. Mostra síntese física modal de movimento transversal/longitudinal e arquitetura paralela em condições do artigo; não benchmark do Stage V4.
2. **Balázs Bank — Publications** — **BIBLIOGRAFIA**, https://home.mit.bme.hu/~bank/publist/index.html. Fonte autoral de métodos de DSP piano, não licença automática de código.
3. **MDN — _AudioWorkletProcessor.process()_** — **STD**, https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletProcessor/process. Chamadas síncronas na thread de áudio; o tamanho do bloco não deve ser assumido eternamente fixo.
4. **W3C — _Web Audio API 1.1_** — **STD**, https://www.w3.org/TR/webaudio-1.1/. Quantum default 128 frames, rendição de áudio e métricas/requisitos da API.
5. **MDN — _Background audio processing using AudioWorklet_** — **STD**, https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Using_AudioWorklet. Preparação do Worklet e processamento no browser, não performance garantida em aparelho específico.
**Falta:** após C4 aprovado, perfilar 88 cordas/teclas permanentes, 32/48/64 martelos simultâneos, bordo/tampo comum, CC64, pedal parcial, 48kHz/variantes de block, CPU/GC/underruns em PC/Android. Não considerar CI Node prova de tempo real.

## 3. Índice de cobertura e confirmação de limites

| Prioridade | K IDs | Fontes científicas ou técnicas verificáveis localizadas | Ainda carece de medição no piano-alvo? |
|---|---|---|---|
| P0 | K01–K09 | Todos têm 2–5 entradas individualizadas | **Sim, todos** |
| P1/P2 | K10–K16 | Todos têm 2–5 entradas individualizadas | **Sim, todos** |
| P2 | K17–K18 | Todos têm ≥3 entradas individualizadas | **Sim, todos** |

**Por que a bibliografia ainda não torna o V4 um piano?** Porque muitos artigos descrevem instrumentos diferentes e alguns nem fornecem curvas de força, tempo, mobilidade complexa ou microfone em tabelas transferíveis. Não temos um único piano-alvo com parâmetros C4/ação/corda/ponte/tampo/campo acústico medidos e ligados pela mesma linha temporal.

## 4. Leitura em sequência por retorno prático (proposta)

### Ciclo A — raízes do ataque (K02/K03/K04/K08)
1. Askenfelt/Jansson + Goebl: duração, cinemática, velocity.
2. Giordano/Winans + Stulov + experimento JASA 2013: feltro viscoelástico e força em corda real.
3. Conklin + medição de inarmonicidade + Askenfelt III: forma da força, posição do golpe e parcials.
4. Plath, com confirmação de licença e instrumentos: alinhamento keybed–ponte–ouvinte (SEM confundir keybed com feltro).

### Ciclo B — corpo/resposta acústica (K05/K06/K07/K16)
1. Miranda Valiente + Corradi: corda/apoio, mobilidade com pontes e montagem.
2. Ege/Boutillon + JASA soundboard: modos localizados, madeira com nervuras/condições.
3. ISMA/AES/TUe: diretividade, tampa, sala e pressão em posição definida.

### Ciclo C — caráter de piano, manutenção e musicalidade (K09–K15/K17)
1. Teste de percepção controlada (loudness, pitch, duração).
2. Weinreich: uníssono, batimentos e aftersound.
3. PTG/Yamaha: alinhamento, regulagem, desgaste e pedais.
4. Lehtonen + Bank/Etchenique + estrutura de madeira: simpatia e phantom partials.
5. Histórico/duplex e climatização, somente após notas reais.

### Ciclo D — implementação (K18)
Depois de o C4 ter som reconhecível e causalmente explicado, arquitetar simulação com DSP modal/waveguide passivo e medir recursos em hardware-alvo. **Nenhum número de testes unitários substitui esse gate**.

## 5. Controle de direitos, interpretação e próximos passos

- Links podem exigir assinatura acadêmica; um **resumo validado** não basta para extrair parâmetros finos de figures/tabelas, e uma recomendação de fabricante não é lei universal.
- Não usar fotos/áudios de terceiros no código Stage Synth ou nos documentos distribuídos sem autorização; referências bibliográficas são apontadores, **não material reproduzido**.
- Para converter artigo em parâmetro implementável, guardar: autor/ano; piano e nota; tipo de sensor; condições de contorno; valor + unidade + tolerância; amostra/controle; método; confidência; validade fora dos dados do artigo.
- Se não houver publicação com todos os sinais do mesmo piano, solicitar **campanha de medição própria** com técnico/acústico habilitados; evitar extrapolação arbitrária.
- **Estado de produto:** V4 permanece em pesquisa draft, \`main\` v1.12.8 intacta; não há WAV V4 aprovado como piano e a geração deve continuar exclusivamente por modelagem física.
