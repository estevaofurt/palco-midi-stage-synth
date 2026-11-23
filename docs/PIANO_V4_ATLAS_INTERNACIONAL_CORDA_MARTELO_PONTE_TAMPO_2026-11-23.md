# STAGE SYNTH V4 — ATLAS INTERNACIONAL DE PESQUISA: MARTELO → CORDAS → PONTE → TAMPO → AR

**Data da coleta:** 23/11/2026. **Status:** investigação e interpretação de literatura internacional, sem implementação de novo motor. **Branch:** research/piano-v4-restart-physical-20261123, PR #39 draft. O produto main v1.12.10 permanece inalterado.

**Pedido:** “procure por mais referencias para cordas → martelo → ponte → tampo, procure por estudos em todo o mundo.”

**Observação:** a ordem de transferência de energia ao executar uma nota é, em termos físicos, **ação/tecla → martelo/feltro ↔ cordas ↔ ponte ↔ tampo ↔ ar**, com retroação de cada estrutura sobre a anterior. O subsistema do martelo pode sofrer influência da ação durante o contato. Referências a circuitos elétricos equivalentes são analogias matemáticas da física, NÃO síntese de um piano elétrico.

## 0. Como foi feita a busca e o que se pode afirmar

A pesquisa pesquisou registros de artigos/anais, abstracts nas páginas das editoras, repositórios de universidade, arquivos históricos japoneses J-STAGE e páginas abertas de estudos experimentais. **Algumas publicações têm PDF disponível; esta coleta não afirma leitura integral dos PDFs de todas elas**. Quando há acesso pago, a descrição restringe-se ao abstract e aos metadados publicados. A diversidade regional não é uma lista decorativa: cada grupo respondeu uma pergunta técnica verificável da V4.

- **Evidência EXP:** experimento em instrumento, dispositivo ou material identificado, mas não generaliza a todos os pianos.
- **MOD/VALID:** simulação física comparada com medições, sujeita às condições do estudo.
- **REVIEW:** revisão; boa para descobrir bibliografia, menos adequada para retirar parâmetros físicos.
- **THESIS:** pesquisa extensa de um instituto/universidade; observar data, instrumentação e recorte.
- **TÉCNICA:** procedimento de medição que pode ser reproduzido; não é valor medido do nosso instrumento.
- **SINTESE:** metodologias de otimização/controle numérico do som com física interpretável; NUNCA incorporar samples/IR gravadas na V4.

**Princípio decisivo:** o modelo não estará “pronto” por conhecer estudos mundiais; ainda não temos características reais e simultâneas de um piano-alvo. Qualquer número físico retirado dessas fontes deve registrar unidade, instrumento, direção, posição, microfone, dinâmica, faixa e incerteza.

## 1. Japão — acústica integrada e medições diretas dos martelos

### JP-01 | Isao Nakamura, *Simulation of the sound production mechanism: Acoustical research on the piano, Part 2* (1981)
**Fonte:** https://www.jstage.jst.go.jp/article/jasj/37/2/37_KJ00001455009/_article/-char/en  
**Tipo:** MOD, original J-STAGE, DOI **10.20697/jasj.37.2_65**.  
**Resultado relevante:** cadeia explícita com martelo, propagação na corda, impedância de reflexão na ponte, movimento do tampo e pressão acústica; simulação por circuitos eletromecânicos equivalentes. O trabalho discute batimentos por ligeiras diferenças de afinação e decaimento inicial rápido seguido de pós-som. **Limite:** a aproximação e hardware/condições de 1981 não representam piano contemporâneo calibrado.  
**Relevância:** contrato energético F3↔F4↔F5↔F6↔F7. Confirmar a notação original do artigo antes de transcrever coeficientes.

### JP-02 | Takeshi Yanagisawa & Kijuro Nakamura, *Dynamic compression characteristics of piano hammer felt* (1984)
**Fonte:** https://www.jstage.jst.go.jp/article/jasj/40/11/40_KJ00001453633/_article/-char/en  
**Tipo:** EXP, DOI **10.20697/jasj.40.11_725**.  
**Resultado:** medem **força de martelo contra corda** e deslocamentos da madeira/núcleo de martelo e da corda **ao mesmo tempo** para deduzir compressão real. Relatam variação da rigidez efetiva durante o contato e criticam hipóteses de rigidez fixa.  
**Consequência V4:** selecionar lei de feltro por medição do evento de contato e por energia dissipada; não escolher “ratio de dureza” global. **Limite:** parâmetros do ensaio japonês não são parâmetros universais por nota.

