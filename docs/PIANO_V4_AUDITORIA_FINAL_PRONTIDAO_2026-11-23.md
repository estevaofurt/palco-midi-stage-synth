# STAGE SYNTH — VERIFICAÇÃO FINAL DE PRONTIDÃO DO MOTOR FÍSICO V4

**Data:** 23/11/2026  
**Solicitação:** verificar se ainda há dúvidas que impeçam iniciar o motor.  
**Resultado:** **GO PARA IMPLEMENTAÇÃO EXPERIMENTAL EM BRANCH ISOLADA. NO-GO PARA AFIRMAR TIMBRE DE PIANO CONVINCENTE OU INTEGRAR NA MAIN.**

## 1. Veredito

Não restou uma dúvida de fundamento físico ou de escopo que impeça começar a programação do motor V4. Existem, porém, parâmetros materiais e acústicos ainda não medidos que impedem prometer fidelidade do timbre. A pesquisa cobriu as 18 lacunas K01–K18 com bibliografia e métodos de medição; cobertura bibliográfica não significa que o instrumento foi calibrado.

**Alvo operacional inicial:** piano de cauda acústico contemporâneo, uma nota Dó4 (MIDI 60, 261,625565 Hz para A4 nominal = 440 Hz), uma corda isolada como laboratório inicial; não alegar emulação de marca até selecionar e caracterizar um instrumento de referência. O Steinway modelo B da Iowa é uma opção de comparação auditiva EXTERNA provisória, porque a captura e o instrumento estão documentados, mas os parâmetros da ação, martelo, ponte e madeira desse piano não estão disponíveis em um único conjunto completo de medições.

**Regra sonora irrevogável:** V4 produz som SOMENTE por equações de modelagem física. É proibido incorporar gravações de notas, ataques ou impactos PCM, SoundFont, samples, respostas ao impulso medidas ou camadas artificiais de clique ao renderizador físico. Referências gravadas, quando legalmente acessíveis, só entram em análise/escuta separada e nunca no gerador.

## 2. Inconsistências efetivamente identificadas no código

A leitura do arquivo research/piano-v4/stiff-string-hammer.mjs confirma:
- Possui uma corda de aço modal com parâmetros em SI, dispersão de rigidez, força de feltro unilateral e integração conservativa da energia.
- Usa funções de forma senoidais para uma corda com **DOIS apoios fixos**. Sua função bridgeShearForceN devolve **uma reação do apoio rígido**. Esse número NÃO é velocidade da ponte, NÃO pode funcionar como pressão acústica e NÃO deve ser conectado unilateralmente a uma placa como se fosse uma interface física real.
- Para incluir ponte móvel, reformular a condição de contorno e o campo de deslocamento ou resolver PDE corda+apoio por outra discretização. Exigir deslocamentos/velocidades compatíveis no encontro; forças de contato opostas e trabalho recíproco para garantir energia de corda+ponte+tampo+martelo+feltro.
- O feltro atual é apenas potencial elástico unilateral: ainda **não** inclui dissipação interna/histerese dependente da história, haste flexível ou parâmetros calibrados.
- O amortecimento modal por n² e a geometria C4 (0,62m, raio 0,48mm, massa martelo 8g etc.) são HIPÓTESES DE LABORATÓRIO, não medições do piano-alvo.
- A V4 ainda não possui ponte móvel, placa física, radiação para o ar, uníssono completo ou aprovação auditiva. Não produzir outro WAV rotulado como piano realista a partir só do modelo presente.

**Invariante matemático de integração:** força da corda sobre a ponte e força da ponte sobre a corda devem ser conjugadas com a mesma velocidade de interface, respeitando sinais e dissipação não negativa. A soma de energia armazenada e dissipada deve coincidir com a energia inicial e entradas externas dentro de tolerância definida. Testes de partes isoladas NÃO substituem esse ensaio do sistema acoplado.

## 3. Mudança EXTERNA relevante no projeto existente

No momento da inspeção, a MAIN PUBLICADA avançou para **Stage Synth v1.12.10**, commit **1129e2e46a8a8bc373b43c1284b668ceea3e05ca**. Foram incluídos nas versões 1.12.9–1.12.10 um **motor E opcional de amostras WAV locais**, teclado, importador e avisos; ele é um módulo DISTINTO do motor V4 puramente físico.

A PR #39 partiu da main **v1.12.8**, commit **626f5089aad95d22b63283b2b6babbfc8f7f17ad**, estando agora **dois commits atrás da main**. A comparação no GitHub reportou branch divergida, com **13 commits à frente e 2 atrás** no instante da verificação.

**Consequência importante:** testes antigos aprovados na branch V4 só certificam as funcionalidades conhecidas daquela base. ANTES de qualquer integração deve-se conciliar a V4 com a main moderna, preservar o motor E opcional e todos os demais A/B/C/D/Clássico, MIDI, CC64, presets, efeitos e interface, e executar a suíte COMPLETA dos dois ramos. Essa divergência não impede continuar P&D isolada.

## 4. Decisões de arquitetura que eliminam ambiguidades para COMEÇAR

