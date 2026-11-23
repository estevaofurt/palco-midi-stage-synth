# CADERNO DE ESTUDOS V4 — O piano acústico como instrumento completo

**Projeto:** Stage Synth — desenvolvimento do novo piano de modelagem física pura  
**Data:** 23 de novembro de 2026  
**Status:** pesquisa multidisciplinar, não implementação integrada; PR #39 em draft.  
**Base do aplicativo:** main v1.12.8, commit 626f5089, **não modificada**.  
**Decisão do titular:** abandonar o E2/E3 como candidata de timbre (E3.4 foi percebido como sintetizador/piano elétrico), recomeçar o piano, estudar detalhadamente sua construção e aprender com vários campos, não apenas com artigos de síntese matemática.

## 0. Método científico, limites e prioridades

**Conhecimento sobre construção ≠ validação de timbre.** Diferenciar três categorias:
- **Fato documentado:** processos de fabricantes, medições publicadas, funcionamento mecânico comprovado.
- **Hipótese de projeto:** como essas propriedades podem ser representadas no V4.
- **Dado ainda ausente:** propriedades medidas da escala, ação, cordas, ponte, tampo, radiação e impressão auditiva de um piano-alvo específico.

As páginas de fabricantes são evidência direta dos **próprios processos de fabricação**, mas afirmações de superioridade de uma marca não devem ser transformadas em fatos científicos universais. Estudos laboratoriais específicos não devem ser universalizados para todas as marcas, notas, ambientes e velocidades.

**Regra de áudio:** as gravações existentes servem para estudo, medição e escuta comparativa quando autorizadas; NUNCA para reproduzir notas, ataques, ruídos, respostas ao impulso ou reverberações na síntese. O V4 será gerado apenas por mecanismos calculados. A aprovação subjetiva da sonoridade de piano é mandatória antes de escalas, presets ou polifonia.

## 1. Organologia e história: o que estamos tentando reproduzir?

O piano nasce da solução de **Bartolomeo Cristofori** (registro em 1700) de um teclado que propulsiona um martelo e permite tocar suave/forte, em vez de beliscar continuamente as cordas como o cravo. A invenção introduziu problemas de escapamento, repetição e captura do martelo. O mecanismo moderno, o quadro fundido, o encordoamento cruzado e os materiais são frutos de séculos de evolução, não um único desenho universal.

A ampliação do registro, a robustez do quadro e a evolução da ação modificaram substancialmente o timbre: **fortepiano histórico, piano vertical e piano de cauda moderno não são o mesmo instrumento**. O projeto precisa nomear seu alvo: inicialmente um **piano de cauda acústico contemporâneo, nota Dó4**, e só depois estabelecer perfis de outros instrumentos, sem transferir parâmetros de um para outro cegamente.

Fontes:
- The Metropolitan Museum of Art — *The Pianofortes of Bartolomeo Cristofori*: https://www.metmuseum.org/ko/essays/the-piano-the-pianofortes-of-bartolomeo-cristofori-1655-1731
- National Music Centre — *Bartolomeo Cristofori Grand Piano*: https://nmc.emuseum.com/objects/224/bartolomeo-cristofori-grand-piano
- Yamaha — história, estrutura e fabricação: https://www.yamaha.com/en/musical_instrument_guide/piano/

## 2. Anatomia funcional — caminho real da energia

### 2.1 Ação do teclado: não apenas um acionador MIDI

Abaixar a tecla movimenta um sistema de alavancas e articulações: tecla, capstan, balancim/wippen, macaco (jack), rolo, haste, martelo, escape (let-off), alavanca de repetição, backcheck e abafadores. O escapamento libera o martelo perto da corda; depois do impacto o martelo retorna e é capturado. A ação de cauda possui mecanismo de dupla repetição distinto do vertical. **A intensidade acústica resulta da velocidade do martelo no instante de impacto**, mas os movimentos mecânicos da ação e da tecla também produzem sons e influenciam a percepção.

Em um caso experimental documentado por Askenfelt/Jansson, o abafador saiu da corda cerca de 15 ms antes do impacto e o contato durou por volta de 2 ms; **não** são tempos fixos ou universais. Estudo de ação inclui curso da tecla, ponto de escape, peso/inércia, repetição, ruído das articulações e afastamento do abafador. Uma tecla MIDI velocity 1–127 **não equivale diretamente** a uma velocidade de martelo em m/s sem curva e calibração.

