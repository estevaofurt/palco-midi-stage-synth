# STAGE SYNTH V4 — PLANO MESTRE COMPLETO DE MODELAGEM FÍSICA DO PIANO ACÚSTICO

**Status:** PLANO DE ENGENHARIA — **nenhum novo motor deve ser implementado como consequência automática deste documento**.  
**Data:** 23/11/2026 · **Branch de pesquisa:** research/piano-v4-restart-physical-20261123 · **PR:** #39, draft.  
**Produto atual na main verificada:** Stage Synth **v1.12.10**, commit 1129e2e46a8a8bc373b43c1284b668ceea3e05ca. A pesquisa V4 deriva da v1.12.8 e está 2 commits atrás da main; sua futura integração requer atualização de base e novas regressões.  
**Aprovação auditiva V4:** NÃO realizada. **Status de release:** NO-GO.

> O propósito deste plano é impedir a repetição da E2/E3: modelos que conservavam energia, mas soavam como sintetizadores ou piano elétrico. **Matemática correta, número elevado de modos, CI verde e FFT visualmente promissora não substituem uma nota reconhecível de piano acústico.**

## 0. Contrato do produto (não negociável)

1. **Som sintetizado exclusivamente por fenômenos físicos calculados.** Não utilizar reprodução de amostras, wavetable obtida de gravações, SoundFonts, ataques gravados, ruído de martelo colado como áudio, respostas impulsivas gravadas em convolução, filtros aprendidos que reproduzam áudio ou camadas que contornem a mecânica. 
2. Gravações, medições de mobilidade e pesquisas externas podem **informar parâmetros e validar** o modelo; não entram como áudio reproduzido ou como IR gravada processada diretamente pelo gerador. Um **modelo modal passivo com massas/rigidezes/amortecimentos ajustados por medições** continua físico, desde que seus parâmetros sejam interpretáveis, rastreáveis e sua resposta não seja um playback de IR ou de samples.
3. Preservar o Stage Synth já publicado: A/B/C/D/Clássico, motor opcional **E com WAVs locais** (módulo separado da V4, existente na v1.12.10), presets, MIDI/CC64, efeitos, UI e arquivos privados. A V4 deve permanecer 100% física **mesmo que o produto possua outro motor de amostras**.
4. **Não alterar a main nem publicar como novo piano** até concluir os gates físicos, acústicos, auditivos e de regressão; PR #39 continua draft.
5. Alvo inicial de investigação: **piano de cauda acústico contemporâneo**, C4 (MIDI60; f nominal 261,625565 Hz para A4=440 Hz). Marca/modelo acústico específico ainda não escolhido nem medido. Não atribuir propriedades Steinway/Yamaha/Fazioli aos números ilustrativos da V4.
6. Cada limitação será registrada, e resultados negativos também. Não usar termos “aprovado”, “fiel”, “acústico convincente” ou “100% calibrado” sem sua prova correspondente.

### 0.1 Pergunta de engenharia
**Como um impulso produzido por uma ação real se converte, por uma sequência de sistemas mecânicos acoplados, em um campo de pressão no ar com ataque, brilho, dinâmica, batimentos, corpo e decaimento perceptualmente típicos de um piano de cauda?**

## 1. Arquitetura: duas implementações, uma física

### 1.1 Laboratório de referência — simulação offline de alta fidelidade

- Solver de **elementos finitos/diferenças de energia** para cordas tensionadas com rigidez; condições de contorno de ponte móvel.
- Sistema de contato unilateral martelo–corda com **não linearidade, histerese/viscoelasticidade passiva**, haste flexível quando houver necessidade demonstrada.
- Ponte distribuída e tampo **ortotrópico com nervuras**, massa e rigidez geométricas, condições de apoio e perdas materiais.
- Modelo acústico espacial no ar; iniciar com integral de Rayleigh **apenas se o pressuposto de placa em defletor rígido estiver explicitamente aceitável**; usar modelo acústico com difração/contorno e reação radiativa para confronto quando necessário.
- Tamanho de passo, malha e ordem modal escolhidos **por convergência**, não pelo custo do navegador.
- Gera sinais separados: força do martelo, compressão, deslocamento da corda, carga/velocidade da ponte, campo vibratório do tampo, potência radiada e pressão nos observadores. Em cada etapa manter unidades SI e leis de potência/energia.
- O resultado é a **verdade de referência numérica do nosso modelo**, NÃO a verdade de um piano real até calibração e audição.

### 1.2 Motor real-time — redução física controlada, somente depois da aprovação acústica

