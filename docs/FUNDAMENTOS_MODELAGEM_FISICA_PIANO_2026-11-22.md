# Stage Synth — fundamentos de modelagem física de piano e lacunas técnicas

**Data:** 22/11/2026 (fuso Brasil; consultas e CI registrados também em UTC 23/11).  
**Escopo:** pesquisa crítica e planejamento; nenhuma mudança de DSP, interfaces, presets, MIDI ou FX.  
**Código de referência:** estevaofurt/palco-midi-stage-synth, main em 8683246dcdb8557dc129bee15249dc78aca80411, v1.12.4.  
**P1 preservado como experimento separado:** PR #2, sem merge ou aprovação auditiva.

## 1. Síntese

A principal lacuna não é a quantidade absoluta de ressonadores. O sistema atual soma (a) uma corda em guia de onda, (b) modos sintéticos com frequências e decaimentos próprios e (c) um bloco pequeno de ressonância mecânica. Falta coerência entre transferência de energia, relação de fase, modos da ponte/tampo, vibrações em dois planos, calibração com notas isoladas e radiação sonora.

Os trabalhos de Bank–Zambon–Fontana (2010) e Chabassier–Chaigne–Joly (2014) mostram alternativas fisicamente informadas que não exigem solucionar uma estrutura completa 3D em tempo real. O trabalho de Cheng–Dixon–Mauch (2015) liga os comportamentos de decaimento a acoplamentos reais. Os materiais recentes do Unsampled Piano (2026, código GPL) mostram uma arquitetura modal completa, separando coeficientes físicos, calibração offline e renderização em tempo real, mas não constituem validação independente do projeto.

**Decisão recomendada para pesquisa:** suspender ajustes de timbre por ganho de um harmônico ou por adicionar filtros independentes. Antes de escolher a arquitetura, construir um modelo reduzido coerente e medido, reproduzível em Node e no AudioWorklet.

## 2. O que a literatura estabelece

### 2.1 Martelo, mecanismo e transientes
O toque MIDI deve determinar velocidade efetiva do martelo (mapeamento calibrável para o controlador). A força de contato depende da compressão do feltro e da posição/velocidade relativa martelo–corda. Um modelo inicial possível é F = K·max(u,0)^p, com massa e rebote do martelo e extensão viscoelástica/histerese quando justificada. O expoente p, K, massa, ponto de batida e tempo de contato variam por região e instrumento; não usar um conjunto arbitrário global.

Há evidência experimental de que contato mais curto em golpes fortes excita mais frequências agudas. A colisão pode conter mais de um contato e o feltro não age como uma mola linear. Um pulso sintetizado dependente de nota/velocity é alternativa eficiente, mas sua forma deve ser derivada de um modelo físico offline e verificada; não basta aumentar um ganho de brilho.

Fontes:
- Askenfelt e Jansson, From touch to string vibration: https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html
- Askenfelt e Jansson, nonlinear stiffness: https://www.speech.kth.se/music/5_lectures/askenflt/nonlinea.html
- Euphonics, valores de massa, comprimento, tensão, rigidez e martelo: https://euphonics.org/12-2-1-parameter-values-for-piano-simulations/
- Smith, Commuted Piano Synthesis: https://www.dsprelated.com/freebooks/pasp/Commuted_Piano_Synthesis.html

### 2.2 Corda rígida: altura, dispersão e perdas
Os parciais de uma corda rígida não seguem necessariamente n vezes o fundamental. Uma aproximação da literatura é f_n = n·f_ideal·sqrt(1+B·n²). Quando f1 é a **primeira parcial efetivamente medida**, usar f_n = n·f1·sqrt((1+B·n²)/(1+B)) para não introduzir erro de afinação na comparação.

B depende de material, raio, comprimento, tensão e nota. Separadamente, cada parcial perde energia por atrito, comportamento interno e transferência ao tampo. A rigidez afeta **frequência**; a filtragem de perdas afeta **envelope**; a excitação afeta **amplitude/fase**. Esses três problemas não devem ser corrigidos com o mesmo ganho espectral.

Uma seção allpass qualquer não implementa automaticamente uma curva B observada. É preciso ajustar a dispersão na faixa audível por nota, validar cents por parcial e compensar o atraso da fundamental. Modelar em guia de onda ou em modos são opções igualmente físicas quando sustentadas pela equação de movimento.

Fontes:
- Smith, Piano Synthesis e Dispersion Filter-Design: https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html e https://www.dsprelated.com/freebooks/pasp/Dispersion_Filter_Design_I.html
- Bank et al., A Modal-Based Real-Time Piano Synthesizer (2010): https://home.mit.bme.hu/~bank/publist/taslp10.pdf
- Vibration modeling, Frontiers (2023/24): https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full