Fontes:
- Yamaha, mecanismo da ação: https://www.yamaha.com/en/musical_instrument_guide/piano/mechanism/mechanism003.html
- KTH, Askenfelt/Jansson, timing: https://www.speech.kth.se/music/5_lectures/askenflt/timing.html
- KTH, medições de timing: https://www.speech.kth.se/music/5_lectures/askenflt/measure.html
- Steinway, história da ação: https://www.steinway.com/piano-action
- Estudo multibody vertical × cauda: https://www.sciencedirect.com/science/article/abs/pii/S0094114X21000549

### 2.2 Martelo: madeira, feltro, forma e preparação

A Yamaha documenta núcleos de madeira cobertos por **feltro de lã**, cortado com formato e dimensões diferentes conforme o registro. A fabricação inclui prensagem/colagem e repouso do material. O feltro não tem uma dureza única: a resposta depende da deformação, velocidade, histórico de carga, histerese, temperatura/umidade, região do feltro e desgaste. O núcleo e a haste também têm massa e flexibilidade.

Técnicos executam **harmonização (voicing)**: alinhar martelos às cordas, modelar a superfície, raspar/lixar, aplicar agulhas e, quando apropriado, tratamentos de dureza, sempre depois de conferir afinação e regulagem. Isso é **construção do timbre**, não um equalizador aplicado ao som pronto.

Medições com câmera rápida de um piano vertical captaram o movimento de martelo e cordas em **oito dinâmicas, com velocidades de impacto de 1,06 a 2,98 m/s**; tais dados são específicos ao experimento e não são limites universais. Askenfelt mostra que o contato martelo–corda fica mais curto com ataques fortes e varia de cerca de 4 ms nos graves para menos de 1 ms no extremo agudo em seu instrumento.

**Implicação V4:** devemos obter uma lei de compressão **com perdas/histerese**, massa efetiva e força-tempo plausíveis por nota/velocidade. O antigo "feltro 12 vezes mais rígido" sem fonte empírica é um exemplo do que NÃO repetir. **Não criar uma faixa de "click" sintético por fora da mecânica** para forçar percepção de percussão.

Fontes:
- Yamaha, fabricação do martelo: https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing002.html
- Yamaha, harmonização na fábrica: https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing005.html
- Askenfelt/Jansson, contato e dinâmica: https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html
- *Experimental investigation of the piano hammer-string interaction*, JASA, 2013: https://pubmed.ncbi.nlm.nih.gov/23556611/
- *Testing the Nonlinearity of Piano Hammers Using Residual Shock Spectra*, pesquisa da Penn State: https://pure.psu.edu/en/publications/testing-the-nonlinearity-of-piano-hammers-using-residual-shock-sp/
- *Physics-informed differentiable method for piano modeling* (histerese): https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full
- Piano Technicians Guild, harmonização/regulagem: https://www.ptg.org/piano/care/servicing

## 3. Escala de cordas: fabricação e engenharia por registro

Uma nota não corresponde necessariamente a uma corda. A Yamaha ensina que a região média/aguda tem tipicamente **três cordas por tecla**; nos graves há transição para duas e depois uma. Os bordões utilizam **núcleo e enrolamento de cobre**, ao passo que médias/agudas usam aço nu; comprimento, diâmetro, tensão e número de cordas são **projetados por registro**. Isso é parte do desenho da escala (scaling).

Equação inicial de uma corda flexível: f aproximadamente (1/2L)*sqrt(T/mu). A rigidez longitudinal e transversal, o diâmetro, o módulo de elasticidade e as condições de contorno fazem os parciais terem **inarmonicidade**. A escala também influencia o ponto de martelo: a posição relativa ao comprimento vibrante pode enfraquecer certos parciais, enquanto a velocidade/tempo de contato altera a distribuição do ataque.

A Yamaha descreve variações de movimento mesmo entre cordas do mesmo uníssono e disponibiliza exemplos de diferença de afinação ilustrativa ±0,5, ±1,0 e ±1,5 cent; **não transformar esses exemplos didáticos em valores universais de desafinação intencional de fábrica**. As cordas interagem através da ponte, produzindo batimentos e decaimentos complexos. A afinação profissional procura uníssonos coerentes, não simplesmente três osciladores independentes com detune fixo.