- Partir das matrizes, modos, parâmetros e acoplamentos físicos aceitos pela referência, com redução modal/ordem de sistema **passiva e comprovável**.
- Compartilhar o **mesmo estado de ponte/tampo entre todas as cordas**, sem renderizar notas isoladas para somá-las como se fossem um piano acoplado.
- Trabalhar em AudioWorklet (ou tecnologia equivalente no alvo), respeitando buffers de tamanho efetivamente recebido, escalonamento, memória e restrições de baixa latência. **Não pressupor sempre bloco fixo** nem ignorar GC/underruns.
- O alvo 32/48/64 vozes, CPU e latência fica **posterior** à qualidade acústica.
- A implementação rápida deve explicar as aproximações por mecanismo e demonstrar o erro frente à referência física, não apenas ter som parecido com um sample.

**Regra:** não manter duas teorias sonoras diferentes. O modelo otimizado é uma aproximação validada da mesma física.

## 2. Diagrama causal de arquitetura

\`\`\`mermaid
flowchart TD
  CTRL[Tecla / MIDI / pedal, gesto]
  ACT[Ação mecânica: alavancas, escape, repetição]
  HAM[Martelo: haste, massa, feltro viscoelástico]
  STR[Grupo de 1–3 cordas, duas polarizações + longitudinal se necessário]
  BR[Interface ponte: deslocamento e força conjugados]
  PL[Tampo ortotrópico: madeira, nervuras, contorno, perdas]
  AIR[Radiação para o ar, radiação traseira e tampa quando validadas]
  OUT[Pressão acústica em posição definida]
  CTRL --> ACT --> HAM
  HAM <-->|força / compressão / reação| STR
  STR <-->|força / velocidade / trabalho| BR
  BR <-->|força / velocidade / trabalho| PL
  PL <-->|velocidade de superfície / carga radiativa| AIR
  AIR --> OUT
  DAMP[Abafadores / pedais / cordas simpáticas] <--> STR
\`\`\`

**Interface mecânica não é um cabo de áudio.** Mecanismos adjacentes trocam esforços e movimentos recíprocos. A carga do tampo modifica o movimento da ponte e a vibração das cordas; não basta calcular force em uma corda fixa e “enviá-la” a osciladores de tampo.

## 3. Modelo físico por subsistema

### 3.1 Controle/ação e martelo

**Inputs:** key position/velocity em m/m·s⁻¹ ou MIDI com curva identificada; estado do pedal; geometria, massas/inércias e atrito de articulações.  
**Estados:** tecla e alavancas, escape, haste/rotação, deslocamento e velocidade do martelo; eventos de liberação/captura.  
**Output ao contato:** velocidade livre do martelo em m/s, energia cinética em J, posição normal em m.  
**Fase inicial:** em bancada, definir a **velocidade física inicial do martelo** como condição de contorno; ainda não modelar a ação inteira. A velocidade MIDI não é m/s.  
**Fase posterior:** mecanismo com escapamento/repetição e sensores, comparação de pp/mf/ff, captura, ruídos mecânicos apenas se derivados de contatos físicos modelados.

**Martelo/feltro:** deformação unilateral \`δ = x_h - u_strike\`, compressão \`δ_+=max(0,δ)\`. Energia elástica ilustrativa \`U(δ_+)=k δ_+^(p+1)/(p+1)\`; a força sem perdas é a derivada. **Isso é apenas um ponto de partida**, não a lei final do feltro. Estudar leis viscoelásticas com memória e deformação dependente da história (Giordano/Winans; Stulov). Escolher variáveis internas de relaxação ou elemento Kelvin/Maxwell não linear **que garantam produção de entropia não negativa**, e validar em dados de compressão e restituição. A haste flexível pode ser viga de Timoshenko quando estudos/ensaios exigirem. Não produzir “click” de ataque fora dessa cadeia.

**Gate local:** força normal nunca atrativa, sem contato ⇒ força nula, ganho energético sem origem impossível, variação física verificável com velocidade, contato medido/modelado, convergência temporal; perdas medidas como energia dissipada, não como redução ad hoc de amplitude final.

### 3.2 Cordas: geometria, rigidez, polarização, amortecimento

**Estados:** deslocamentos e velocidades de cada corda (vertical e horizontal; longitudinal adicionado quando justificado), eventual deformação axial, massa linear e rigidez de flexão.  
**PDE escalar inicial de corda tensa rígida:** \`mu*u_tt = T*u_xx - EI*u_xxxx - D(u_t) + f_h(x,t)\`, com condições de suporte adequadas; \`mu = rho*pi*r²\`, \`EI = E*pi*r⁴/4\` para fio circular homogêneo. Para cordas revestidas, massa linear, rigidez e dissipação dependem de núcleo/enrolamento e **não** devem ser calculadas como se o bordão fosse fio maciço.
**Inarmonicidade ideal com apoios articulados:** \`f_n = (n/(2L))*sqrt(T/mu)*sqrt(1 + B*n²)\`, \`B=pi² EI/(T L²)\`; usar apenas como cheque do banco simples, NÃO impor mesma fórmula quando a ponte se move ou a geometria é variável.

**Discretização de referência:** escolher explicitamente FE 1D com continuidade suficiente para a energia de flexão (ex.: Hermite para termo EI) **ou** diferenças finitas passivas adequadas. Matriz física \`M_s,C_s,K_s\` simétrica onde pertinente, \`M_s>0\`, \`K_s>=0\`, \`C_s>=0\`, contatos e restrições introduzidos por forças generalizadas de trabalho recíproco. Não escolher número fixo de modos sem avaliar espectro e convergência da força de martelo.

**Tipos por registro:** grupos de 1/2/3 cordas conforme **escala do piano-alvo**; cordas gravíssimas com enrolamento; distribuição de perdas/polarização e localização física. Martelo de uma nota normalmente encontra simultaneamente várias cordas da mesma nota: forças por contato individual, compartilhamento do estado de ação e massa de martelo, diferenças reais de alinhamento.

**Observáveis:** vibração no impacto, forças na ponte, frequência/inharmonicidade de cada parcial, polarização, beat rate, decay por parcial, energia no string group.

**Gate:** comparação de f_n/B/perdas com medidas ou intervalo físico declarado; estabilidade e conservação de energia na corda isolada; mudança correta ao fixar/liberar apoio; sem detune ou equalização escolhidos para “parecer piano”.

### 3.3 Ponte móvel e condição de contorno — PRIMEIRA REFORMA NECESSÁRIA NA V4

**Erro conhecido do protótipo atual:** o código \`research/piano-v4/stiff-string-hammer.mjs\` possui modos senoidais com as extremidades fixas e calcula \`bridgeShearForceN()\` como reação de um apoio imóvel. **Essa força não pode ser irradiada como se fosse uma ponte/tampo móvel.**

**Escolha de referência:** sistema mecânico conjunto com graus de liberdade de corda/ponte/tampo e restrições na conexão: deslocamento/velocidade do contato iguais nas direções transmitidas; força de ação e reação, trabalho igual e oposto. Para suportes FE, usar nós compartilhados ou restrições de Lagrange que conservem energia. Para solver modal, representar explicitamente o deslocamento do apoio por um campo de “lifting” e todos os termos de massa/rigidez associados, sem dupla contagem.

**Localização:** ponte principal, ponte grave, pinos e segmento secundário das cordas de acordo com o modelo-alvo; diferentes componentes de força (vertical/horizontal) quando necessários. **Não reduzir automaticamente a ponte a uma mola escalar.**

**Grandeza medida prioritária:** mobilidade mecânica complexa \`Y_bridge(f)=V_bridge(f)/F_bridge(f)\`, unidade (m/s)/N, com magnitude **e fase**, local e direção documentados. Uma ponte fisicamente passiva tem impedância/admitância compatível com dissipação não negativa, não uma curva de EQ escolhida.

**Gate:** teste isolado “ponte livre versus ponte rigidamente bloqueada”, reações coerentes, deslocamento/velocidade sem descontinuidade, energia total conservação/dissipação e respostas de mobilidade em frequências NÃO usadas na identificação.

### 3.4 Tampo harmônico e madeira

**Estrutura:** placa elástica aproximadamente ortotrópica, nervuras, pontes, espessura variável, crown/downbearing, fixação ao aro, massas e perdas. FE de referência com malha e materiais físicos, matriz \`M_p,K_p,C_p\`; efeito de montagem representado em condições de contorno. Um modelo de placa simples é permitido **como bancada experimental claramente incompleta**, mas a nota aprovada deve passar por uma representação com justificativa espacial e modal.

**Identificação:** ajustar geometria e parâmetros materiais usando medidas conhecidas; a parte dinâmica pode depois ser reduzida por autovetores/valores da matriz FE; cada modo deve carregar forma espacial e massa generalizada, nunca uma frequência livremente escolhida para moldar o espectro. As primeiras evidências são mobilidade de ponte e mapas de vibração em vários pontos.

**Gate:** convergência de malha, passividade, mobilidade nas diferentes regiões da ponte, formas modais/massa, amortecimento e teste de validação cruzada com pontos não usados no ajuste. A quantidade de modos será **consequência de convergência**, não “16 por parecer detalhado”.

### 3.5 Acústica do ar e observador

**Grandeza que queremos:** pressão \`p(x_mic,t)\` em Pascal em posições explícitas, derivada da **velocidade normal da área do tampo** e das condições acústicas externas.

**Modelo inicial de radiação:** integral causal/retardada de Rayleigh para placa em defletor rígido, **com hipótese de geometria expressa e comparação posterior com campo acústico de maior fidelidade**. Para grande piano aberto, tampa, difração/borda e ar frente/trás importam; métodos BEM/FEM de ar são candidatos para modelo de referência quando o pressuposto baffle falhar. Nenhum microfone virtual recebe diretamente \`F_h\` nem velocidade de um ponto de ponte.

**Acoplamento:** na referência completa considerar também potência radiada e reação acústica sobre o tampo; se o primeiro cálculo for **unidirecional**, declarar explicitamente a aproximação e NÃO contar energia radiada no balanço mecânico sem carga acústica real de retorno.

**Saídas:** pressão frente/trás, padrão direcional, potência radiada, velocidade de painel; output em 48 kHz com posição, distância e referência de ganho documentadas. Ambiente/sala inicialmente separado do instrumento; **não usar IR gravada para simular a sala**.

**Gate:** placa imóvel ⇒ pressão nula, deslocamento de microfone ⇒ mudança de fase/distância coerente, convergência da malha de radiação (N de patches) **e dos modos estruturais** separadamente, controle de aliasing, não criar radiador “de ponte inteira”.

### 3.6 Uníssono, ressonâncias, ação secundária e pedais

- **Primeiro C4 audível para avaliação:** incluir o **grupo de cordas da nota no piano-alvo**, provavelmente três no médio do piano de cauda, e suas duas polarizações, com mesma ponte/tampo. Uma única corda serve como teste mecânico, **não como prova de timbre final de C4**.
- Modelar diferença real de comprimento/tensão/frequência por corda, alinhamento de contato e mobilidade de ponte; deixar **batimentos e decaimento duplo emergirem do sistema acoplado**.
- Após C4 aprovado: bordões com massa variável, vibrações longitudinais, phantom partials, segmentos duplex quando presentes, abafadores reais com contato dissipativo, CC64, pedal parcial, sostenuto, una corda, ressonância simpática e ações de repetição.
- Os ruídos da tecla, escapamento, colisões de ação, martelo/haste e abafador são **contatos mecânicos físicos opcionais** a serem validados; não uma pista de ruído independente “para dar realismo”.

## 4. Identificação, materiais, dados e rastreabilidade

### 4.1 Três fontes possíveis de parâmetro
- **MEASURED:** medido em instrumento definido com instrumento/captura, unidade, método, incerteza e licença.
- **LITERATURE:** extraído de artigo/fabricante com autor, modelo de piano, condições e escopo; **não generalizar** para a V4.
- **ILLUSTRATIVE:** plausível e rotulado como hipótese, restrito a bancada, sujeito a análise de sensibilidade; nunca anunciado como “piano calibrado”.

### 4.2 Esquema obrigatório para registro de parâmetros — SPEC, não arquivo implementado
\`\`\`json
{
  "parameter_id": "string.C4.length_m",
  "component": "string",
  "unit": "m",
  "status": "unknown",
  "value": null,
  "uncertainty": null,
  "instrument": null,
  "source_type": "unmeasured",
  "source_uri": null,
  "measurement_protocol": "vibrating length from terminations",
  "valid_range": null,
  "validation_split": "not_assigned"
}
\`\`\`
- Campos numéricos sem evidência permanecem \`null\`. O protótipo atual (L=0,62m; r=0,48mm etc.) deve ser migrado como **ILLUSTRATIVE**, não como verdade física.
- **Nunca ajustar parâmetros ao mesmo conjunto usado para relatar validade.** Separar notas, velocidades, tomadas, microfones e condições de treino/validação/holdout.
- Guardar hash, versão e licença de dados **diagnósticos** sem colocá-los nos outputs do motor.

### 4.3 Fontes de dados candidatas
- **Plath/Zenodo:** impacto **tecla–fundo** em N, aceleração **próxima à ponte** em m/s² e pressão binaural em Pa, sincronizados; **não mede força do martelo contra a corda**.
- **BiVib/Disklavier:** vibração no **teclado** e áudio binaural, dez níveis de velocity; **não mede diretamente o tampo**.
- **Iowa/Steinway B:** notas pp/mf/ff em captação descrita, sem instrumentação mecânica completa, sala não anecoica.
- Outras medições de mobilidade/FE (Fazioli, literatura do tampo) servem para metodologia e ordens de grandeza, não para misturar geometrias incompatíveis como se fossem o mesmo piano.
- Primeiro conferir **direitos, instrumentos e canais**. Não baixar bibliotecas inteiras por padrão.

### 4.4 Dados mínimos que realmente precisamos para alegar calibração de C4
Identidade do piano-alvo; número de cordas C4; comprimentos/raios/tensão/posição do martelo (ou uma justificativa de identificação indireta com incerteza); curva de contato e velocidades de ataque; f_n, B, amortecimento por parcial; mobilidade ponte (módulo/fase) em ponto C4; resposta espacial do tampo e cadeia microfone; repetição pp/mf/ff. **Não existe hoje um pacote único completo medido no projeto** — sem ele somente alegar modelo físico plausível, nunca correspondência precisa a piano conhecido.

## 5. Métodos numéricos e conservação física

### 5.1 Formulação geral de acoplamento
Equações discretizadas em forma de energia para graus de liberdade da estrutura, em uma aproximação linear por trecho:
\`\`\`text
 M q_ddot + C q_dot + K q = F_contact(q, q_dot, z) + J^T lambda + F_ext
 C(q, q_dot, z) governam perdas materiais; lambda impõe restrições conjuntas.
 H = 1/2 q_dot^T M q_dot + 1/2 q^T K q + U_felt + H_internal
 Delta(H) + D_material + W_radiation = W_external   (acoplamento completo)
\`\`\`
**Nota de notação:** o \`C\` da matriz amortecedora e o operador de restrição serão tratados com símbolos diferentes no código final; a apresentação acima é um esquema, não contrato de API. **Ao usar radiação unilateral, não subtrair W_radiation sem modelar reação radiativa.**

### 5.2 Escolha de integrador
- Preferir midpoint implícito, variantes discrete-gradient/energy quadratization ou métodos passivos com prova/ensaio de balanceamento para contato não linear e mecanismos dissipativos; estabilidade com rigidez elevada e múltiplos contatos.
- Em contato unilateral, solução robusta de complementaridade ou raiz monotônica, tratamento de separação/recontato e estado do feltro; não impor força arbitrária de duração fixa.
- Pré-condicionadores, matrizes esparsas e solver implícito onde necessário; tolerâncias e resíduos por componente em unidades SI.
- FDTD/FE benchmark de convergência de discretização espacial e passo temporal com os mesmos parâmetros físicos. Verificar condicionamento, aliasing e estabilidade, sem usar amortecimento numérico excessivo como “melhoria de timbre”.
- Se dividir a integração em sub-sistemas, garantir **o mesmo fluxo de energia** nos dois sentidos a cada passo (integração port-Hamiltoniana/estrutura passiva ou correção iterativa convergida), não acoplar apenas pelo sinal de força/áudio.

### 5.3 Critérios numéricos iniciais (não perceptuais)
- **Energia:** com fonte desligada após o golpe, \`H + dissipação\` compatível com energia inicial; proposta inicial |erro relativo| ≤ 10⁻⁶ em ensaios especificados, com tolerâncias absolutas para estado quase silencioso. Não certifica realismo.
- **Unidades:** f em Hz, T e forças em N, deslocamento em m, velocidade m/s, massa em kg, pressão em Pa, potência W, energia J; contratos impedem confundir força de ponte com pressão.
- **Convergência:** verificar refinamentos de malha, modos, discretização de radiação, passo de tempo e precisão; tornar mais precisos os critérios após observar ensaios. Não aceitar “48 patches próximos a 192” como validação estrutural.
- **Amostragem:** comparar 44,1/48/96 kHz; oversampling somente nos subsistemas/contatos que exigirem, com redução de amostragem antialiasing de método matemático explícito.
- **Casos de borda:** martelo parado e afastado ⇒ saída nula; nenhuma massa negativa; feltro separado ⇒ sem contato; ponte travada ⇒ potência de interface nula; tampo imóvel ⇒ sem saída de superfície; damping positivo ⇒ energia não cresce; contatos múltiplos e repetição não injetam energia não contabilizada.

## 6. Validação acústica, física e auditiva

### 6.1 Instrumentação e sinais-alvo
Canais sincronizados do motor: evento da tecla, velocidade do martelo, força/pressão do feltro, deslocamento no ponto de golpe, energia de cada corda, força/v na ponte, campo de v da placa, pressão do observador; registrar estado de pedal. Calcular:
- tempo de contato, força máxima/impulso e rebotes;
- envelope de energia em **0–10, 10–80, 80–400 ms, 0,4–2 s** com alinhamento temporal de eventos e tratamento de sala/mic;
- frequência/inharmonicidade de parciais, distribuição de energia, onset e variação pp/mf/ff;
- taxas de decaimento de cada parcial e duas inclinações de decaimento para uníssono;
- batimentos por nota, cor tonal por registro, posição de escuta/diretividade;
- comparação de ruído mecânico por canal apenas se o fenômeno estiver fisicamente representado.

### 6.2 Evitar validação circular
- Não otimizar pelos WAVs de referência e depois relatar erro nos mesmos WAVs como demonstração de generalização.
- Uma medição C4 com dois mics só permite afirmações sob aquelas condições, e não de todas as salas.
- Separar **identificação física do mecanismo** (por sensor) de **escuta do produto**. Comparar áudio com referência e metadados; relatórios numéricos são auxiliares, não classificadores definitivos de piano.
- Teste auditivo: primeiro avaliação livre do titular, depois comparações A/B com nível, afinação e duração controlados, arquivos anonimizados quando útil. Registrar “parece piano elétrico”, “ataque amolecido”, “sustain sintético” como **falhas**, não como gosto irrelevante.
- Testes de usuário podem ser repetidos com pianistas/técnicos se disponíveis; se não houver esse painel, não afirmar validação profissional.

### 6.3 Definição de pronto para primeiro WAV de demonstração
**Somente após:** martelo + corda(s) + ponte móvel + tampo espacial + radiação do ar **na mesma cadeia causal**, passes de energia/convergência e registro de parâmetros/proveniência. Este WAV será **experimental** até o titular reconhecer sonoridade de piano. **NÃO gerar demonstrações de escala/acorde como prova de que C4 foi aprovado.**

## 7. Plano de desenvolvimento em gates, entregáveis e bloqueios

| Etapa | Entregável técnico verificável | Gate obrigatório | Situação atual |
|---|---|---|---|
| **F0 — especificação** | Este plano mestre, caderno científico, matriz K01–K18, limites, decisões e testes | Revisão e congelamento da arquitetura; nada de áudio novo | **Documento em elaboração/concluído nesta tarefa; código não iniciado** |
| **F1 — dados/proveniência** | Ficha do piano-alvo, escala C4, pacote de medições disponíveis e placeholders marcados | Cada parâmetro medido/literatura/hipótese, licença e unidade | **Pendente** |
| **F2 — infraestrutura numérica** | Tipos de grandezas, matrizes físicas, integradores, energia e banco de testes isolados | Massa/rigidez válidas, conservação, convergência, ausência de fonte escondida | **Pendente; V4.0 atual é bancada anterior, não engine** |
| **F3 — corda rígida verificável** | FE/FDTD C4 com rigidez, perdas físicas, força/posição de golpe | f_n/B, inarmonicidade, perdas, ensaio de resolução, zero input | **Pendente reestruturação** |
| **F4 — martelo viscoelástico** | Compressão unilateral com memória/dissipação e reação, curva dependente da dinâmica | Balanço de contato, impacto e separação, sensibilidade a parâmetros, tempo de contato plausível | **Pendente; lei elástica atual NÃO suficiente** |
| **F5 — ponte MOVEL** | Terminação móvel física, restrições de contato estruturais, duas direções conforme dados | Teste de ação-reação, mobilidade complexa passiva, energia conjunto | **Pendente — prioridade arquitetural #1** |
| **F6 — tampo de referência** | Placa ortotrópica com nervuras/ponte/contorno, malha e mapas modais | Mobilidade espacial, convergência e validação contra pontos independentes | **Pendente** |
| **F7 — radiação** | Pressão gerada de velocidade espacial, posição definida, aproximação/contorno documentados | Testes de silêncio/malha/fase, identidade dimensional, diferença entre baffle/BEM | **Pendente** |
| **F8 — C4 grupo de cordas** | 2/3 cordas de C4 conforme escala-alvo + 2 polarizações, acoplamento e batimentos | Balanço comum e resposta espectro/decaimento, sem soma de WAVs isolados | **Pendente** |
| **F9 — PRIMEIRO gate de timbre** | WAV C4 pp/mf/ff com dados e A/B, diagnóstico de ataque/corpo/cauda | Escuta reconhece piano acústico; se falhar, **STOP/diagnose**, sem polifonia | **Pendente, gate mais importante** |
| **F10 — diferentes registros** | C2/C3/C5/C6 e respectivas geometrias; graves enrolados, longitudinal se necessário | Escuta por faixa, phantom partials, stretch tuning, voicing por material | **Bloqueado por F9** |
| **F11 — piano completo** | 88 teclas, ação/dampers/pedais, uníssonos e ressonância simpática, acordes reais | Acordes 32/48/64 com **ponte/tampo compartilhados**, CC64 e notas repetidas | **Bloqueado por F9** |
| **F12 — redução/tempo real** | Motor otimizado derivado da referência; AudioWorklet; testes PC/Android | Comparação referência vs otimizado, CPU, latência, GC, clipping, underruns | **Bloqueado por F9/F11** |
| **F13 — integração segura** | Base atualizada para main mais recente e seletor de novo motor com rollback | Regressões **todas** as engines incluindo E sampleado independente, presets/FX/MIDI/UI | **Bloqueado por F9/F12** |

**Não são estimativas de dias ou compromissos de lançamento.** As etapas de pesquisa podem requerer revisão de hipótese, calibração e repetição; não avançar por número de etapas “concluídas” se som continuar artificial.

## 8. Riscos: como saber que estamos repetindo os erros antigos

| Risco | Sinal de que ocorreu | Ação obrigatória |
|---|---|---|
| Som de piano elétrico/sintetizador | Espectro estável sem transientes/decay/ponte/acústica convincentes | Abrir diagnóstico físico da cadeia, rejeitar candidato |
| Endurecer feltro melhora força mas não pressão | Força aumenta e ataque radiado continua apagado | Investigar mobilidade/transferência/área ativa, não adicionar ruído |
| Ponte fixa mascarada de ponte móvel | \`bridgeShearForceN\` emitida por radiador sem realimentação | Bloquear áudio, refazer condição de contorno conjunta |
| Mais modos, mesma qualidade | Convergência numérica mas timbre não melhora | Verificar geometria, material, ponto de acoplamento e dados |
| Mistura de modelos de pianos diferentes | Escala de um, tampo de outro e mic de terceiro como se fosse instrumento único | Etiquetar fontes e incerteza, não alegar emulação de instrumento |
| Equalização, samples ou IR no motor V4 | Efeito oculto na função de som que não representa mecanismo físico | Remover, falha de gate de pureza |
| Chord fake | Somar WAVs de cada tecla independentemente com placa reinicializada | Falha de gate de uníssono/polifonia compartilhada |
| Ajuste para um único WAV | Bom C4 numa tomada, falha em outras velocities/mics | Reservar conjunto de validação, registrar fracasso |
| Otimizar prematuramente | CPU verde, mas corte de modos destrói realismo | Reverter e só otimizar após referência validada |
| Atualização da main perde recursos | Motor E/local WAV ou outros modos desaparecem ao integrar V4 | Reconciliar a base, testes A/B/C/D/E/Clássico e rollback |

## 9. Contratos de arquitetura a implementar DEPOIS da aprovação do plano

**Interfaces lógicas, ainda não código:**
- \`ActionInput → HammerState\`: posição [m], velocidade [m/s], energia [J], gatilho de escape;
- \`HammerContact ↔ StringGroup\`: deformação [m], força [N], velocidade relativa [m/s], potência [W], estado interno de feltro;
- \`StringGroup ↔ BridgePort\`: deslocamento [m], velocidade [m/s], força [N], potência [W], mesmo ponto e direção de contato;
- \`BridgePort ↔ Soundboard\`: vetor de força e velocidade em múltiplos pontos, dissipação/radiação contabilizadas;
- \`Soundboard ↔ Radiation\`: campo de velocidade normal [m/s] e pressão radiada [Pa], atraso geométrico [s], carga acústica opcional bidirecional;
- \`Damper ↔ StringGroup\`: contato e forças dissipativas, pedais e estados.
- \`DiagnosticRecorder\`: salvar metadados e séries internas para análise **sem se tornar camada sonora do motor**.

Os módulos devem possuir testes de energia, unidades, limitação espacial/temporal e contratos de origem de parâmetros. O caminho de saída para WAV só existe no **estágio F7/F8**, não na bancada F2.

## 10. Gestão do repositório, documentação e evidência

- V4 permanece na PR #39 em draft e em branch separada, sem tocar no motor publicamente ativo.
- \`main\` foi verificada em **v1.12.10**, commit \`1129e2e46a8a8bc373b43c1284b668ceea3e05ca\`; a branch V4 partiu da v1.12.8. **Antes de merge**, atualizar base e reexecutar CI da versão atual.
- Nenhum trabalho de código será iniciado nesta tarefa: **a entrega é este plano completo**. O arquivo existente \`StiffStringHammerV4\` continua classificado como **bancada física já existente**, não o novo motor completo.
- Em cada etapa: relatório \`hipótese → referência → parâmetros com origem → implementação → teste → áudio quando permitido → avaliação → decisão GO/NO-GO\`.
- Sem sucesso de CI = correção imediata antes de promover. CI verde sem som natural = **falha de timbre**, não sucesso musical.
- Cada PR/commit deve ter rollback viável, evitar alteração de arquivos públicos antes do release e preservar dados/importações atuais.
- Criar futuramente apenas após iniciar desenvolvimento: registro de unidades e parâmetros, log de energia por subestrutura, testes de convergência, corpus de avaliações auditivas (sem distribuir gravações privadas) e relatório de CPU.

## 11. Fontes principais que fundamentam este desenho

1. **Chabassier, Chaigne & Joly, JASA 2013, _Modeling and simulation of a grand piano_** — contato martelo/corda dissipativo, cordas rígidas, tampo ortotrópico, radiação acústica e esquemas que preservam energia: https://pubmed.ncbi.nlm.nih.gov/23862839/
2. **Chabassier, Chaigne & Joly, ESAIM M2AN 2014, _Time domain simulation of a piano. Part 1: model description_** — formulação completa de equações e acoplamentos: https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
3. **Miranda Valiente, Squicciarini & Thompson, JASA 2024, _Influence of soundboard modelling approaches on piano string vibration_** — rigidez/mobilidade do apoio muda força na ponte, vibração e decaimento: https://pubmed.ncbi.nlm.nih.gov/38742965/
4. **Corradi, Miccoli, Squicciarini & Fazioli, Applied Acoustics 2017, _Modal analysis ... at successive manufacturing stages_** — FE e mobilidade de ponte do Fazioli durante construção; não generalizar os parâmetros: https://www.sciencedirect.com/science/article/pii/S0003682X17303444
5. **Ege & Boutillon, JSV 2013, _Vibroacoustics ... reduced models, mobility synthesis, acoustical radiation_** — modos de placa ortotrópica/nervurada e radiação: https://www.sciencedirect.com/science/article/pii/S0022460X13002472
6. **Giordano & Winans, JASA 2000, _Piano hammers and their force compression characteristics_** — compressão do feltro e haste: https://pubmed.ncbi.nlm.nih.gov/10790050/
7. **Stulov, JASA 1995, _Hysteretic model of the grand piano hammer felt_** — materiais com memória: https://cir.nii.ac.jp/crid/1362262945923645952
8. **Weinreich, JASA 1977, _Coupled piano strings_** — acoplamento de cordas/ponte, aftersound, batimentos: https://www.speech.kth.se/music/5_lectures/weinreic/strings.html
9. **PNAS 2025, _Motor origins of timbre in piano performance_** — pistas mecânicas e percepção: https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/
10. **MDN — AudioWorkletProcessor.process** — bloco de áudio e duração da thread de processamento, futuro motor: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletProcessor/process
11. **Universidade de Iowa — Musical Instrument Samples: piano** — referência externa, com condições de captação, sem permitir playback no motor: https://theremin.music.uiowa.edu/MISpiano.html
12. **Zenodo/Plath 2019** — sensores sincronizados keybed, ponte, ouvinte; cuidado: **não mede força martelo–corda**: https://zenodo.org/records/3271370

**Referências adicionais por K01–K18:** [bibliografia anotada anterior](PIANO_V4_REFERENCIAS_TODAS_AS_18_LACUNAS_2026-11-23.md).

## 12. Decisão final do plano

**Plano de modelagem completo definido.** Há informação suficiente para começar **um motor físico experimental verificável**, mas não para prometer fidelidade natural sem parâmetros reais e escuta. A primeira implementação após o aceite do plano será **a infraestrutura de estados/energias e uma corda com apoio móvel fisicamente consistente**, nunca apenas mais um oscilador ou mais modos escolhidos por gosto.

**Regra de saída:** se o primeiro Dó4 completo não soar como piano acústico, não avançar para 88 teclas, acordes, pedal ou integração. Revisar o mecanismo físico que não foi reproduzido até encontrarmos uma explicação suportada por dados.
