# PIANO V4 — PROGRAMA DE FORMAÇÃO, FICHAS DE EVIDÊNCIA E TESTES DE CAMPO

**23/11/2026 — complementar ao Caderno Multidisciplinar.** Este documento foi concebido para fazer o projeto agir como uma equipe que conhece pianos reais: fabricante/luthier, técnico de regulagem e afinação, cientista de materiais, acústico, pianista, pesquisador de percepção e desenvolvedor DSP. É um **roteiro de estudo**, não uma certificação de competência profissional.

## A. Dez módulos com resultados práticos

| Módulo | Estudar | Prova de aprendizagem | Fontes de referência |
|---|---|---|---|
| 1. História/organologia | Cristofori, fortepiano, overstringing, quadro de ferro, família cauda/vertical | Mapa de diferenças construtivas e sonoras | Met Museum, National Music Centre, Yamaha |
| 2. Anatomia da ação | tecla, macaco, escape, martelo, repetição, backcheck, abafadores, pedais | Diagrama causal dos eventos de uma nota | Yamaha, Steinway, KTH Askenfelt |
| 3. Fabricação e manutenção | sequências da fábrica, alinhamentos, voicing, materiais de feltro | Ficha de martelo por registro + procedimentos de técnico | Yamaha manufacturing, PTG, Reblitz |
| 4. Escala de encordoamento | corda nua/enrolada, 1/2/3 cordas, pontos de contato, tensão e inarmonicidade | Inventário de geometria por tecla do alvo (dados reais ou ausentes) | Yamaha, KTH Conklin, JASA afinação |
| 5. Materiais do instrumento | feltro viscoelástico, aço/cobre, abeto ortotrópico, maple, ferro fundido | Tabela de propriedades com fontes, condições e incerteza | Yamaha, Mason & Hamlin, Kawai, PMC madeira |
| 6. Construção do tampo | nervuras, crown, downbearing, taper, colagem, linha das pontes | Mapa das diferenças entre tampo livre/instalado e mobilidade na ponte | Yamaha, Applied Acoustics, KTH Wogram |
| 7. Acústica e captação | radiação direcional, tampa aberta/fechada, lado superior/inferior, sala | Protocolo de mics com posições e níveis comparáveis | DPA, Shure, AES, JASA |
| 8. Afinação/voicing e execução | tuning stretch, uníssonos, escape, pedais, harmonização, repetição | Análise de como regulagem muda notas sem trocar o modelo de piano | PTG, KTH, PNAS 2025 |
| 9. Psicoacústica | ataque percebido, peso/clareza/brilho, ruídos mecânicos, efeito do volume | Escuta nivelada e cega, sem prometer excelência a partir de FFT | PNAS 2025, preparação de estímulos |
| 10. Engenharia física V4 | energia de cada componente, contato e mobilidade, calibragem/validação | Uma nota C4 reconhecida como piano, sem samples no motor | Chabassier, KTH Hall/Wogram/Weinreich |

## B. Fatos que invalidam hipóteses antigas

**B1 — golpe no lugar certo é dependente da nota.** Harold Conklin explica que a posição de impacto (d/L) muda ao longo da escala. Uma regra histórica comum entre 1/7 e 1/9 não atende ao registro agudo: no extremo C8 são relatados valores em torno de 1/12–1/17 em seus pianos examinados. A V4.0 usa fração **1/8 apenas como hipótese para C4**. NÃO reutilizar 1/8 em todo o teclado.  
Fonte: https://www.speech.kth.se/music/5_lectures/conklin/whereshould.html

**B2 — força correta do golpe é um fenômeno de contato.** Donald Hall mostra por que as idealizações "corda beliscada", "martelo massivo empurrando" e "golpe instantâneo de massa leve" falham espectralmente. O tempo finito e a reação da corda sobre o martelo são decisivos; não basta elevar 8/16 parciais com EQ.  
Fonte: https://www.speech.kth.se/music/5_lectures/hall/hall.html

**B3 — sustain e ataque compartilham a mesma ponte.** Gabriel Weinreich explica o compromisso entre acoplamento forte (ataque sonoro inicial, decaimento rápido) e fraco (sustentação, pouca potência). O **duplo decaimento** explica parte do caráter do piano, sem inventar dois envelopes independentes.  
Fonte: https://www.speech.kth.se/music/5_lectures/weinreic/weinreic.html

**B4 — nervuras alteram a impedância, não só a aparência da placa.** Klaus Wogram testou mudanças na altura e número de nervuras de um tampo vertical. Altura, massa/rigidez, anisotropia da madeira e condição de contorno mudaram a mobilidade e a radiação de formas distintas segundo região e frequência. Não traduzir este estudo para parâmetros universais sem medir o instrumento-alvo.  
Fonte: https://www.speech.kth.se/music/5_lectures/wogram/ribbing.html

**B5 — o movimento do pianista importa inclusive para ruídos da ação.** A pesquisa PNAS 2025 estudou movimentos de teclas e atributos percebidos como peso, clareza e brilho, além de ruídos mecânicos; contudo ela não prova que qualquer camada arbitrária de click resulta em piano.  
Fonte: https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/

**B6 — captação deslocada altera o 'timbre de referência'.** Medições da DPA com 10 microfones mostram variação do campo sonoro pela tampa e posição. Não comparar nota simulada em ponto abstrato com referência acústica microfonada de maneira desconhecida.  
Fonte: https://dpa-microphones.euwest01.umbraco.io/mic-university/background-knowledge/piano-sound-fields-and-miking-implications/