**Implicação V4:** tabela de escala por nota com comprimento vibrante, raio de aço, massa linear (inclusive enrolamento), tensão nominal, ponto de impacto, número de cordas, resistência/perdas, polarizações e pontos de apoio. Para um acorde, as várias cordas precisam compartilhar **ponte física**, não somar WAVs gerados em modelos separados.

Fontes:
- Yamaha, desenho das cordas: https://www.yamaha.com/en/musical_instrument_guide/piano/mechanism/mechanism004.html
- Yamaha, encordoamento (~230 cordas, ~20 toneladas na demonstração da fábrica): https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing003.html
- KTH, Gabriel Weinreich — acoplamento de cordas: https://www.speech.kth.se/music/5_lectures/contents.html
- Cheng/Dixon/Mauch, *Modelling the Decay of Piano Sounds* (ICASSP 2015): https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2015/ChengDixonMauch-ICASSP2015-Decay.pdf
- *Effect of inharmonicity on pitch perception and subjective tuning of piano tones* (JASA 2022): https://doi.org/10.1121/10.0013572

## 4. Ponte, tampo, nervuras, aro e quadro: o corpo vibrante

### 4.1 Processo real de fabricação

A Yamaha descreve a seleção de **abeto (spruce)**, secagem até determinada umidade, junção de tábuas, corte/espessura, colagem de nervuras perpendicularmente ao veio e fixação de duas pontes (longa e curta) no lado oposto às nervuras. O tampo recebe uma **ligeira curvatura (crown)** e se ajusta ao aro. O aro combina madeiras laminadas e vigas, enquanto a placa de ferro fundido sustenta a enorme tensão acumulada das cordas. Pontes e pinos de ponte transmitem forças de cordas ao tampo. Diferentes fabricantes adotam métodos diferentes de coroa, taper de espessura, nervuras e soluções de estabilidade.

Kawai destaca o uso de compósitos ABS-Carbon no mecanismo e madeira de tampo preparada; Mason & Hamlin documenta abeto, coroa de múltiplos raios, taper de bordas, pontes laminadas de maple e seu tension resonator. **Não são evidências de superioridade sonora universal**, mas demonstram diversidade real de engenharia.

### 4.2 Consequências científicas

Uma madeira é **ortotrópica**: elasticidade e propagação são diferentes ao longo e transversalmente às fibras. Nervuras, pontes, grampos, aro, secagem, umidade e tensão estática do encordoamento modificam as formas modais. Um estudo acompanhou o mesmo tampo livre, com pontes instaladas e finalmente montado no quadro do piano; a mudança da construção altera as medidas de mobilidade. Outra pesquisa encontrou efeitos importantes da estrutura/arranjo do tampo em suas frequências e modos.

**Implicação V4:** jamais confundir a velocidade **localizada** da ponte com a velocidade distribuída do tampo. Devemos medir ou calcular a **mobilidade complexa** na ponte (relação força→velocidade no espaço/frequência) e a distribuição real de modos de placa/madeira/nervuras. Quatro ou dezesseis senos matemáticos arbitrários não representam necessariamente o corpo de um piano.

Fontes de fabricação:
- Yamaha, corpo, aro, tampo e frame: https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/
- Kawai Shigeru: https://www.shigerukawai.jp/en/features/
- Mason & Hamlin: https://www.masonhamlin.com/craftsmanship/

Fontes experimentais:
- *Modal analysis of a grand piano soundboard at successive manufacturing stages*: https://www.sciencedirect.com/science/article/pii/S0003682X17303444
- *Dynamical properties of piano soundboards*, JASA: https://pubmed.ncbi.nlm.nih.gov/23556610/
- *Piano soundboard: structural behavior, numerical and experimental study in the modal range*: https://www.sciencedirect.com/science/article/pii/S0003682X03000653
- *Measurement and Analysis of Vibration Responses of Piano Soundboards with Different Structures* (2024, acesso aberto): https://pmc.ncbi.nlm.nih.gov/articles/PMC10934193/

## 5. Acústica efetiva: o instrumento soa no AR, não no osciloscópio da corda