### JP-03 | Isao Nakamura, *The vibration of a struck string (Acoustical research on the piano, Part 1)* (1992)
**Fonte:** https://www.jstage.jst.go.jp/article/ast1980/13/5/13_5_311/_article/-char/en  
**Tipo:** MOD, DOI **10.1250/ast.13.311**.  
**Resultado:** interação martelo–corda explicada por analogias de impedância/mobilidade, observando reflexões e comportamento temporal; útil para formular portas mecânicas conjugadas, não só formas harmônicas.

### JP-04 | Isao Nakamura, *Vibrational and acoustic characteristics of soundboard (Part 3)* (1993)
**Fonte:** https://www.jstage.jst.go.jp/article/ast1980/14/6/14_6_429/_article/-char/en  
**Tipo:** EXP/MOD, DOI **10.1250/ast.14.429**.  
**Resultado:** com cordas instaladas, frequências de alguns modos do tampo sobem e Q diminui; em altas frequências a vibração local ocorre entre nervuras, alterando admitância e campo irradiado. É evidência **contra** considerar tampo isolado com a mesma lista de modos após juntar as cordas.  
**Teste V4:** medir a placa antes/depois de acoplar cordas/ponte ou confirmar por solver com pré-tensão e condições de contorno.

### JP-05 | Isoharu Nishiguchi, *Recent research on the acoustics of pianos* (2004)
**Fonte:** https://www.jstage.jst.go.jp/article/ast/25/6/25_6_413/_article/-char/en  
**Tipo:** REVIEW, DOI **10.1250/ast.25.413**.  
**Resultado:** revisão japonesa ligada a ISMA Nara 2004/ICA Kyoto 2004, incluindo parciais secundárias, golpe e acoplamento cordas–ponte–tampo. Excelente índice de **47 referências**, sem retirar delas números não verificados.

## 2. Canadá — a ação mecânica NÃO é independente do contato

### CA-01 | Vyasarayani, Birkett & McPhee, *Modeling the dynamics of a compliant piano action mechanism impacting an elastic stiff string* (2009)
**Fonte:** https://pubmed.ncbi.nlm.nih.gov/19507984/  
**Tipo:** MOD, Universidade de Waterloo, DOI **10.1121/1.3125343**.  
**Resultado:** modela ação com alavancas/corpos rotativos, haste flexível, contatos com perdas histeréticas e **atrito tangencial entre cabeça e corda**. O movimento da ação afeta duração, força e posição de impacto, e a flexibilidade da haste modifica o resultado.  
**Mudança V4:** tratar martelo de massa pontual como primeira bancada F4, mas manter interface capaz de receber retorno de haste/ação; não afirmar que massa pontual isolada é o martelo real.

### CA-02 | Stephen Birkett, *Experimental investigation of the piano hammer-string interaction* (2013)
**Fonte:** https://pubmed.ncbi.nlm.nih.gov/23556611/  
**Tipo:** EXP, Waterloo, DOI **10.1121/1.4792357**.  
**Resultado:** observa força/compressão durante interação com cordas reais, deformação da haste e pulsos refletidos no apoio/agrafes. **Diferencia medição de martelo–corda de teste de martelo contra sensor rígido**.  
**Teste V4:** verificar contato/recontato e propagação de ondas de reflexão durante a batida.

## 3. França — equações acopladas e tampo com nervuras

### FR-01 | Chabassier, Chaigne & Joly, *Modeling and simulation of a grand piano* (2013)
**Fonte:** https://pubmed.ncbi.nlm.nih.gov/23862839/  
**Tipo:** MOD, JASA, DOI **10.1121/1.4809649** (confirmado pelo registro bibliográfico da publicação JASA 134, 648–665).  
**Resultado:** cordas rígidas com perdas e não linearidades, contato dissipativo de feltro, ponte/tampo ortotrópico com nervuras, ondas transversais/longitudinais e acoplamento ao ar. Não é um sample player nem prova de que toda implementação reduzida terá mesmo timbre.