| Questão | Decisão inicial | Dado ainda ausente (não bloqueia código de laboratório) |
|---|---|---|
| Qual tipo de piano? | Cauda acústico contemporâneo; primeiro Dó4 | Marca/modelo medido integralmente |
| Usar áudio de referência como excitador? | NÃO; somente modelagem física | Licenças e medidas específicas da referência |
| Escrever 88 teclas agora? | NÃO; comprovar uma corda → uníssono → teclado | Escala completa por nota |
| Corda: como terminar? | Apoio de ponte MOVEL com força/velocidade recíprocas | Mobilidade complexa medida no C4 real |
| Feltro | Compressão unilateral + perdas materiais fisicamente passivas; pesquisar histerese | Rigidez, relaxação e massa efetiva real |
| Martelo | Massa/velocidade dinâmica, reação e eventual haste flexível | Curvas velocity da ação real |
| Tampo | Modelo físico reduzido com área, massa, rigidez, amortecimento e modos espaciais interpretáveis | Geometria nervurada/crown/ortotropia específicas |
| Radiação | Velocidade de SUPERFÍCIE para o ar, observador com localização definida | Função de transferência/acústica medida |
| Amostragem | Saída de referência 48kHz; validar 44,1/48/96kHz e oversampling só se necessário | Resolução suficiente e orçamento de CPU |
| Comparação | C4 pp/mf/ff, ataque e parciais/decaimento, escuta de nível controlado | Limiar perceptual e parâmetros do piano-alvo |
| Integração | Somente após gates físicos, auditivos e regressão na MAIN ATUAL | Hardware/browser/polifonia ainda não verificados |

A escolha de C4 e cauda contemporâneo é um perfil de desenvolvimento provisório, não uma afirmação de que já conhecemos a geometria ou o som exato de um Steinway.

## 5. Gates inegociáveis antes de anunciar uma nota como "piano acústico"

- **G1 contato:** força do feltro não atrai corda fora do contato; deformação/histerese e perdas com unidades físicas, sem pulso desenhado manualmente.
- **G2 interface:** trabalho e energia de martelo+feltro+corda+ponte+tampo+perdas verificados em conjunto; propor inicialmente erro relativo < 10^-6 para ensaios definidos, não tratar tolerância numérica como prova de realismo.
- **G3 convergência:** refazer com amostragem temporal e ordem modal aumentadas; verificar estabilidade, início do contato, parciais, aliasing, energia e diferença entre resoluções.
- **G4 som no ar:** radiação derivada de um campo de velocidade do tampo realmente calculado, jamais da reação pontual da ponte tratada como placa inteira; fase/posição do observador documentadas.
- **G5 ouvido:** C4 suave, médio e forte sem efeitos; comparar espectro/duração em janelas e escutar em nível comparável. Se o usuário não reconhecer um piano, a variante é reprovada apesar do CI verde.
- **G6 escala:** somente após C4 aprovado, introduzir 2–3 cordas por nota, polarizações, graves, pedais, acordes, ação e ruídos mecânicos fisicamente justificados.
- **G7 integração:** atualizar a base para main atual e refazer todas as regressões, performance e AudioWorklet/hardware antes de release.

**GO para desenvolver G1/G2/G3 em pesquisa agora.** G4/G5 exigem implementar partes ainda ausentes. G6/G7 são NO-GO nesta fase.

## 6. As incertezas reais que NÃO devemos esconder

1. Parâmetros medidos do martelo de C4: massa efetiva, feltro, relaxação/histerese, curva de velocidade e influência da haste.
2. Comprimento, tensão, amortecimento por parcial, posição do martelo e condições de contorno de um piano de referência identificado.
3. Mobilidade complexa da ponte e mapa de vibração/radiação de tampo com nervuras e madeira ortotrópica; o sistema inteiro, não só uma reação em apoio rígido.
4. Igualdade de condições entre gravações externas e modelo: nota, dinâmica, sala, microfones, afinação, nível e direito de utilização.
5. Aprovação REAL da sonoridade por escuta e capacidade de execução simultânea 32–64 notas em navegador/hardware; ambos ainda não realizados.

São incertezas de CALIBRAÇÃO, EXPERIMENTO e PRODUCTIZAÇÃO, não motivo para adiar a escrita de um primeiro solver físicamente consistente. Cada parâmetro não medido deve ficar etiquetado como **illustrative, literature ou measured**, com unidades, origem, faixa de validade e teste de validação.

## 7. Fontes verificadas para fundamentar o GO/NO-GO

- Askenfelt & Jansson, KTH — contato e dinâmica: https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html
- Giordano & Winans, JASA 2000 — compressão e haste: https://pubmed.ncbi.nlm.nih.gov/10790050/
- Stulov, JASA 1995 — histerese do feltro: https://cir.nii.ac.jp/crid/1362262945923645952
- Chabassier et al., ESAIM 2014 — sistema físico acoplado com equilíbrio de energias: https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
- Miranda Valiente et al., JASA 2024 — condição de contorno na ponte altera força/decaimento: https://pubmed.ncbi.nlm.nih.gov/38742965/
- Ege & Boutillon, JSV 2013 — mobilidade e radiação do tampo: https://www.sciencedirect.com/science/article/pii/S0022460X13002472
- Plath, Zenodo 2019 — força KEYBED, aceleração PONTE, pressão biauricular: https://zenodo.org/records/3271370
- Iowa Steinway B — gravações de referência com cadeia descrita: https://theremin.music.uiowa.edu/MISpiano.html

## 8. Decisão final

**Aprovado iniciar a engenharia física da V4 em branch isolada.** Primeira tarefa técnica: reformular a corda com **condição de contorno móvel de ponte**, usando grandezas físicas com força/velocidade recíprocas, e verificar a energia do conjunto antes de criar radiação. Em seguida, contato martelo/feltro com perdas materiais e montagem de placa acústica progressivamente validada.

**Não aprovado:** reduzir a física a presets arbitrários, usar samples/IR de terceiros, reutilizar os motores E2/E3, apresentar outra nota que não soe como piano como "evolução", mexer na v1.12.10 ou fazer merge antes de gates.

**Sem dúvidas bloqueadoras para começar; com incertezas explícitas a resolver experimentalmente durante a execução.**