As vibrações são transmitidas em sequência: cordas → ponte → tampo → ar, com participação do aro, tampa, reflexão, caixa, chão e ambiente. A radiação espacial não é uniforme: local e orientação do ouvinte e microfone alteram o espectro percebido. Um estudo da DPA com matriz de **dez microfones** investigou posições, abertura da tampa e campos sonoros, reforçando que comparar um microfone próximo contra um som de ouvinte não é um teste justo.

Estudos da radiação do tampo analisam pressão/velocidade em diversos pontos e distinguem baixos modos estruturais de padrões radiativos complexos em frequências médias/altas. Além das parciais musicais, a radiação pode incluir transientes estruturais excitados pela ação. **Isso não autoriza sobrepor ruído aleatório**: primeiro descobrir a fonte mecânica e sua transmissão.

**Implicação V4:** escolher uma condição de escuta de referência (ex.: cauda com tampa aberta, ouvinte à frente), estudar radiação com posição explícita e comparar tomadas em **posições e níveis equivalentes**. Ambiente e posicionamento deverão ser controlados no protocolo de medição.

Fontes:
- DPA, campo sonoro e matriz de mics: https://dpa-microphones.euwest01.umbraco.io/mic-university/background-knowledge/piano-sound-fields-and-miking-implications/
- Shure, técnicas de gravação: https://www.shure.com/en-US/docs/education/Microphone-Techniques-for-Recording
- AES, *Sound Radiation from a Grand Piano*: https://aes.org/publications/elibrary/elibrary-page/?id=7613
- *Vibroacoustics of the piano soundboard* (modelo reduzido): https://www.sciencedirect.com/science/article/pii/S0022460X13002472

## 6. O piano é REGULADO, AFINADO e HARMONIZADO após construído

A fábrica não termina o piano ao instalar peças. Yamaha descreve afinação final, regulagem do movimento do teclado/ação e harmonização especializada dos martelos. A PTG (Piano Technicians Guild) separa:
- **Afinação**: alteração das tensões nas cordas/pinos para determinar alturas/uníssonos.
- **Regulagem**: alinhamento, distância de golpe, escape, queda, repetição, retorno de tecla, captura do martelo, abafadores e pedais.
- **Harmonização (voicing)**: forma e consistência dos martelos, elasticidade/dureza do feltro, brilho e uniformidade entre notas.
- **Manutenção/reconstrução**: controle de condições de madeira, cordas, pinos, mecanismo, pontes e tampo.

A inarmonicidade exige afinação acústica com extensão dos extremos em relação à temperação de frequências matematicamente exatas: **stretch tuning**. A curva e magnitude dependem do instrumento e sua escala; a pesquisa JASA 2022 relaciona inarmonicidade e percepção de afinação.

**Implicação V4:** um modelo fisicamente correto de um piano **fora de regulagem** pode soar pior; precisamos de parâmetros de "regulação virtual" com fundamento na ação real, não de presets de EQ como substituição. Normalizar afinação antes de comparar timbres para não confundir desafinação com sensação de falta de realismo.

Fontes:
- Yamaha, voicing da fábrica: https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing005.html
- PTG, manutenção e harmonização: https://my.ptg.org/ptgmain/piano/care/care-faqs
- PTG, exames de afinação/regulagem/reparo: https://my.ptg.org/ptgmain/join/careers
- JASA 2022, stretch tuning: https://doi.org/10.1121/10.0013572
- Referência prática bibliográfica: Artur A. Reblitz, *Piano Servicing, Tuning, and Rebuilding*: https://www.simonandschuster.co.uk/books/Piano-Servicing-Tuning-and-Rebuilding/Artur-A-Reblitz/9780757008825

## 7. O pianista e o ouvido humano são parte do problema

O artigo *Motor origins of timbre in piano performance*, PNAS (2025), investigou percepção do timbre, movimento das teclas e aspectos de execução, incluindo ruído de início, ruído da tecla ao fundo e movimento de escape. Concluiu haver relações mensuráveis entre gestos e características percebidas como **peso, clareza e brilho**; não significa que o pianista altera livremente as frequências naturais da corda de uma nota.