### FR-02 | Chabassier, Chaigne & Joly, *Time domain simulation of a piano. Part 1: Model description* (2014)
**Fonte:** https://www.numdam.org/item/M2AN_2014__48_5_1241_0/  
**Tipo:** MOD, texto matemático de referência; detalha equações de cordas, apoio, tampo e ar com interações.  
**Relevância:** especificar **equações de interface e energia total** antes do DSP.

### FR-03 | Ege, Boutillon & Rébillat, *Vibroacoustics of the piano soundboard: Reduced models, mobility synthesis, and acoustical radiation regime* (2013)
**Fonte:** https://www.sciencedirect.com/science/article/pii/S0022460X13002472  
**Tipo:** EXP/MOD, JSV.  
**Resultado:** ponte tem **mobilidade dependente de ponto e frequência**; nervuras levam a padrões de vibração mais localizados em parte da banda. O estudo de referência comenta regimes de estrutura e radiação, não justifica inventar “N modos” por ouvido.  
**Teste V4:** comparar mapa modal, admitância de ponte e radiação separadamente; testar pontos C4 e outras notas.

### FR-04 | Chaigne, Cotté & Viggiano, *Dynamical properties of piano soundboards* (2013)
**Fonte:** https://pubmed.ncbi.nlm.nih.gov/23556610/  
**Tipo:** EXP/MOD, JASA.  
**Resultado:** pequenas irregularidades no espaçamento das nervuras podem concentrar vibrações e reduzir a área efetivamente radiante; fase/diretividade importam.

## 4. Itália — medições ao longo da montagem de um piano real

### IT-01 | Corradi, Miccoli, Ripamonti & Squicciarini, *Experimental Modal Analysis and Structural Modelling of a Grand Piano Soundboard to Support Instrument Design* (2010)
**Fonte:** https://re.public.polimi.it/handle/11311/572761  
**Tipo:** EXP/MOD, Fazioli/politecnico, anais RASD.  
**Resultado:** compara modos vibratórios e FE antes de colagem de pontes, incluindo curvatura e pré-tensão; **validação quantitativa relatada até ~250 Hz para tampo livre**. Não usar isso como garantia de precisão de 0–5kHz.

### IT-02 | Corradi et al., *Modal analysis of a grand piano soundboard at successive manufacturing stages* (2017)
**Fonte:** https://www.sciencedirect.com/science/article/pii/S0003682X17303444  
**Tipo:** EXP/MOD em Fazioli F278.  
**Resultado:** o mesmo tampo é medido solto antes e depois de colar pontes e depois montado; **mobilidade de ponte FE** comparada com medições, reportando boa concordância até 4 kHz nas condições do estudo.  
**Teste V4:** variar rigidez/geom da ponte e aro e verificar impacto na admitância e distribuição modal do MESMO modelo de tampo.

## 5. Alemanha — evolução da construção e amortecimento

### DE-01 | Niko Plath, *From Workshop to Concert Hall: Acoustic Observations on a Grand Piano under Construction* (2019)
**Fonte:** https://ediss.sub.uni-hamburg.de/handle/ediss/6308  
**Tipo:** THESIS, Universidade de Hamburgo, dois pianos de concerto medidos ao longo da fabricação.  
**Resultado:** nervuras condicionam propagação de ondas, ponte pode atuar como guia de ondas e partes da energia ficam localizadas em configurações espaciais específicas; mostra diferença entre tampo bruto e tampo com pontes/nervuras.  
**Teste V4:** quantificar propagação inicial no tampo, **não apenas frequências de modos estacionários**.

### DE-02 | Rolf Bader & Niko Plath, *Impact of Damping on Oscillation Patterns on the Plain Piano Soundboard* (2022)
**Fonte:** https://www.mdpi.com/2624-599X/4/4/62  
**Tipo:** EXP/MOD, modelos FDTD e medição de tampo em etapas de fabricação.  
**Resultado:** avalia como amortecimento interno e posição da força na ponte mudam padrões de vibração. A investigação usa uma placa bruta simplificada, de forma deliberada; NÃO representar a mesma placa como um tampo final de cauda pronto.