### 2.3 Um teclado ≠ 88 osciladores
No piano, a tecla pode acionar uma, duas ou três cordas conforme região; cordas nominalmente iguais são levemente diferentes e **acopladas pela ponte**, não apenas somadas com detune independente. Cada corda também vibra em planos predominantemente vertical e horizontal. As componentes transferem energia ao tampo com eficiências diferentes, causando *prompt sound*, *aftersound* e batimentos. A situação de afinação e a impedância de ponte alteram o comportamento.

É incorreto explicar todo *double decay* com um único envelope global aplicado depois da soma. Uma versão econômica pode usar conjuntos reduzidos de modos acoplados, principalmente nas primeiras parciais que permanecem audíveis, medidos em múltiplos registros.

Fontes:
- Bank, Zambon e Fontana (2010), seção VI: https://home.mit.bme.hu/~bank/publist/taslp10.pdf
- Cheng, Dixon e Mauch (2015), Decay: https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2015/ChengDixonMauch-ICASSP2015-Decay.pdf
- Weinreich, Coupled piano strings (1977), bibliografia revisada por Bank 2010.

### 2.4 Graves: modos longitudinais e parciais fantasmas
Deformações geométricas das cordas produzem componentes longitudinais e frequências de soma/diferença associadas aos parciais; isso pode contribuir para a textura de graves tocados forte. Não basta adicionar oitavas de oscilador: é preciso respeitar a dependência da intensidade e dos modos que realmente excitam essas componentes. O modo longitudinal pode ser ativado só na região em que for audível, preservando CPU.

Fontes:
- Bank e Sujbert, Generation of longitudinal vibrations (2005): https://pubmed.ncbi.nlm.nih.gov/15898667/
- Bank, Zambon e Fontana (2010), seções IV/V: https://home.mit.bme.hu/~bank/publist/taslp10.pdf

### 2.5 Ponte, tampo, carcaça e radiação: papéis distintos
A corda, por si só, radia pouco. Sua força é transmitida pela ponte ao tampo, que possui modos estruturais e amortecimento próprios; a resposta depende da posição da ponte e do ponto de escuta. A ponte/tampo também alteram as condições de contorno e o decaimento das cordas. No modelo eficiente de Bank 2010, muitos efeitos de impedância podem ser representados na modelagem das cordas, e a radiação é aplicada por filtro compartilhado: NÃO é obrigatório simular FEM 3D em tempo real.

Opções leves: banco compartilhado de filtros modais calibrados; IR/transferências identificadas por regiões do registro; combinação com filtros de forma e radiadores estéreo distintos. Uma IR fixa não reproduz sozinha ressonância simpática sensível ao pedal. Convolução física do tampo não deve ser confundida com reverb da sala.

Fontes:
- Bank 2010, seções II, VII: https://home.mit.bme.hu/~bank/publist/taslp10.pdf
- Chabassier, Chaigne e Joly, modelo acoplado completo (2014): https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
- Soundboard/position/radiation, Unsampled Piano (documentação de autor): https://unsampled.mgth.fr/docs/parameters/soundboard/ e https://unsampled.mgth.fr/docs/parameters/microphones/

### 2.6 Pedal, amortecedores e ressonância simpática
A liberação da tecla e o estado do pedal mudam os amortecedores por corda. Eles atenuam frequências e direções de vibração de forma desigual; algumas notas agudas não possuem abafadores. O pedal abre caminhos de ressonância entre notas por meio da ponte. Há modelos unidirecionais de ressonância simpática numericamente mais seguros que loops arbitrários de feedback; os efeitos de realimentação deverão respeitar estabilidade/passividade.

Considerar sustentação contínua e meio-pedal no futuro exige medir estados de controle e releases, não apenas CC64 binário. Mecanismos acessórios e ruídos de teclas são úteis no acabamento, mas não corrigem cordas incorretas.

Fontes:
- Bank 2010, seção VI: https://home.mit.bme.hu/~bank/publist/taslp10.pdf
- Unsampled Piano, Dampers (implementação de terceiro, não autoridade universal): https://unsampled.mgth.fr/docs/parameters/dampers/
- Yamaha VRM (funcionalidade anunciada; não algoritmo revelado): https://faq.yamaha.com/ca/s/article/000025704?language=en_US

