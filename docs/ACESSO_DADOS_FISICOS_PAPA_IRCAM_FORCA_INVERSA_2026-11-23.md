# Stage Synth — pesquisa direcionada de DADOS FÍSICOS: PAPA/FPM2, força inversa e corpo/radiador (23/11/2026)

**Escopo:** somente pesquisa e preparação para possível aquisição legal de dados. **Nenhum DSP, MIDI, UI, FX, preset, amostra ou motor alterado.**

**Base verificada antes da edição:** `main` SHA `6d73ddea67334d6725d31ad906e1d3d0a8409b98`, `package.json` `1.12.4`; documentação `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md`, `docs/PROXIMAS_ETAPAS.md`, protocolo M01–M09 e últimas pesquisas F01–F08. **Motor B histórico da v1.9.5 apenas com estabilidade relatada pelo usuário**, A/B/C da raiz não homologados. **R-GATE-1..7 continuam 0/7 integralmente aprovados; P1/P2 e qualquer implantação de DSP congelados por pedido expresso.**

## 1. Novas fontes institucionais, com separação rigorosa de *paper* / dados / direito comercial

| Código/prioridade | Fonte primária conferida | Contribuição relevante | Disponibilidade real e barreira |
| --- | --- | --- | --- |
| G01 — **alta para pedido de acesso** | **FWF PAPA: Predictive Approach in Piano Acoustics** — https://www.fwf.ac.at/en/research-radar/10.55776/M1653 — projeto do Austrian Science Fund, concluído em setembro de 2016; pesquisa de Antoine Chaigne na MDW/IWK Viena, incluindo colaboradores ENSTA/INRIA | O relatório final diz que **cerca de seis instrumentos modernos/históricos** foram submetidos a ensaios para estimar parâmetros de martelo, cordas, ponte, tampo, campo acústico e percepção, e construir uma representação 3D. É fonte potencial de **medições cruzadas do MESMO instrumento** (muito mais útil que WAVs sem metadados). | Relatório institucional publicado e conferido. **Não foi localizado ou adquirido pacote público completo com séries temporais, resposta H/V, FRF 2×2, manifestos por piano ou licença para uso comercial**. Dados históricos do projeto não devem ser marcados como disponíveis porque um relatório descreve sua existência. Solicitar catálogo de material e condições de acesso comercial **antes** de pensar em usá-lo. |
| G02 — alta, **alternativa ao sensor de força direta** | **Antoine Chaigne**, *Reconstruction of piano hammer force from string velocity*, **JASA 140, 3504–3517 (2016)**, DOI https://doi.org/10.1121/1.4965965 ; resumo autoral https://www.growkudos.com/publications/10.1121%252F1.4965965/reader ; projeto financiador G01 | Método de **reconstrução de F_h(t)** a partir de medidas **não invasivas de velocidade da corda** e filtro inverso derivado dos pulsos propagados. Pode reduzir necessidade de alterar a ação acústica para instalar transdutor de força. | **Não é extração de F_h(t) de uma gravação estéreo comum**: exige a velocidade da corda em ponto(s) medido(s) e hipóteses/condições de onda, sincronização e validação da inversão. Artigo disponível, mas **não foi identificado conjunto original de velocidade+força de validação nem direito comercial dos dados**. Comparação com transdutor direto no piloto para estimar erro; não tratar inversão como medição direta. |
| G03 — alta, fonte complementar para radiadores | **Tan, Chaigne & Acri**, *Operational transfer path analysis of a piano*, **Applied Acoustics 140, 39–47 (2018)**, DOI https://doi.org/10.1016/j.apacoust.2018.05.008 ; instituição https://research.tue.nl/en/publications/operational-transfer-path-analysis-of-a-piano/ ; artigo editora https://www.sciencedirect.com/science/article/abs/pii/S0003682X1730871X | Estudo experimental em **Bösendorfer 280VC-9** identifica contribuição relativa do **tampo harmônico, bordas/aro, estrutura metálica e tampa** com análise operacional dos caminhos vibroacústicos. Tampo domina no instrumento do estudo; relatório FWF G01 relata também **contribuição significativa do lado esquerdo do aro em regiões graves**. Isso responde ao problema do Stage de soar como uma corda isolada em vez de um corpo mecânico inteiro. | Medições de um **Bösendorfer específico**, não parâmetro universal de Yamaha/Steinway/Upright. **Não foram encontrados sinais brutos por caminho/sensor/posição e licença comercial pronta para o Stage.** A prioridade perceptiva do aro, estrutura e tampa depende de ablação; não supor que todas as peças precisem ter simuladores caros e independentes em 64 vozes. |
| G04 — média, **dados modais já empacotados** | **IRCAM Modalys — Piano Soundboard**: https://support.ircam.fr/docs/Modalys/3.3/co/object_soundboard_piano.html ; https://support.ircam.fr/docs/Modalys/3.4.4/co/object_soundboard_piano.html | A documentação oficial indica que o objeto de tampo usa **medições de Philippe Dérogis num piano real**, contém malha **13×13 pontos** e é distribuído como **dois modelos de dados modais fixos**, carregados por *Read from File* (incluindo `piano-soundboard2.dat`). É o candidato de dado estrutural mais concreto encontrado fora de WAV. | **Somente documentação foi inspecionada**. Não baixamos nem verificamos os arquivos `.dat`; não foi confirmada licença para **extrair, redistribuir ou derivar parâmetros em software comercial independente do IRCAM**. São modelos modais, **não garantidamente matriz mecânica Y2×2(f), força do martelo, nem dados de Yamaha/Steinway**. Obter anuência escrita do titular e prova de origem para uso no Stage antes de acesso/calibração. |
| G05 — média, metodologia de separação de radiador | **Nicholas Giordano — Purdue Piano Physics**, https://www.physics.purdue.edu/piano/articles.shtml , estudo *Sound Production by a Vibrating Piano Soundboard* (JASA 104, 1648, 1998) | Estudo experimental mediu pressão acústica `p` e velocidade de tampo `v_b` sob força conhecida aplicada em diferentes pontos da ponte. Investigou tanto excitação **normal** quanto alguns casos **paralelos** ao tampo, relevantes para acoplamento e projeção. | Página institucional oferece artigos em PDF, **não arquivo aberto identificado com pares brutos F, v_b, p, fase e calibração ou licença de dataset**. Curvas não são matriz 2×2 nem dataset novo verificado. |
| G06 — média, processo global de modelagem | **Elie, Cotté & Boutillon**, *Physically-based sound synthesis software for Computer-Aided-Design of piano soundboards*, **Acta Acustica 6, 30 (2022)**, DOI https://doi.org/10.1051/aacus/2022024 ; instituição https://www.research.ed.ac.uk/en/publications/physically-based-sound-synthesis-software-for-computer-aided-desi/ | Modelo físico em **quatro blocos**: modos estruturais do tampo reforçado, cordas e martelo, vibração do tampo excitado, e radiação. O artigo explica que o objetivo principal é **prever efeitos de mudanças estruturais**, não reproduzir fielmente todos os detalhes perceptivos do piano. Apoia a divisão de ensaios por subsistema e posterior redução. | Artigo **CC BY** localizado (uso de texto/figuras sob seus próprios termos), **não significa** dados numéricos de instrumentação liberados ou código de engenharia disponível para copiar. Não fornece autorização para unificação de todas as referências e modelos. |
| G07 — contextual, projeto relacionado | **FWF FPM2: From Physical Modeling to Piano Making**, https://www.fwf.ac.at/en/research-radar/10.55776/P29386 ; lista do departamento https://www.mdw.ac.at/iwk/projects/ | Projeto posterior/relacionado do grupo PAPA, unindo ensaios e simulações para pianos reais, incluindo experiências sobre campo acústico. Pode identificar a continuidade institucional dos dados e responsáveis pela custódia. | **Não foi localizado repositório bruto aberto com direitos comerciais confirmados**. O acesso ao relatório/índice de projeto é apenas descoberta de potencial curadoria, não aquisição nem autorização. |