## 6. Reino Unido — interface multidirecional e escolha de complexidade

### UK-01 | Miranda Valiente, Squicciarini & Thompson, *Influence of soundboard modelling approaches on piano string vibration* (2024)
**Fonte:** https://pubmed.ncbi.nlm.nih.gov/38742965/  
**Tipo:** MOD, Southampton, DOI **10.1121/10.0025925**.  
**Resultado:** compara FE de tampo, redução a cinco modos, Kelvin-Voigt e apoio rígido; **efeitos sobre força transmitida, tempo de decaimento e movimento de área radiante**. Inclui segmento duplex na formulação. O fato de um modelo simples produzir alguns resultados semelhantes não é prova de que simplificações agressivas sejam sempre aceitáveis.
**Teste V4:** comparar ponte bloqueada, terminador passivo de laboratório e placa FE real; observar diferenças tanto na corda quanto no tampo, com dados da mesma condição.

### UK-02 | *Modelling the una-corda effect in pianos* (2024)
**Fonte:** https://eprints.soton.ac.uk/499445/  
**Tipo:** MOD.  
**Resultado:** cordas rígidas em três dimensões, movimento multidirecional e tampo modal compartilhado; analisar efeito de golpear somente parte das cordas do mesmo uníssono.  
**Mudança V4:** prever desde a interface F5 um **vetor de esforços e velocidades (vertical/horizontal/longitudinal)**, mesmo quando a primeira bancada é escalar. Evitar assumir que uma admitância vertical única descreve todas as interações.

### UK-03 | Pablo Miranda Valiente, *Modelling of sound generation in pianos* (2025)
**Fonte:** https://eprints.soton.ac.uk/504922/  
**Tipo:** THESIS, Southampton, resumo de repositório consultável via busca.  
**Resultado anunciado:** conjunto integrado ação/cordas/tampo e comparação de graus de liberdade e acoplamentos; estudo de rigidez, force, caminhos de radiação e uníssono. **Texto integral não foi conferido nesta coleta (repositório deu bloqueio de acesso à abertura)**: antes de copiar número/gráfico, obter versão completa e leitura direcionada.

### UK-04 | *Vibrations of piano strings and coupling to the soundboard*, Institute of Acoustics (arquivo histórico)
**Fonte:** https://www.ioa.org.uk/system/files/publications/AR%20BAXANDALL%20IS%20BROWN%20CE%20GOUGH%20VIBRATIONS%20OF%20PIANO%20STRINGS%20AND%20COUPLING%20TO%20THE%20SOUNDBOARD.pdf  
**Tipo:** EXP/MOD, arquivo PDF identificado, **não analisado integralmente**. Investigar polarizações transversais da corda e amortecimento/acoplamento por ponte. Adiar extração numérica até leitura integral.

## 7. Estados Unidos — medição física do som ao redor da ponte

### US-01 | Nicholas Giordano, *Simple model of a piano soundboard* (JASA 1997), mais *Mechanical impedance of a piano soundboard* (JASA 1998)
**Fonte primária de modelo:** https://www.physics.purdue.edu/piano/articles.shtml  
**Fonte experimental de impedância:** https://www.scispace.com/papers/mechanical-impedance-of-a-piano-soundboard-4alm9wsiiz  
**Tipo:** o primeiro é MOD/FE (JASA **102**, 1159–1168, 1997); o segundo é EXP (JASA **103**, 2128–2133, 1998).  
**Resultados distintos:** o estudo de 1997 modela **anisotropia e nervuras** para explicar impedância da placa; o estudo de 1998 **mede diretamente** a impedância de uma placa de piano na faixa de 50Hz–10kHz, encontrando diferenças com alguns resultados anteriores. Não confundir o modelo FE de 1997 com a campanha de medição de 1998.

