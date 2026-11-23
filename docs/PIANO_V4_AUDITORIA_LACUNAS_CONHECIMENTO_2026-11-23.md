# PIANO V4 — AUDITORIA DAS LACUNAS DE CONHECIMENTO E DAS INCERTEZAS

**Pesquisa aprofundada — 23 de novembro de 2026**
**Responsável pelo produto:** Stage Synth — piano por modelagem física exclusivamente.
**Status:** estudo, sem aprovação auditiva e sem integrar alteração de áudio.
**Referência de código verificada:** PR #39, branch \`research/piano-v4-restart-physical-20261123\`, baseada na \`main\` estável v1.12.8 (commit 626f5089). PR #37 (E2/E3) encerrada sem merge após reprovação do timbre.

## 1. Diagnóstico de epistemologia: o que "sabemos" quer dizer?

A literatura estabelece fenômenos **gerais** do piano; isso NÃO dá os parâmetros necessários para um piano específico. Para cada afirmação separaremos:

- **F — fato da literatura** (observado em experimento, qual piano, método, faixa e condição).
- **G — geometria conhecida do modelo** (código determinístico, não necessariamente igual ao instrumento).
- **H — hipótese de engenharia** (parâmetro escolhido para teste, ainda sem confirmação).
- **M — medição do nosso piano de referência** (ainda inexistente para a nova V4).
- **E — evidência auditiva controlada** (ainda inexistente para a V4).

Uma nota passar em testes matemáticos mostra estabilidade, **não semelhança auditiva**. A V4 atualmente só demonstra uma **corda rígida transversal com martelo reativo** e parâmetros ilustrativos. Não há ponte móvel, placa real, ar, um instrumento-alvo identificado, múltiplas cordas por nota nem som V4 validado. **176/176 testes anteriores não certificam timbre.**

## Bibliografia por lacuna — cobertura K01–K18

A auditoria foi acompanhada de uma [**bibliografia anotada específica para todas as 18 lacunas**](PIANO_V4_REFERENCIAS_TODAS_AS_18_LACUNAS_2026-11-23.md), com 2–5 referências por tópico, instituições/anos/tipos, contribuições, limites e experimentos que ainda faltam. **Encontrar referência não é o mesmo que identificar parâmetros físicos do piano-alvo**. Os artigos foram classificados pelo escopo; parte da leitura integral de publicações pagas ou PDFs fica pendente. Os códigos do motor não foram alterados.

## 2. Matriz priorizada: o que ainda NÃO sabemos

Critérios de prioridade: **P0 = bloqueia C4 acústico convincente**, **P1 = importante logo após C4**, **P2 = refinamento ou pesquisa específica do registro**. A prioridade não implica que a causa tenha sido comprovada; cada hipótese precisa ser falsificável.