## C. Instrumento de referência: ficha de campo (a preencher, não inventar)

| Campo | O que registrar | Prioridade |
|---|---|---|
| Marca/modelo/série | Identificação de um piano real disponível para estudo | Alta |
| Tipo/altura/comprimento | Cauda/vertical, dimensões e condição de uso | Alta |
| Estado técnico | Afinação/uníssonos, regulagem, voicing, necessidade de reparo | Alta |
| Cordas para C4 | comprimento vibrante, raio/material, quantidade de uníssono | Alta |
| Ponto do martelo | distância até apoio / comprimento da corda C4 | Alta |
| Martelo C4 | massa efetiva, formato, densidade aparente e condição do feltro | Alta |
| Velocidade impacto | velocidades reproduzíveis pp/mf/ff, com sensor ou vídeo | Alta |
| Contato | duração, força indireta, rebound, múltiplas compressões | Alta |
| Madeira/tampo | tipo, localização da ponte, nervuras, umidade, crown | Alta |
| Mobilidade da ponte | força dinâmica versus velocidade por faixa de frequência | Alta |
| Vibração de superfície | acelerômetros/laser de pontos do tampo, quando disponíveis | Média |
| Radiação | mics, distâncias, orientações, tampa e ambiente | Alta |
| Pedais/abafadores | eventos temporais e diferenças de sustain | Média |
| Repetições | pelo menos três tomadas em cada dinâmica e nota | Alta |
| Direitos dos registros | autorização, armazenamento e licença de comparação | Alta |

Os campos ainda **não** contêm medições reais. A investigação não autoriza desmontar um piano nem manipular cordas (carga acumulada na ordem de dezenas de toneladas) sem técnico qualificado.

## D. Roteiro de medição auditiva e física — uma nota por vez

**D1 — antes do áudio:** registrar o instrumento, afinação, ambiente, microfones e estado do pedal. Fazer controle de ruído, clipping e time-zero do martelo/tecla. Se a referência tiver ruídos da sala, não confundir esses elementos com o instrumento.

**D2 — C4 isolado:** quatro níveis de velocidade física do martelo com medições ou estimativas justificadas; notas sustentadas e curtas; com e sem abafador. Registrar início do contato, pico de força, recuo e componente de ruído do mecanismo com o instrumento acústico.

**D3 — sinais separados:** obter, se possível, deslocamento/velocidade no ponto de martelo, força transmitida à ponte, aceleração do tampo e pressão de microfone. O projeto anterior misturou grandezas incompatíveis; a V4 deve explicitar unidades e calibrações.

**D4 — espectro e envelope:** analisar parcialmente as séries de tempo 0–10ms, 10–80ms, 80–400ms, 0,4–2s. Medir energia espectral, posição/largura de parciais, taxa de decaimento por parcial, batimentos, ruídos e transientes. Não usar número único de 'qualidade' para encerrar a questão.

**D5 — comparação controlada:** escutar A/B X com notas/nome de arquivo ocultos, níveis perceptuais próximos (sem mascarar variações dinâmicas reais). Para testes científicos, controle de pitch, loudness, duração e posição microfônica; para aceitação de produto, o titular precisa reconhecer um piano sem 'explicação' ou legenda.

**D6 — registrar resultado negativo:** se o V4 não soar como piano, registrar o porquê, rejeitar o candidato e continuar a investigar. Não multiplicar a nota para 88 teclas, não introduzir samples ou ruído artificial e não integrar em Stage D.

**D7 — passos posteriores, somente após C4:** duas/três cordas por tecla compartilhando ponte, baixos enrolados, C2/C3/C5/C6, múltiplos martelos simultâneos, CC64, ressonância, 32/48/64 notas, CPU de navegador/PC/Android.

## E. Como classificar cada nova fonte

Cada evidência pesquisada deverá guardar:
- **Autor, título, ano, link e tipo:** fabricante, manual técnico, museu, experimento revisado por pares, tutorial, marketing, gravação de referência.
- **Escopo real:** qual instrumento, quantas notas, velocidade, técnica de medição, condição da sala?
- **Observação comprovada vs inferência:** o que o autor realmente mediu ou apenas postulou?
- **Parâmetros aproveitáveis:** com unidade física, tolerância e contexto, ou explicitamente "não medidos".
- **Hipótese V4 afetada:** golpe, cordas, ponte, tampo, ruídos, afinação ou percepção.
- **Teste que refutaria:** qual evidência invalidaria nossa implementação?
- **Licença:** estudos e números podem inspirar mecanismos; código/gravacões/IR proprietários NÃO devem ser incorporados automaticamente.

## F. Próxima decisão de engenharia

O protótipo V4.0 já simula uma corda rígida e martelo recíproco **com parâmetros ilustrativos**. Não acrescentar ponte/tampo como "modelo pronto" até que as leis geométricas e a impedância sejam razoavelmente ancoradas. A V4.2 deverá ser uma **hipótese fisicamente auditável** de transferência corda–ponte–tampo, explicitando limites. Uma WAV C4 que não convence no ataque, corpo e cauda é um teste reprovado, mesmo com 100% dos unit tests aprovados.

Este programa estabelece uma competência de equipe multidisciplinar por etapas, **não declara que já dominamos fabricação, regulagem ou luteria profissional**. A construção de conhecimento será documentada por fontes, observações, testes e resultados.