### US-02 | Nicholas Giordano, *Sound Production by a Vibrating Piano Soundboard* (JASA 1998)
**Fonte institucional:** https://www.physics.purdue.edu/piano/articles.shtml  
**Tipo:** EXP.  
**Resultado:** mede **pressão sonora** e **velocidade do tampo** sob força aplicada em diferentes pontos da ponte, analisando a razão p/v em função da frequência. Resposta próxima de ~1 kHz destacada no resumo institucional; depende do ponto e geometria.  
**Teste V4:** construir protocolo separado de força de ponte → velocidade do painel → pressão de mic e validar fase e ganho espacial, não apenas um “espectro de piano”.

### US-03 | Daniel A. Russell & Thomas D. Rossing, *Testing the nonlinearity of piano hammers using residual shock spectra* (1998)
**Fonte institucional:** https://www.acs.psu.edu/drussell/Piano/Refs.html ; explicação técnica https://www.acs.psu.edu/drussell/hammers.html  
**Tipo:** EXP.  
**Resultado:** exame de dureza dinâmica de martelos por espectro de choque, com dependência de velocidade e dureza do feltro; **choque em transdutor rígido não equivale integralmente ao contato com uma corda vibrante**.  
**Teste V4:** validar força vs velocidade, duração e conteúdo transitório antes de culpar só o tampo por ataque fraco.

## 8. Hungria, Finlândia, Estônia e Suécia — sistema completo, perdas e escuta

### HU-01 | Jenei-Kulcsár & Fiala, *Piano Soundboard Analysis at Radiated Sound* (2023)
**Fonte:** https://www.pp.bme.hu/eecs/article/view/21181  
**Tipo:** MOD, Budapest University of Technology, DOI **10.3311/PPee.21181**.  
**Resultado:** compara martelo com feltro histerético, corda amortecida acoplada e placa 2D FE com nervuras + radiação no campo próximo. **Características acústicas medidas/estimadas dependem de admitância de tampo, ponto de excitação e posição do ouvinte**.  
**Teste V4:** não aceitar “piano pronto” a partir de espectro medido em posição única; observar posição do ponto de C4 e posições da fonte/mic.

### FI-01 | Balázs Bank, *Physics-based sound synthesis of the piano* (2000)
**Fonte:** https://research.aalto.fi/en/publications/physics-based-sound-synthesis-of-the-piano/  
**Tipo:** THESIS/report de 123 páginas, instituição finlandesa no contexto da pesquisa.  
**Resultado:** reúne aspectos de física e síntese, relevante especialmente quando houver redução real-time; **não concluir que toda recomendação DSP corresponde a um instrumento medido**. A etapa final de implementação permanece posterior ao C4 validado.

### EE-01 | Anatoli Stulov, *Hysteretic model of the grand piano hammer felt* (1995)
**Fonte:** https://cir.nii.ac.jp/crid/1362262945923645952  
**Tipo:** EXP/MOD, abordagem viscoelástica com **memória/histerese** do feltro; referência para F4, não fornecimento automático de parâmetros de um piano contemporâneo específico.

### SE-01 | Askenfelt & Jansson, *From touch to string vibration — hammer string contact/dynamics* (KTH)
**Fonte:** https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html  
**Tipo:** EXP, Suécia.  
**Resultado:** duração do contato muda com velocidade e região da tecla, afetando conteúdo espectral do ataque.

### SE-02 | Klaus Wogram, *The strings and the soundboard — measuring impedance* (KTH lecture)
**Fonte:** https://www.speech.kth.se/music/5_lectures/wogram/impedance.html  
**Tipo:** EXP/PROTOCOLO publicado nas aulas da Royal Swedish Academy.  
**Resultado:** shaker e sensor de impedância medem força e velocidade **simultaneamente** em pelo menos 14 posições da ponte, com fase e nível acústico, ao longo de 20Hz–10kHz (no instrumento/protocolo relatado). **Não confundir impedância Z=F/V com mobilidade Y=V/F**. Essas são respostas escalares na direção medida; resposta real multidirecional requer matriz de mobilidade.  
**Relevância:** metodologia AJ45/AJ56 e validação F5/F6/F7.

## 9. China — madeira e fabricação: medir geometria, não assumir placa uniforme