### O que mudou em relação à auditoria F01–F08

- **Novidade A:** existe um **método experimental indireto específico para o F_h(t)** e ele deve entrar no protocolo como opção M01.2. O método não remove a necessidade de medições físicas independentes, pois WAV ≠ vibrometria.
- **Novidade B:** **PAPA/IWK** fornece um **alvo institucional claro** para investigar disponibilidade de dados correlacionados em vários pianos, podendo poupar repetição de capturas. Ainda não sabemos se há sinais brutos preservados/licenciáveis.
- **Novidade C:** **IRCAM** documenta um **modelo modal medido e empacotado**. O dado tem origem experimental, mas a autorização para calibração comercial não foi verificada; não tratar distribuição no software Modalys como autorização para importar `.dat` para Stage.
- **Novidade D:** literatura de Bösendorfer confirma um motivo físico para estudar **aro/rim e estrutura**, sobretudo nos graves. Não ampliar o DSP antes de um teste de ablação com evidência de impacto perceptivo.

## 2. Plano de acesso de baixo desperdício: pedir metadados ANTES dos gigabytes

**A pesquisa documental não contatou ninguém.** São **tipos de instituição e material**, não negociações iniciadas.

### Pacote mínimo de perguntas sobre dados existentes

1. Instrumento e sessão: **fabricante, modelo, região, ano/estado de afinação, configuração de tampa/pedais, número de cordas por tecla**, local de sensor, temperatura e microfonação.
2. Existência real de séries sincronizadas **`F_h(t)`, `δ(t)`, `v_h(t)`, `v_string,T/P(t)`, `F_bridge,T/P(t)`, `v_bridge,T/P(t)`, `p_L/R(t)`**; quais são medições DIRETAS e quais são valores RECONSTRUÍDOS por filtro.
3. Conjunto mínimo de **C2/C3/C4/C5/C6 e transições de 1/2/3 cordas**, intensidades físicas medidas ou níveis claramente identificados, repetições, alterações de feltro e estados de pedais.
4. Para mobilidade: **`Y_{TT},Y_{TP},Y_{PT},Y_{PP}`** complexas por ponto, direção física dos eixos, banda válida, coerência, excitação conhecida e incertezas. Uma única curva `p/v_b` ou `Y_{TT}` escalar é dado parcial, não substituto da matriz.
5. Arquivos brutos ou derivados, formatos, tamanhos, hashes/identificadores, direitos e cadeia autoral. **Permissão comercial expressa** para cópia, análise, modificação, derivação de parâmetros DSP e distribuição de **software/presets derivados**; indicar separadamente se WAV/CSV brutos podem ser redistribuídos.
6. Disponibilidade de um **subconjunto de diagnóstico com licença escrita**, sem exigir acesso aos seis instrumentos completos inicialmente; quem pode autorizar e quais arquivos não são transferíveis.
7. Se a fonte for IRCAM, solicitar a **licença específica dos dados `.dat`** e confirmação de se os modos representam só vibração normal ou também acoplamento transversal; documentação do Modelo 13×13 não estabelece qual matriz física está disponível.