| ID | Prioridade | Lacuna de conhecimento REAL | Evidência que já existe fora do projeto | Como medir ou testar / critério |
|---|---|---|---|---|
| K01 | **P0** | **Qual piano acústico exato estamos imitando?** Marca, modelo, comprimento, ação, estado de afinação/voicing, microfones, sala e dinâmica das gravações. | Fabricantes usam técnicas diferentes. Gravações sem metadados não permitem atribuição física. | Identificar um piano-alvo e criar inventário com licença, condições de captura e três tomadas por dinâmica. **SEM atribuir metadados inexistentes aos WAV American/Japanese/Felt/Upright.** |
| K02 | **P0** | **Velocidade real do martelo versus tecla MIDI** para C4 pp/mf/ff, massa efetiva e perdas na ação. | KTH mede cronologia da ação; PNAS 2025 observa movimentos/ruídos perceptíveis. | Curva key/MIDI→m/s por instrumento, câmera ou sensor, velocidade e contato com incerteza. Testar dinâmica sem equalizar depois. |
| K03 | **P0** | **Força do feltro dependente da HISTÓRIA**, sua histerese/viscoelasticidade, compressão e efeito da haste flexível. | Giordano & Winans, JASA 2000; Stulov 1995/2004; experimentos de força dinâmica. | Registrar força/tempo/deformação da batida real, ciclos compressão–recuo, fase e dissipação; comparar duas leis físicas com dados independentes. Não presumir que \`F=kδ^p\` basta. |
| K04 | **P0** | **Geometria e perdas de C4 reais:** comprimento, diâmetro, material, tensão, inarmonicidade, posição do golpe, torção e amortecimento por parcial. | Equações de cordas rígidas e dados de construção conhecidos; exemplos em outros pianos não bastam. | Medir a escala C4, espectro de vibração, \`f_n\` e \`T60_n\`; contrastar previsão da corda V4 com medição. |
| K05 | **P0** | **Condição física correta do apoio na ponte** (não fim fixo), força, deslocamento e mobilidade complexa por frequência. | Miranda Valiente et al. JASA 2024 compararam FE, 5 modos, Kelvin–Voigt e apoio rígido; alteram a dinâmica da corda, decaimento e força na ponte. | Medir mobilidade \`Y_bridge(f)=V_bridge(f)/F_bridge(f)\` (m/(N·s)), fase e impedância no ponto C4, em duas direções se possível; energia recíproca. |
| K06 | **P0** | **Tampo real**: espessura, espécies, ortotropia, nervuras, crown, downbearing, rigidez, condições do aro, amortecimento por modo e sua área ativa. | JASA 2013 e JSV 2013 mostram localização/variação espacial; fabricação e suporte influenciam mobilidade. | Mapa de aceleração ou mobilidade em múltiplos pontos, sob excitação conhecida. Ajustar modelo com **pontos de validação não usados no ajuste**. |
| K07 | **P0** | **Transferência tampo → pressão no ar** por localização, frequência e orientação, incluindo tampa/aro/radiação traseira e sala. | Estudos de radiação espacial e transfer path; em um Bösendorfer específico a tampa teve importante contribuição nas altas frequências. | Medir \`P_mic(f)/F_bridge(f)\` em posições registradas + mapa de painel e condições da tampa. Separar instrumento de reverberação de sala. |
| K08 | **P0** | **Por onde a 'batida' desaparece?** Ainda não temos canais separados de força feltro, energia da corda, força/velocidade na ponte, velocidade na placa, pressão, ruídos de ação. | A falha E3.4: dobrar a força do feltro quase não modificou a saída relativa do painel. | Um ensaio C4 com os mesmos marcadores de tempo e nível, séries de 0–10/10–80/80–400 ms, sem efeito nem compressão; localizar o gargalo por etapa. |
| K09 | **P0** | **Como testar sem confundir volume/afinação/microfone com realismo?** Critérios perceptuais ausentes. | PNAS 2025 e literatura de psicoacústica mostram impacto de gestos/ruídos e condições de escuta. | Protocolo A/B/X nivelado, identificado apenas depois, C4 pp/mf/ff, 3 repetições, notas isoladas; registro da avaliação de escuta do titular. |
| K10 | **P1** | **Como três cordas de C4 e duas polarizações se acoplam ao mesmo apoio?** Mistuning, contato simultâneo e modos coletivos versus soma de arquivos. | Weinreich JASA 1977: bridge admittance e polarizações explicam batimentos e aftersound. | Medir cada corda + uníssono, \`T60\` inicial/final e batimentos; simular acoplamento efetivo com compartilhamento de energia. |
| K11 | **P1** | **Ruídos da ação e dos apoios no ataque**, origem, espectro, contribuição e velocidade da tecla: tecla no fundo, escapamento, martelo retornando, abafador. | PNAS 2025 relaciona parte dos ruídos da tecla a percepção; técnicos documentam alinhamento/mating. | Separar transientes com sensor mecânico/mics e teste controlado. Implementar só contato/colisão física confirmada, **nunca layer de click gravado ou ruído arbitrário**. |
| K12 | **P1** | **Afinação, alinhamento e harmonização (voicing)**: influência do encontro simultâneo dos martelos com todas as cordas, forma do feltro, regulagem, estado técnico. | Piano Technicians Guild, Yamaha, práticas de preparo de martelos. | Ficha por nota das condições; registrar estado antes de medições; separar ajustes de construção dos algorítmicos. Qualquer trabalho na ação deve ser de técnico. |
| K13 | **P1** | **Pedais e abafadores reais**: contato da cabeça do abafador com cada parcial, cronologia de liberação/assentamento, reação simpática dependente de registro, una corda/sostenuto. | Lehtonen et al. JASA 2007: CC64/acoplamento impacta diferente médios, graves e agudos, batimentos e dupla cauda. | Medir C4 sustain on/off, tecla solta/pressionada, pedal parcial, repetições; adicionar só após C4 isolado sem pedal. |
| K14 | **P1** | **Comprimento secundário das cordas e duplex scaling:** o trecho fora da escala principal e seus abafamentos podem transmitir energia. | JASA 2024 considerou explicitamente segmentos duplex livres e amortecidos. | Inventariar desenho do piano-alvo e comparar com/sem segmento no modelo; não pressupor que todo piano o utiliza da mesma maneira. |
| K15 | **P1/P2** | **Vibrações longitudinais das cordas**, especialmente phantom partials no grave e acoplamento não linear transversal→longitudinal. | Bank & Sujbert JASA 2005; Etchenique/Collin/Moore JASA 2015. | Priorizar quando avançarmos a C2/C3; identificar picos que não são parciais transversais e verificar escala em dinâmica. |
| K16 | **P2** | **Tampa, aro, quadro, caixa, superfícies de fundo e acústica do ambiente**: contribuições mensuradas em diversos instrumentos e frequências. | Operational transfer path analysis de um Bösendorfer 280VC-9 encontrou maior contribuição da tampa nas altas frequências **nesse piano**. | Identificar caminhos com acelerômetros e mics; replicar em outro piano antes de generalizar. |
| K17 | **P2** | **Maturação, umidade, temperatura, desgaste, alteração de feltro/madeira ao longo do tempo.** | PTG e fabricante documentam regulagem e voicing periódicos, variação de material. | Registrar ambiente e condição física, repetir ensaios em sessões distintas; não inferir "aging" mágico de qualquer áudio isolado. |
| K18 | **P2** | **Otimização 32–64 martelos reais e um tampo compartilhado** sem perder a física ou estourar o orçamento de CPU. | CI Node antigo mediu versões E2/E3 com modelos simplificados; não existe benchmark V4 real em PC/Android. | Só depois de aprovação auditiva C4: perfil AudioWorklet com latência, GC, underruns e pedal, 32/48/64 contatos. |

### Lacunas estruturais do CÓDIGO V4.0, não só da literatura

- \`StiffStringHammerV4\` tem **uma corda transversal**, martelo com lei de potência **sem histerese** e **extremidade simplesmente apoiada/fixa**. A função \`bridgeShearForceN\` calcula reação em apoio rígido — **não é ponte móvel nem pressão acústica**.
- A tensão (~598 N), massa modal (~1,76 g), L=0,62m, r=0,48mm e martelo de 8g são **parâmetros geométricos ilustrativos**, não evidência de escala de C4 em piano identificado.
- Há 32 modos de corda dispersiva; não há polarização ortogonal, longitudinal, movimento de corpo/coroa, réplicas de corda do mesmo uníssono, action noise nem modificação da resposta acústica pelas condições de contorno.
- Os testes de conservação e afinação foram aprovados, mas **nenhuma waveform da V4 foi homologada em escuta**. Não produzir marketing de piano nem escalas a partir da V4.0.

## 3. Novidades científicas desta segunda investigação

### 3.1 Feltro real tem memória e a haste do martelo influencia o golpe

Giordano & Winans, *JASA* (2000), estudaram aceleração do martelo, compressão do feltro e flexão da haste. Mostraram que a transmissão de força da borda ao núcleo do feltro e a flexão podem afetar a aparente lei força/deformação. Stulov, *JASA* (1995) e *Acta Mechanica* (2004), mostra modelos **viscoelásticos histeréticos**, com dependência do histórico. As grandezas de um ensaio com martelo atingindo sensor rígido podem ser diferentes das de martelo atingindo uma corda — não copiar uma curva fora do contexto.

**Conseqüência:** o V4 deve tratar \`k\`, \`p\`, massa do martelo e amortecimento do feltro como **incertos**, sujeitos a medição; investigar haste de martelo como DOF adicional, sem introduzir click artificial.

Fontes:
- https://pubmed.ncbi.nlm.nih.gov/10790050/
- https://cir.nii.ac.jp/crid/1362262945923645952
- https://www.ioc.ee/~stulov/Acta2004.pdf
- https://www.jstage.jst.go.jp/article/jasj/40/11/40_KJ00001453633/_article/-char/en

### 3.2 Uma corda rígida TERMINADA por uma ponte real não é apenas uma corda de extremidade fixa

P. Miranda Valiente, G. Squicciarini e D.J. Thompson, *JASA* (2024), contrastaram modelo FEM de tampo, cinco modos, amortecedor Kelvin-Voigt e apoio rígido. Relatam que a dinâmica de placa e do contato na ponte modificam **decaimento, força transmitida e vibração da área radiativa**. Incluíram segmento duplex livre/amortecido. Um outro estudo (2017) mediu evolução do tampo em fases de fabricação.

**Conseqüência:** antes de acoplar arbitrariamente "N modos" à V4, definir mobilidade/impedância no ponto C4, unidade, fase, perdas e referência geométrica. Se possível, obter a função complexa \`Y(f)\` e validar em frequências não usadas na identificação.

Fontes:
- https://pubmed.ncbi.nlm.nih.gov/38742965/
- https://www.sciencedirect.com/science/article/pii/S0003682X17303444
- https://www.sciencedirect.com/science/article/pii/S0022460X13002472

### 3.3 O tampo não é o único emissor

Em *Operational transfer path analysis of a piano*, feita com **um Bösendorfer 280VC-9**, o tampo foi o contribuinte principal e a **tampa** tornou-se o maior contribuinte nas frequências altas consideradas nesse experimento. Não extrapolar essa conclusão para todo instrumento, sala e posição de microfone. A posição do ouvinte e da tampa também altera o campo sonoro.

**Conseqüência:** um radiador que ignore totalmente tampa/aro/ar abaixo da placa pode falhar no ataque mesmo com cordas e martelo corretos; mas **não** adicionar tampa até possuirmos dados experimentais e uma placa defensável.

Fonte: https://www.sciencedirect.com/science/article/abs/pii/S0003682X1730871X

### 3.4 As vibrações longitudinais criam harmônicos "fantasmas" especialmente nos graves

B. Bank & L. Sujbert, *JASA* (2005), mostraram modelo de geração de componentes longitudinais e *phantom partials* a partir do acoplamento com vibrações transversais. Etchenique, Collin & Moore, *JASA* (2015), testaram experimentalmente parte da dependência quadrática dessa excitação. Esses fenômenos são **mais prioritários para C2/C3 que para um primeiro C4**.

Fontes:
- https://pubmed.ncbi.nlm.nih.gov/15898667/
- https://pubmed.ncbi.nlm.nih.gov/25920829/

### 3.5 Os ruídos e movimentos da ação podem alterar a percepção do ataque

O estudo *Motor origins of timbre in piano performance*, *PNAS* (2025), encontrou relações entre movimentos de tecla, ruídos de início/retorno e percepções como clareza, peso e brilho. A PTG documenta a preparação técnica de **mating** (encontro correto de martelo e cordas), nivelamento e alinhamento. Não afirmar que qualquer ruído somado artificialmente será percebido como piano.

Fontes:
- https://doi.org/10.1073/pnas.2425073122
- https://my.ptg.org/viewdocument/focusing-the-hammer-on-the-string-1?CommunityKey=16e8f8dc-7b6a-43b3-aa35-a82288dd8cbf&tab=librarydocuments

### 3.6 O sustain não é só manter notas tocando

Lehtonen, Penttinen, Rauhala & Välimäki, *JASA* (2007), analisaram como pedal de sustain afeta decaimentos parciais, batimentos e ressonância simpática; o efeito depende do registro. Weinreich, *JASA* (1977), explicou papel da admitância da ponte no acoplamento das 2/3 cordas por tecla e na chamada *aftersound*.

Fontes:
- https://pubmed.ncbi.nlm.nih.gov/17927438/
- https://www.speech.kth.se/music/5_lectures/weinreic/strings.html

### 3.7 Materiais/construção se traduzem em grandezas mensuráveis

Yamaha documenta seleção de abeto, nervuras, coroa do tampo, pontes, preparação e voicing de martelos. PTG descreve afinação/regulagem/harmonização. Esses relatos são **sobre práticas documentadas dos próprios fabricantes/técnicos**, não uma licença para extrapolar densidade, qualidade e dureza a todos os pianos.

Fontes:
- https://uk.yamaha.com/en/musical-instruments/pianos/explore/musical-instrument-guide/piano/manufacturing/
- https://www.yamaha.com/en/musical_instrument_guide/piano/manufacturing/manufacturing005.html
- https://www.ptg.org/ptgmain/piano/care/servicing
- https://pubmed.ncbi.nlm.nih.gov/23556610/

## 4. Fatores ocultos, vieses e riscos de conclusões erradas

1. **Problema inverso subdeterminado:** um único WAV de microfone contém a soma de muitos mecanismos; não identifica de maneira única massa, feltro, corda, ponte, radiação, sala e microfone. Este é um argumento de engenharia: os graus desconhecidos excedem as medições independentes. A solução é **multissensor/força/velocidade/pressão**, não apenas otimização de espectro.
2. **Confusão timbre × microfonação:** grave enfatizado, brilho e posição espacial podem mudar por posicionamento/tampa/sala. Comparações A/B só são comparáveis se condições de escuta e captura forem conhecidas ou claramente qualificadas.
3. **Validação circular:** ajustar 15 notas e reportar erro nessas mesmas 15 notas não é validação independente. Separar notas/velocidades/posições/microfones **de treino e teste**.
4. **Dados sem licença/proveniência:** nenhuma gravação de terceiro deve entrar no código nem em repositório público sem direitos claros. Referências fornecidas pelo usuário podem ter procedência, instrumento e tipo de preparo desconhecidos: registrar \`UNKNOWN\`, não inventar.
5. **Efeito de um experimento isolado:** um Bösendorfer, uma Yamaha ou um martelo de artigo não determina todos os parâmetros físicos.
6. **Acerto numérico não é realismo:** erro 10⁻¹³ de balanço de energia é útil, mas a física pode estar equivocada se contato, materiais e condições de contorno forem inventados.
7. **Falso ganho em CPU:** reduzir de 32 para 8 modos pode tornar mais fácil rodar, mas não demonstra timbre; medir **fidelidade primeiro**, performance depois.
8. **Confundir modelagem física pura com ausência de medição:** usar medições para **parametrizar e testar** leis físicas é compatível com síntese puramente física. O que está excluído é **reproduzir audio ou respostas impulsivas gravadas no motor**.

## 5. Próximo ciclo de estudos SEM nova implementação de som

### Pacote de estudo P0-A — ação/martelo/feltro
- Comparar quantitativamente Giordano & Winans (martelo/haste), Stulov (histerese), Askenfelt/Jansson (contato/time), Yamaha/PTG (voicing/mating).
- Preencher ficha de parâmetros por nota e dinâmica: velocidade real, contato, massa efetiva, dissipação, repetição, alinhamento de uníssono.
- Produzir uma tabela **\`medido | literatura de referência | hipótese V4 | não conhecido\`**; não preencher com números inventados.

### Pacote P0-B — escala C4 e terminação
- Determinar comprimento, diâmetro, tensão, B, perdas parciais do C4 real.
- Estudar fórmulas e medições de mobilidade/impedância complexa na ponte; contato com segmento duplex quando presente.
- Medir \`F_bridge\`, \`V_bridge\`, posição e fase para distinguir corda isolada de instrumento acoplado.

### Pacote P0-C — tampo e ar
- Identificar material, nervuras, posição do ponto C4, mapa vibratório e mobilidade por frequência.
- Distinguir modos abaixo/acima do regime de localização entre nervuras (limite dependente do instrumento; ~1,1 kHz foi documentado em um estudo, **não** é universal).
- Investigar radiação de tampo, tampa/aro e mic sem confundir acústica de sala com mecânica.

### Pacote P0-D — avaliação humana e controle
- Escolher instrumento-alvo real e um protocolo de captura/licença.
- Definir medidas de ataque, brilho por faixa, razão espectral entre harmônicos, decaimento por parcial, nível, pitch e reconhecimento auditivo.
- Planejar teste A/B sem identificação do arquivo e com a mesma cadeia de reprodução. Se o usuário não reconhecer piano, a V4 **não avança**.

## 6. Dados reais disponíveis para iniciar a validação

Após o levantamento das lacunas, foram identificadas fontes com medições externas verificáveis, catalogadas em [`PIANO_V4_CATALOGO_DADOS_EXPERIMENTAIS_MEDICOES_2026-11-23.md`](PIANO_V4_CATALOGO_DADOS_EXPERIMENTAIS_MEDICOES_2026-11-23.md):

- **Plath/Universidade de Hamburgo (Zenodo, ISMA 2019):** impacto **tecla–keybed** em N, aceleração próxima à ponte em m/s² e pressão binaural em Pa, canais sincronizados 50 kHz. **Não mede diretamente martelo–corda**.
- **BiVib (Zenodo 2019):** dois Yamaha Disklavier (cauda e vertical), dez níveis MIDI e sinais de **vibração do teclado** mais som binaural. **Não é medição da ponte**.
- **Iowa/Steinway B:** gravações pp/mf/ff com referência de captação; **não contêm sensores de força/placa**, e a sala não era anecoica.
- **Fontana et al. (2024):** dados de respostas perceptivas sobre localização de sons mecânicos de piano vertical.

**Nenhum dado externo foi importado ou integrado**; avaliar licenças, metadados, volumes de dezenas de GB e eventuais versões posteriores antes de processamento. O catálogo não transforma uma gravação em instrumentação mecânica faltante.

## 7. Resultado e decisão para PR #39

**Resultado deste estudo:** a V4 está agora fundamentada por um **inventário de 18 lacunas**, referências multidisciplinares e testes correspondentes, sem alegar que a execução prática foi realizada. O **gargalo nº 1 do projeto não é CPU ou MIDI; é a identificação física dos mecanismos e sua transmissão até a pressão no ar sob condições audíveis e reproduzíveis**.

**Decisão:** não adicionar ponte, tampo, pedal, reverberação ou click por palpite. A PR #39 continua DRAFT. Não promover nenhuma nota como "piano acústico" sem C4 fisicamente fundamentado e reconhecido pela escuta. A \`main\` v1.12.8 (A/B/C/D/Clássico, efeitos, MIDI, interface e dados) permanece inalterada.