Na audição, alterar apenas **volume, duração, espectro médio, início da nota, posição de microfone ou reverberação** pode fazer o teste parecer melhor sem reproduzir corretamente o piano. Estudos de psicoacústica recomendam evitar covariação involuntária entre brilho, volume e ataque quando testamos timbre.

A **percussão solicitada pelo titular** pode envolver simultaneamente:
1. frente do impulso mecânico real martelo–corda;
2. vibração estrutural rápida que chega ao tampo e ao ar;
3. ruídos discretos da própria ação/teclas e escapamento.
É incorreto tratar os três como "mais dureza do feltro" ou como uma amostra única de "click".

Fontes:
- PNAS 2025: https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/
- *Preparation of stimuli for timbre perception studies*: https://pubmed.ncbi.nlm.nih.gov/23967955/
- KTH, cinco aulas de acústica de piano: https://www.speech.kth.se/music/5_lectures/contents.html

## 8. Cauda versus vertical e diferenças entre escolas de fabricação

Um **piano de cauda** tem encordoamento e tampo predominantemente horizontais e martelos geralmente lançados para cima; a geometria inclui mecanismo de repetição específico. No **vertical**, cordas/tampo são verticais, a ação tem arquitetura e comportamento de retorno diferentes e o móvel/parede podem influenciar bastante a radiação. Pedais também não são universalmente equivalentes: no cauda o una corda desloca a ação lateralmente; no vertical o pedal esquerdo geralmente modifica a distância do martelo às cordas, enquanto pedais intermediários variam.

Diferenças históricas: fortepianos de Cristofori, caudas de concerto atuais e verticais modernos são **famílias com dinâmicas/timbres diferentes**. O Stage Synth não deve tentar se passar por todos usando um único conjunto de parâmetros.

Fontes:
- Yamaha, cauda versus vertical: https://www.yamaha.com/en/musical_instrument_guide/piano/selection/
- Yamaha, pedais em detalhe: https://hub.yamaha.com/pianos/p-acoustic/how-does-a-piano-work/
- Kawai, materiais da ação contemporânea: https://www.shigerukawai.jp/en/features/
- Met Museum, instrumentos históricos: https://www.metmuseum.org/ko/essays/the-piano-the-pianofortes-of-bartolomeo-cristofori-1655-1731

## 9. O estudo de campo é indispensável

A teoria precisa encontrar **um piano acústico real**. O protocolo a seguir é de pesquisa e exige autorização do proprietário/técnico; **não** modificar mecanicamente instrumentos de terceiros ou retirar tampas/cordas sem profissional habilitado.

**Inventário inicial de um piano de referência**:
- fabricante/modelo/tamanho/ano aproximado/cauda ou vertical, estado técnico;
- escala: notas A0–C8, 1/2/3 cordas, bordões enrolados, comprimentos vibrantes e ponto do martelo;
- ação: massa/inércia efetivas, curso e repetição, feltro, regulagem, deslocamento e velocidade do martelo;
- madeira: espécie/veio/umidade/espessura, nervuras, crown, localização da ponte;
- estado de afinação, uníssonos, pedais e abafadores;
- resposta vibracional e acústica em posições e dinâmicas documentadas.

**Campanha de medição ideal (pessoal treinado)**:
- MIDI/captura de velocidade do teclado, câmera alta velocidade no martelo, microfone de contato/medição de aceleração na ponte e tampo, microfone calibrado no ar;
- registrar C2/C3/C4/C5/C6 em pp/mf/ff, notas curtas/longas e com/sem sustain;
- medir separadamente: velocidade do martelo, tempo de contato, movimento da corda, mobilidade na ponte, vibração da placa, pressão no ar e ruídos da ação;
- separar posições de microfone: perto do martelo, sobre o tampo e posição de ouvinte, com informações de abertura da tampa e sala;
- auditar clipping, alinhamento temporal, ruído de fundo, frequência de amostragem e licenças antes de calcular espectros;
- repetir medidas para estimar variabilidade — um único WAV isolado não define uma verdade universal.

**AVISO:** os dispositivos e métodos acima são alvos de uma campanha futura, não equipamentos que o projeto possui nem medições que já realizamos.

## 10. O que deve mudar IMEDIATAMENTE na V4