### Piloto próprio se não houver licença/acesso viável

- M01.2: medir velocidade real de corda sem contato, fazer a inversão publicada de F_h(t) **offline** e comparar com pelo menos uma medição direta quando possível; sem comparação, registrar margem de erro desconhecida.
- M02/M03: acompanhar polarizações de uma e múltiplas cordas em C2/C4/C6, com controle de abafadores e pedal, reportar fase e dupla cauda por parcial.
- M04/M04.1: medir FRF mecânica da ponte (força→velocidade) escalar e, com segurança profissional, **2×2** no mesmo ponto por regiões, sem confundir força tecla–base e força martelo com força aplicada na ponte.
- M05 estendido: captar pressão estéreo e vibração de **tampo, aro esquerdo e estrutura** no grave do mesmo instrumento; testar a contribuição relativa para que detalhes custosos sejam guiados por evidência, não decoração.
- **Sem exigir FEM 3D em tempo real:** o modelo físico offline pode ser reduzido por região/posição e validado por métrica física e escuta; não assumir desempenho 32–64 no Android.

## 3. M01.2 — requisito de validação da reconstrução inversa

Um sinal estimado `F_est(t)` é **resultado de inferência**. Exigir:
- distância conhecida sensor–posição de impacto, comprimento/massa/tensão/rigidez e reflexões na corda, taxa e calibração da medição;
- registro de impulso esperado, duração, pico, espectro e ruído do filtro inverso; avaliação de estabilidade da inversão;
- sensibilidade a ruído, posição de captação, múltiplas cordas e reflexões precoces, e **comparação com força direta medida em um piloto**;
- autorizações para usar os sinais medidos e os parâmetros derivados no Stage comercial;
- marcar como desconhecida qualquer incerteza não medida; **não sintetizar “dados reais” a partir de gráficos do paper**.