### 2.7 Síntese comutada, modal, waveguide, híbrida: trade-offs
**Modal:** representa diretamente modos, frequências e perdas; boa precisão e possibilidade de SIMD. Pode exigir muitos modos nos graves, e o acoplamento precisa ser considerado.
**Waveguide dispersivo:** eficiente para ondas viajantes e atraso de propagação, mas um único allpass de baixa ordem, como o atual, não necessariamente reproduz a rigidez em todo registro; mecanismos não lineares podem tornar-se difíceis de representar.
**Síntese comutada:** move a resposta linear do corpo para o ataque/entrada; reduz computação por nota, mas perde graus de liberdade de ressonância dinâmica se aplicada integralmente.
**Híbrido:** martelo sintético derivado de contato físico + notas com modos/guia calibrados + acoplamento reduzido + corpo/radiação compartilhado. Hipótese promissora, **não arquitetura comprovadamente superior**. Devemos comparar protótipos com custo e escuta nivelada.

Fontes: Smith (Piano/Commuted), Bank 2010, Modartt (funcionalidades públicas, não código): https://www.modartt.com/pianoteq_features

## 3. Implementações abertas relevantes

1. **Unsampled Piano (Rust, 2026, GPL-3.0):** modelo modal com até 3 cordas por tecla, 2 polarizações, ponte, tampo, abafadores, meio-pedal e radiação espacial; documentação técnica e testes com notas reais. O autor reconhece erros no equilíbrio dos graves e C5/C6. Estudar arquitetura, critérios de validação e custos — **não copiar código GPL no Stage sem decidir compatibilidade de licença**. https://github.com/mgth/unsampled-piano ; https://unsampled.mgth.fr/docs/how-it-works/
2. **Bank–Zambon–Fontana (2010):** sintetizador modal real com excitação/cordas/ressonadores secundários e radiador. Descreve otimização por custo por nota e redução dos modos menos audíveis. Referência de arquitetura particularmente importante para 32–64 notas, sem extrapolar números de CPU de PC antigo para Android.
3. **Podrazka Piano (browser, 2026, MIT no código):** síntese modal, dois estágios, modos longitudinais, IR e comparação com referência; reconhece agudos pouco convincentes. É referência de organização de ensaios web, não motor a incorporar automaticamente. https://github.com/danielpodrazka/piano
4. **Dussek (Rust, AGPL-3.0):** sistema físico de martelo/cordas/soundboard/pedais em tempo real; estudo conceitual, código sujeito à licença. https://github.com/ccoors/dussek
5. **Pianoteq / Roland V-Piano / Yamaha VRM:** tomar como exemplos de funcionalidades e percepção pretendida; a arquitetura interna proprietária não é dedutível dos materiais comerciais. https://www.modartt.com/pianoteq_features ; https://www.roland.com/global/products/v-piano/

## 4. Auditoria específica do Stage v1.12.4

| Subsistema | Evidência no código | Lacuna |
|---|---|---|
| Modal A | piano-worklet.js; MAX_VOICES=32; modos com perfis físicos aproximados | ligação dos modos com corda/ponte/direções de vibração; custo de 64 |
| Físico B | physical-piano-legacy.js copiado da v1.9.5 | dispersão/perdas insuficientemente calibradas; referência estável sem estalos relatada pelo usuário |
| Físico C | physical-piano.js, linha de atraso e modos aditivos, piano-resonance.js | subsistemas com parâmetros/fases pouco coerentes; resposta da ponte e radiação não identificadas |
| Martelo | seedString() injeta pulso de forma pré-definida e som de impacto parametrizado | sem solução de colisão não linear / velocidade relativa resolvida |
| Timbres | ganho de segundo parcial Japanese = 8, Upright = 4.6 em perfil C | compensações locais para C4 não generalizam a 88 notas |
| Corpo | saída C mistura aproximadamente 72% do sinal processado das cordas com componente de corpo | não está calibrado como transferência físico-espacial de ponte/tampo/radiação |
| Ressonância | 12 modos de corpo e 2 modos simpáticos por tecla compartilhados em piano-resonance.js | frequências/ganhos de referência sintéticos; não uma medição do tampo e posições da ponte |
| P1 isolado | PR #2, segunda seção allpass sem merge | incremento B ~13,8% no guia de onda de C4, ~2,4% na saída total; prova impacto limitado na arquitetura atual |
| P0 | docs/BASELINE_ACUSTICA_V124.md e testes; CI 90/90, 108 renders | estima características do **próprio sintetizador**, não valida sem áudio real seco nem escuta |

A afirmação de que a proporção direta da saída é um erro físico é **hipótese de diagnóstico**, não prova perceptual. A diferença entre sinal de vibração calculado e filtro de radiação do atual motor pode justificar parte do ganho. Testá-lo isoladamente, sem apenas multiplicar um slider de corpo.