### CN-01 | Lan He et al., *Measurement and Analysis of the Vibration Responses of Piano Soundboards with Different Structures* (2024)
**Fonte:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10934193/  
**Tipo:** EXP, Northeast Forestry University, Harbin, revista *Materials*, DOI **10.3390/ma17051004**.  
**Resultado:** quatro construções diferentes de tampo (incluindo configurações de madeira/laminado) mostram modos e respostas diferentes por local de impacto e orientação do material. A resistência e módulo dinâmico diferem conforme método e orientação de medição.  
**Conseqüência V4:** o FE de tampo precisa de propriedades ortotrópicas por direção e mapa de nervuras; material nominal “spruce” sozinho não identifica densidade, rigidez e perdas do alvo.

## 10. Brasil — percepção, timbre e tradução entre ouvido e mecanismo

### BR-01 | *O conceito timbre no piano: perspectivas de cinco pianistas pós-graduandos* (SciELO)
**Fonte:** https://www.scielo.br/j/rv/a/gnNvfXDZF8ZNQXGKmkSYzxy/?lang=pt  
**Tipo:** pesquisa qualitativa de música/percepção; **NÃO é um experimento de mobilidade de ponte**.  
**Resultado:** discute ataque, corpo, extinção e ruídos de interação mecânica além do espectro estacionário, com entrevistas de pianistas.  
**Conseqüência V4:** orientar testes F9 sobre “parece piano elétrico”, qualidade do ataque e corpo, sem fazer inferência de massa/rigidez física a partir da opinião isolada.

## 11. Convergências transnacionais que mudam decisões de arquitetura

### C1 — não há um único “martelo isolado” universal
Japão (Yanagisawa/Nakamura), Canadá (Birkett/Vyasarayani), EUA (Russell), Estônia (Stulov) e Suécia (Askenfelt) concordam que duração, velocidade, contato e propriedades materiais alteram o transiente. **Conclusão de arquitetura:** uma lei mínima unilateral é excelente para ensaio de energia, mas a classe de martelo deve permitir estado de histerese e retorno da haste/ação, sem force pulse artificial. Não afirmar que todas as fontes exigem necessariamente o mesmo modelo específico.

### C2 — ponte e tampo são uma impedância dinâmica espacial e frequentemente multidirecional
Japão (Nakamura), Alemanha (Plath), Itália (Corradi), França (Ege/Boutillon), Reino Unido (Miranda Valiente) e Suécia/Alemanha (Wogram) demonstram dependência da montagem, ponto e frequência. **Conclusão:** interface V4 F5 deve ser um **porto vetorial físico** (força N, velocidade m/s e potência W) com 1 eixo na bancada e 2–3 direções no modelo de piano. Mantenha mobilidade complexa e fase, não apenas magnitude de EQ. Evitar usar como “verdade absoluta” uma placa ortotrópica com modos escolhidos por gosto.

### C3 — o tampo não só amplifica; ele seleciona/irradia de forma espacial
EUA (Giordano), França (Chaigne), Alemanha (Plath), Itália (Corradi), China (He et al.), Hungria (Jenei-Kulcsár/Fiala). **Conclusão:** medir/gerar campo normal de velocidade, incl. fase, aplicar radiação do ar em posições físicas e registrar diretividade; **não irradiar a reação em apoio fixo como se fosse uma superfície inteira**.

### C4 — adicionar cordas muda até o próprio tampo
Nakamura (Japão, 1993) e Corradi/Plath (Itália/Alemanha) mostram diferença estrutural entre montagem sem cordas, pontes, nervuras e instrumento em uso. **Conclusão:** depois da F8, rodar **recalibração obrigatória F3/F4/F5/F6/F7**, não assumir que tudo continua igual ao banco de 1 corda.

### C5 — o ataque acústico NÃO está garantido pela força de contato
A física do feltro pode gerar um pico maior, mas o som emitido pode continuar fraco em altas frequências se a mobilidade, a área radiante e a fase forem inadequadas. **Conclusão:** criar canais simultâneos de diagnóstico: compressão F_h(t), velocidade da corda no golpe, força/v na ponte, mapa de v da placa e p no microfone; comparar suas transformadas e envelopes de 0–10, 10–80 e 80–400ms com dados instrumentais.

## 12. Matriz de transições e novos experimentos recomendados