## 4. R-GATEs e ordem de verificação

| R-GATE | Como a presente pesquisa ajuda | O que ainda impede aprovação |
| --- | --- | --- |
| 1 / 4 — arquivos originais/manifestações | Identifica instituições com potencial de séries físicas e modelos fixos | Nenhum novo arquivo físico foi adquirido/hasheado, e as 50 gravações anteriores não contêm as grandezas necessárias |
| 2 — física identificada | M01.2 método inverso e possível Modalys 13×13; fontes de corpo/rim no grave | Sem séries calibradas de F_h, string H/V e **Y_ponte 2×2**, com fase, por instrumento |
| 3 — cadeia comercial | Descreve perguntas concretas para instituições/custódia | Direitos de PAPA/FPM2, IRCAM `.dat` e dados de terceiros **não aprovados** |
| 5 — medidores e cadeia A/B/C | Distinção F direta/inferida e soma de radiadores | E1.0/E1.1 não executados; A/B/C ainda sem cadeia equivalente |
| 6 — ensaios | Adiciona M01.2 e possibilidade de M05 estendido | Protocolo preparado ≠ medições físicas realizadas |
| 7 — homologação | Nenhuma mudança | 32–64 notas / CPU / latência / xrun / ABX em hardware real continuam pendentes |

**Contabilidade:** nenhum dado real novo, WAV/CSV/FRF/datafile baixado nesta rodada; conservar **50 gravações verificadas de seis pianos acústicos** e `0/7` R-GATEs integralmente aprovados. Não há novas versões de motor, integrações, modelos GPL/LGPL ou amostras incorporadas.

## 5. Recomendação de pesquisa seguinte

**Parar de buscar bibliografia genérica por volume** e priorizar a seguinte ordem de diligência documental e legal:

1. **PAPA/FPM2:** confirmar custódia, índice dos instrumentos, quais séries ainda existem e autorização de subconjunto mínimo comercial de M01–M05;
2. **IRCAM Modalys:** confirmar a existência do arquivo em distribuição acessível e licença para seu uso **fora** do software original; classificar modos (radiação/posição, graus de liberdade, unidades);
3. **Purdue e TU/e:** perguntar pela existência de pressão/velocidade/força/estrutura em arquivos brutos com fase, coordenadas, datas e direitos, incluindo contribuição do aro nos graves;
4. Se não houver dados adequados com licença, **preparar contratação de piloto próprio no mesmo instrumento**, com M01.2 opcional e M04.1 preferencial, sem fingir que dados publicados substituem a medição.

**Conclusão:** a pesquisa identificou caminhos tecnicamente plausíveis para obter dados físicos do instrumento inteiro e uma alternativa experimental de força do martelo, mas não converteu publicação em dado utilizável. A calibração comercial física permanece **NÃO PRONTA** e o novo DSP **BLOQUEADO**.