## 5. Perguntas ainda abertas: não atribuir respostas sem medições

1. Quais parciais e envelopes de ataque representam os quatro modelos nas notas C2, C3, C4, C5, C6 e suas velocities? Referências musicais atuais incluem FX e não fornecem parâmetros de corda secos.
2. Qual é a função de transferência ponte–tampo por regiões e as características de estéreo e microfone dos pianos-alvo?
3. Qual a importância audível da segunda polarização, do acoplamento entre 2–3 cordas e dos modos longitudinais para cada região?
4. Quanto custo de CPU realmente consome cada bloco no AudioWorklet em PC e Moto g04s, com MIDI, FX, sustain e 32/64 notas? 48 kHz/128 frames: orçamento total por bloco ~2,67 ms, requer margem.
5. É mais eficiente modelar 64 notas como guias completos, bancos modais, ou misturar vozes de qualidade variável? Exige benchmark e escuta por registro.
6. Como calibrar parâmetros de martelo em velocity real se o teclado MIDI não fornece diretamente a velocidade física do martelo?
7. Há amostras públicas **com licença compatível** e notas secas/níveis conhecidos que possamos analisar privadamente? Verificar licença antes de usar ou redistribuir; WAVs privados do usuário jamais ao repositório.

## 6. Método de pesquisa recomendado antes da próxima mudança em timbre

**Experimento E0 — referências:** localizar gravações autorizadas por nota, sem FX, com informação confiável de velocity; se só houver MIDI e áudio polifônico, usar como teste musical, não rigidez da corda. Mapear 4 modelos de piano em famílias acústicas/voicing, sem inferir que a captura é o mesmo piano físico.

**E1 — identificação de cordas:** medir frequência de 4–10 parciais, B por nota, amplitude/fase inicial e amortecimento temporal por parcial. Não depender de uma única FFT central ou de um scorecard 5/5.

**E2 — colisão de martelo:** resolver offline o sistema martelo-corda para algumas notas/velocities, gerar família sintética de impulsos e comparar espectros sem embutir sons gravados.

**E3 — acoplamento:** criar protótipo mínimo (1–3 cordas, 2 polarizações, acoplamento reduzido passivo) e avaliar prompt/aftersound, batimento e transferência de energia para uma ponte compartilhada. Isolar os ressonadores preexistentes; evitar somar saídas duas vezes.

**E4 — radiação/corpo:** estimar corpo por registro/posição e testar saída seca calibrada; separar componente radiada de corda/corpo e reverb de sala. Pedal precisa mudar modos simpáticos, sem feedback instável.

**E5 — escolha de arquitetura:** comparar 3 hipóteses técnicas (modal, waveguide corrigido, híbrido) com exatamente as mesmas referências, nivelamento de loudness e protocolos MIDI. Tratar benefícios subjetivos e custo como eixos separados.

**E6 — aceite:** 32 notas sem perda audível e 64 como meta; verificar tempo por bloco, picos, clipping, estalos, roubo de voz, sustain, repetições, key-off, estabilidade numérica e notas presas em PC e Moto g04s. Preservar B v1.9.5, sem promover experimentos antes da aprovação auditiva.

## 7. Critérios para alegar realismo

- Frequências/inharmonicidade por registro dentro da variação de pianos reais de referência, não de um B fixo inventado.
- Brilho aumenta de modo plausível com velocidade do martelo; caráter do Felt deve resultar de parâmetros físicos próprios, não só EQ.
- Parciais exibem perdas e decaimentos individuais plausíveis, inclusive batimentos e prompt/aftersound.
- Pedal e teclas alteram ressonância simpática e tempos de cauda; a ressonância do corpo não é reverb de sala duplicado.
- Piano inteiro soa consistente em notas, acordes, dinâmica e repetição; avaliação auditiva nivelada/cega complementa métricas.
- CPU e robustez verificadas em dispositivos físicos com a aplicação completa, não inferidas de benchmark offline.

## 8. Limites éticos e técnicos

Não afirmar que conhecemos código-fonte do Pianoteq, Yamaha VRM ou Roland V-Piano. Não copiar código GPL/AGPL para o Stage sem revisão de licença. Referências de áudio não devem ser publicadas nem embutidas por padrão. Não declarar sistema FEM 3D em tempo real viável em celular sem protótipo medido. Não interpretar mais harmônicos, mais B ou mais ressonância como sinônimo de realismo. Manter main v1.12.4 e a v1.9.5 como referência até validação rigorosa.