1. **Não continuar E3.4.** Encerrar a hipótese "mais modos arbitrários + feltro endurecido = piano"; o titular reprovou auditivamente.
2. **Não adicionar ponte/tampo por palpite.** A V4.0 já tem uma corda física independente. Antes do V4.2, especificar massa, rigidez, perdas, apoio, posição da ponte e mobilidade, além de testes de energia recíproca.
3. **Ajustar martelo a partir de dados reais:** medir/ancorar contato versus velocidade e registro, com histerese se identificada.
4. **Medir o ataque em cada estágio físico:** força do feltro, velocidade da corda, força da ponte, velocidade do tampo, som no ar, ruído de ação. Identificar exatamente onde a percussão desaparece; não usar click artificial.
5. **Estudar o tampo real:** madeira ortotrópica, nervuras, espessura/crown, bordas e mapas de mobilidade/radiação. Não substituir a geometria por dois números fixos.
6. **Escuta como gate de produto:** WAV V4 de UMA nota em diferentes dinâmicas com contexto de captura/nível comparável. Sem aprovação do timbre, não desenvolver escalas/acordes.
7. **Só então acordes:** duas/três cordas por tecla, uníssono real, batimentos, decaimento duplo, 32–64 martelos e uma ponte/tampo comuns, sustentação/abafadores. Validar CPU em browser/hardware, não apenas no Node/Linux.
8. **Regra de propriedade intelectual:** audio externo de diagnóstico somente, sem copiar samples, IRs, DSP de terceiros, patentes restritas ou gravações não licenciadas para distribuição.

## 11. Bibliografia multidisciplinar — ordem de estudo sugerida

| Módulo de especialização | Melhor porta de entrada | Foco | Origem |
|---|---|---|---|
| Organologia/história | Met Museum, Cristofori | O que define piano e sua evolução | Museu |
| Anatomia e fabricação | Yamaha Musical Instrument Guide | Sequência real de produção | Fabricante |
| Ação e tempos | KTH, Askenfelt/Jansson | Tecla, escapamento, contato, repetição | Pesquisa experimental |
| Feltro e harmonização | Yamaha + PTG + JASA de hammer/string | Por que um martelo pode soar diferente | Técnica + laboratório |
| Escala de cordas | Yamaha + KTH/Weinreich | Geometria, uníssonos, ataques, decaimento | Indústria + física |
| Ciência da madeira | artigo PMC 2024 + Yamaha | Ortotropia, umidade e desenho do tampo | Materiais |
| Fabricação comparada | Kawai + Mason & Hamlin | Soluções de projeto diferentes | Fabricantes |
| Vibroacústica medida | JASA, Applied Acoustics | Mobilidade de ponte/tampo, radiação | Engenharia experimental |
| Afinação e regulagem | Piano Technicians Guild + Reblitz | Tornar o instrumento responsivo e coerente | Profissão |
| Timbre e execução | PNAS 2025 + estudo psicoacústico | O que o ouvido realmente distingue | Neurociência |
| Som no ambiente | DPA + AES/Shure | Diretividade, tampa, captação real | Engenharia de áudio |
| Modelagem física | Chabassier/Chaigne/Joly | Implementar a teoria APÓS conhecer o instrumento | Matemática aplicada |

### Referência de método integrado, não copiar software
- *Modeling and simulation of a grand piano*, JASA 2013: https://pubmed.ncbi.nlm.nih.gov/23862839/
- *Time domain simulation of a piano, Part 1*, ESAIM M2AN 2014: https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
- *Five Lectures on the Acoustics of the Piano* (KTH/Royal Swedish Academy of Music): https://www.speech.kth.se/music/5_lectures/contents.html

---

## 12. Resposta à pergunta "por que não soava acústico?"

**Hipótese de engenharia (não diagnóstico comprovado com dados de campo):** o motor anterior acertava relações de frequências, mas falhava na **cadeia causal e material** de propagação do impacto, na **impedância e construção real da ponte/tampo**, nos **tempos/ruídos da ação**, nos **uníssonos acoplados** e na **evolução de energia no tempo**. Ao aumentar modos e percussão arbitrariamente, aproximava-se mais de um sintetizador com características de piano do que do instrumento real.

**Nova diretriz:** primeiro instrumento real → medições/leis da física → cadeia acústica verificável → escuta humana → eficiência de computador → integração. Nessa ordem.