| Interface V4 | Fonte-âncora para estudo integral | Variáveis a registrar | Teste que deve falhar se a física estiver incorreta |
|---|---|---|---|
| **AJ23 F2→F3**: solver corda | Nakamura 1992, Chabassier 2014 | f_n, inarmonicidade, perda por parcial, deslocamento m, energia J | malha/refino muda o espectro ou cria energia |
| **AJ34 F3→F4**: contato martelo | Yanagisawa/Nakamura 1984, Birkett 2013, Stulov 1995, Vyasarayani 2009 | tempo/força de contato, δ, F_h, velocidade martelo, dissipação | contato cria energia, força atrativa sem feltro, perde reação da haste |
| **AJ45 F4→F5**: corda–ponte | Wogram, Miranda Valiente 2024, Nakamura 1993 | vetores F/v, Z(f), Y(f), fase, potência | modo bloqueado responde como ponte livre, ou trabalho sem reação |
| **AJ56 F5→F6**: ponte–tampo | Corradi 2010/2017, Plath 2019, He 2024 | geometria e pontos de ponte, M/K/D, modos, v(x,y) | placa sem ponte e com ponte produzem exatamente a mesma mobilidade |
| **AJ67 F6→F7**: placa–ar | Giordano 1998, Jenei-Kulcsár 2023, Ege 2013 | pressão Pa, v normal m/s, p/v(f), distância, fase | placa silenciosa produz som, radiação não varia com observador |
| **AJ78 F7→F8**: uníssono e realimentação | Nakamura 1981, Miranda Valiente una corda 2024, Weinreich | 2/3 cordas, contatos, deslocamento de ponte comum, batimentos | mixagem independente é indistinguível de sistema físico compartilhado |
| **AJ89 F8→F9**: audição | Aalto/Bank, SciELO Brasil, estudo acústico completo | ataque pp/mf/ff, picos, batimentos, decay e reconhecimento | "piano elétrico" recebe status GO sem correção física |

**Prioridade de leitura integral antes de escrever a próxima peça de DSP:** JP-02 (feltro), CA-01/02 (ação/haste), UK-01 (condição móvel), IT-02/DE-01 (montagem do tampo), US-02/HU-01 (radiância). Esses trabalhos têm dados ou métodos concretos que atacam nossos erros históricos.

## 13. Riscos de interpretação encontrados

1. A literatura de um **piano vertical** não deve ser tratada como modelo medido de um **cauda** e vice-versa.
2. Medir contato contra **sensor rígido** não reproduz automaticamente martelo contra **corda vibrante**.
3. Não comparar p/v em **posição de mic desconhecida** a outro artigo com posição e baffle diferentes.
4. Não copiar coeficientes e curvas de instrumentos de fabricantes diferentes como se fossem um único piano.
5. Não concluir que **16 modos** bastam: convergência de ponte/placa/radiação são problemas distintos.
6. Não somar **WAVs de notas separadamente sintetizadas** como prova de um tampo comum.
7. Não extrapolar experimento de feltro em um nível de força para todas as notas/velocidades.
8. Se uma tese/resumo indica possível alternativa mais simples, a hipótese só vale após medir **o erro acústico e físico** num caso de interesse; não aprovar simplificações pela economia de CPU.

## 14. Decisão de pesquisa

**Sem necessidade de novo motor neste pedido.** A literatura agora mostra explicitamente os mecanismos que devem ser ensaiados **entre cada fase** e reforça o plano F0–F13 com retroações **F3↔F4↔F5↔F6↔F7↔F8**. A primeira próxima implementação, quando solicitada, deve ser um **banco de forças/velocidades em SI para corda com apoio móvel passivo** e provas de energia, não um novo timbre arbitário.

**Fontes secundárias de consulta:** [Plano Mestre V4](PIANO_V4_PLANO_MESTRE_MODELAGEM_FISICA_COMPLETO_2026-11-23.md), [Bibliografia 18 lacunas](PIANO_V4_REFERENCIAS_TODAS_AS_18_LACUNAS_2026-11-23.md), [Auditoria de prontidão](PIANO_V4_AUDITORIA_FINAL_PRONTIDAO_2026-11-23.md).
