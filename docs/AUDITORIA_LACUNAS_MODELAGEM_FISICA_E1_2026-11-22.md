# Auditoria E1 — Lacunas de modelagem física do piano Stage Synth

Data: 22/11/2026, fuso America/Sao_Paulo.  
Base de código examinada: main ba224226917d292ff85febb18259717c7fa48fc6, Stage v1.12.4.  
Escopo: physical-piano.js, piano-resonance.js, piano-worklet.js, acoustic.js, stage.js, patches.js, tests/piano_acoustic_metrics.mjs e o analisador E0, além de pesquisas acústicas revisadas.  
Audição e DSP: NÃO ALTERADOS. P1 permanece separado no PR #2. B v1.9.5 permanece preservado.

## Veredito

Ainda NÃO temos evidências físicas suficientes para integrar ou promover como realista outro motor C/P1/P2. Entretanto, a literatura oferece conhecimento suficiente para iniciar protótipos isolados e testes de hipóteses, sem precisar de FEM 3D em tempo real. A falta de um mecanismo não significa automaticamente que ele seja perceptivamente importante: sua prioridade deve ser demonstrada por medição, experimento de ablação e escuta.

O bloqueio principal não é a ausência de muitos harmônicos, mas a falta de uma CADEIA COERENTE de energia, fase, excitação, perda, acoplamento e radiação; agrava-se por lacunas no nosso próprio medidor.

### Definição de prioridades

P0 = bloqueia integração de um novo motor com alegação de fidelidade física; a investigação isolada pode começar.
P1 = essencial para uma versão musicalmente convincente, com testes concluídos antes da homologação completa.
P2 = acabamento potencialmente adiável sem comprometer a hipótese básica.

## Matriz de 18 lacunas verificadas

### L01 — P0 — Martelo–corda: colisão não linear sem solução dinâmica

Evidência: physical-piano.js linhas 159–189 preenche os buffers com dois pulsos Gaussianos pré-configurados; linhas 254–314 adicionam componentes modais/ruídos por fórmula, sem estados de massa, compressão, reflexão de força e separação. A modal em piano-worklet.js:101–140 usa uma força espectral sintética e não resolve o contato com retorno da corda.

Falta: solução de contato unilateral, massa e velocidade real do martelo, duração do contato dependente de velocity e registro, histerese no feltro e possibilidade de múltiplos contatos. A ausência desses mecanismos não invalida uma síntese comutada, MAS o impulso que a substitui precisa derivar de simulação física offline e ser calibrado.

Teste: modelo simples de uma corda e um martelo com força não linear F=K[max(δ,0)]^p e dissipação; verificar energia de contato, rebote, duração e espectro por tecla e velocidade. Comparar os pulsos obtidos com um filtro leve em tempo real. Sem amostra de martelo bruto não declarar K/p identificados.

Fontes: https://www.dsprelated.com/freebooks/pasp/Piano_Hammer_Modeling.html ; https://home.mit.bme.hu/~bank/publist/jasp03.pdf .

### L02 — P0 — Cordas de uníssono e duas polarizações reais

Evidência: os presets C no physical-piano.js:11–15 alocam uma corda/guia em eco e duas em balanced/studio para QUALQUER nota; v.beatRe/beatIm é um ressonador auxiliar, e outros 4–6 parciais são acrescentados independentemente. A modal produz pares de ressonadores desafinados nos primeiros seis parciais (piano-worklet.js:19,125–128). Não há sistema físico de 1–3 cordas dependendo da nota, cada uma vibrando em dois planos com impedância de ponte compartilhada.

Falta: acoplamento recíproco H/V e entre cordas de uníssono; diferentes taxas de transferência de energia ao tampo e radiadores.

Teste: isolar uma parcial e demonstrar prompt sound e aftersound em dois regimes de decaimento MESMO na fundamental, com dependência da posição de captação; depois comparar 1, 2 e 3 cordas acopladas. Weinreich mostrou experimentalmente que as duas polarizações explicam double decay até com só uma das cordas soando.

Fontes: https://www.speech.kth.se/music/5_lectures/weinreic/motion.html ; https://www.scilit.com/publications/e42d7761773fbb2ce4cead737338f02e .

### L03 — P0 — Ponte, tampo e fluxo de energia sem admissão/mobilidade física calibrada

Evidência: physical-piano.js:43 e :89–103 usa um banco de 3–7 modos do tampo, frequências pré-definidas. piano-resonance.js:20–21,75–88 mantém OUTRO banco com 12 modos. physical-piano.js:390–399,459–464 aplica a mesma reação escalar à propagação das cordas ativas; piano-resonance.js:157–159 reconhece explicitamente a falta de calibração da impedância. O retorno é limitado por clamp, sem garantia de passividade.

Falta: mobilidade da ponte variável com posição da corda e frequência; distinção entre força da corda na ponte, velocidade da ponte e pressão sonora; reciprocidade, passividade, resposta radiada estéreo. A soma de vários corpos pode duplicar ou omitir energia.

Teste: construir mobilidade reduzida por 2–4 regiões da ponte, de resposta causal e estável, com balanço energético sem entrada e teste de feedback em acordes/repetições/sustain. Comparar corpo radiado separado da vibração da corda. Não exigir tampo FEM 3D na aplicação.

Fontes: https://www.sciencedirect.com/science/article/pii/S0022460X13002472 ; https://juliettechabassier.perso.math.cnrs.fr/public/focus/2023/piano/ ; https://home.mit.bme.hu/~bank/publist/taslp10.pdf .

### L04 — P0 — Inarmonicidade, perdas por parcial e comportamento do registro não identificados

Evidência: a única seção allpass do waveguide C é assumidamente simplificada em physical-piano.js:143–157; loopGain fornece decaimento geral (:229–230), enquanto os modos extras recebem um B exponencial por nota (:268) e tempos de decaimento independentes (:300–303). O P1 dual-allpass alterou B do waveguide isolado C4 em ~13,8%, mas só ~2,4% na saída mista — evidência de que adicionar allpass por si só não resolve a coerência.

Falta: medição de f1 e da posição das parciais individualmente, dispersão por nota/modelo, loss filter ajustado por parcial e filtro de loop livre de alias/falhas. B, perdas e volume são mecanismos diferentes.

Teste: recuperar os modos audíveis de gravações sem perdas com incerteza, e só depois escolher modal ou guia de ondas. Comparar a sequência de frequências, decaimentos e fases em C2, C3, C4, C5, C6 e velocidades distintas.

Fontes: https://home.mit.bme.hu/~bank/publist/jasp03.pdf ; https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html .

### L05 — P0 — O analisador acústico atual tem viés físico verificável

Evidência: tests/piano_acoustic_metrics.mjs:47–58 procura picos em intervalo de ±2,5% a partir de n×frequência da nota em 12-TET; :93–111 estima B nessa janela com uma FFT Hann de 32768 amostras começando 0,18 s após o ataque. O método não acompanha a afinação real, múltiplas cordas ou parciais que desaparecem antes da janela. scripts/analyze_reference_audio.mjs usa média L/R mono.

Cálculo analítico: se f1 é a primeira parcial, a razão de deslocamento do n-ésimo modo é sqrt((1+B*n²)/(1+B))-1. Para n=8:
- B=0,0004: +1,252%, dentro dos ±2,5%;
- B=0,0007: +2,180%, dentro;
- B=0,0010: +3,099%, FORA;
- B=0,0012: +3,707%, FORA;
- B=0,0020: +6,101%, FORA.

Consequência: para B elevado, o analisador pode escolher o pico errado, subestimar a rigidez ou produzir diferenças espectrais que não correspondem à parcial física. Algumas estimativas E0 com Felt C4 e regiões agudas são preliminares até validação independente. Ter >=3 parciais detectadas NÃO prova que sejam as parciais certas. Diferenças de dB nos 33 arquivos E0 não são rankings objetivos de realismo A/B/C.

Teste obrigatório E1.1: sintetizar sinais com f1, B entre 0 e 0,003, envelopes por parcial, ruído, detune, duas cordas e notas suaves; rastrear cristas em tempo-frequência ou ajustar modelo inarmônico iterativo. Registrar erro e confiança por parcial; reapurar o histórico de 33 arquivos sem sobrescrever medições anteriores.

### L06 — P0 — Identificabilidade de parâmetros físicos e referência sonora

Um microfone que capta uma única nota não determina univocamente massa do martelo, curva de feltro, perdas da corda, impedância da ponte, radiação ou a resposta da sala. **Problema adicional do benchmark E0:** o Motor A modal dentro da aplicação recebe convolução de cordas/corpo na cadeia acoustic.js:213–225,268–279 (node conectada a this.strings, retorno res e corpo classic), enquanto scripts/analyze_reference_audio.mjs e tests/measure_piano_engines.mjs analisam apenas a saída direta dos respectivos motores, sem passar pelo mesmo grafo final. O C já incorpora um corpo mecânico interno. Portanto, as diferenças dB A/B/C de E0 sequer comparam **os mesmos estágios de saída ou a experiência final do aplicativo**. Um filtro de corpo e uma curva de excitação diferentes podem produzir quase o mesmo espectro. BiVib oferece 10 velocidades MIDI/duas classes de piano e posições binaurais; RWC oferece fabricantes e articulações; bitKlavier D oferece 9 microfones, mas usa edição e equalização de amplitudes. A velocidade MIDI comandada não é a mesma grandeza que a velocidade física do martelo.

Teste: comparar em **duas trilhas separadas**: (1) núcleos secos, sem corpo/radiador, para identificar cordas; (2) saída real do aplicativo com corpo, reverb/FX=off, mics e ganhos pareados para escuta. A diferença entre A modal com convolução e C com corpo interno deve ser explicitada, não escondida num único score. Fixar hipóteses físicas verificáveis e usar diferentes velocidades, posições, tampas, pedal, registros e instrumentos independentes. Conservar metadata, licença e hashes; não ajustar 30 parâmetros apenas pelo erro de C4.

Fontes e licenças: docs/AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md .

### L07 — P0 — Ausência de homologação física e perceptiva sob 32–64 vozes

Evidência: 95/95 testes Node e 108 cenários secos são úteis para regressão, mas não validam naturalidade, estabilidade em AudioWorklet do navegador, latência nem capacidade do Moto g04s. C usa 32/48/64 vozes por qualidade; A usa no máximo 32. O áudio no aplicativo completo também soma FX e outros módulos.

Teste: Chrome em PC e Moto g04s, 48 kHz / 128 frames (orçamento total ~2,67 ms), tempo médio e p95/p99 por callback, ciclos sem GC, underrun/xrun, streaming MIDI, pedal, 32 notas mínimas e 64 como meta, voice stealing, acordes e FX ativos. Escuta cega A/B/X em múltiplas notas e dinâmicas. Só chamar HOMOLOGADO após hardware real.

### L08 — P1 — CC64 contínuo perde resolução de meio-pedal

Evidência: stage.js:175–176 reduz CC64 a b>=64 (booleano); acoustic.js:281–284 envia apenas valor 0 ou 127. piano-resonance.js:101–106 admite 0..127 e keyGate contínuo. Assim, o suporte analógico parcial do corpo não recebe o valor MIDI que permitiria meio-pedal real.

Teste: após definir comportamento físico do amortecedor, receber 0..127, modelar contato/fall e liberação progressiva, testar 0→30→70→100→60→0, release e notas repetidas, respeitando estados da tecla.

Referências: https://pubmed.ncbi.nlm.nih.gov/19640015/ ; https://pubmed.ncbi.nlm.nih.gov/17927438/ .

### L09 — P1 — CC66 e CC67 não modelados

Evidência: stage.js:163–183 trata CC1, CC64, CC120, CC121, CC123, mas não CC66 sostenuto ou CC67 una corda. Piano não recebe os controles.

Faltam: sostenuto mantém só as notas já sustentadas no momento da ativação; una corda em grand desloca o mecanismo e pode atacar menos cordas/feltro diferente; no vertical, efeitos de pedal são distintos. Não substituir só por um ganho baixo.

Fonte: https://hub.yamaha.com/keyboards/k-how-to/how-to-use-keyboard-pedals/ .

### L10 — P1 — Graves enrolados, escala física e transições de encordoamento

Evidência: physical-piano.js:268 atribui B pela fórmula exponencial da nota e não separa tamanho, tensão, núcleo, cobre, comprimento de fala e cordas enroladas. A topologia do instrumento não muda fisicamente entre regiões de 1, 2 e 3 cordas.

Falta: descontinuidades da escala dos baixos, diferenças Yamaha/Steinway/vertical, corda simples e enrolada e perdas; algumas cordas enroladas fogem da lei B para parciais elevados.

Fontes: https://doi.org/10.1051/aacus/2021002 ; https://euphonics.org/12-2-1-parameter-values-for-piano-simulations/ .

### L11 — P1 — Afinação esticada (Railsback) não separada da dispersão

Evidência: midiHz(key) usa A440 / 12-TET para todas as notas; physical-piano.js:212–214 só altera levemente a segunda corda. B desloca as PARCIAIS mas não define a afinação global real de um piano.

Falta: mapa f1 por tecla/instrumento separado de B, detune entre uníssonos e stretch de oitavas. Evitar confundir afinação de piano acústico com desafinação artificial.

Fonte: https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html .

### L12 — P1 — Vibração longitudinal e parciais fantasmas

Evidência: os parciais extras do C são inarmônicos pré-definidos; não há fonte não linear quadrática transversal→longitudinal, precursor de impacto ou frequências soma/diferença; A também não identifica a mesma cadeia mecânica.

Falta: mecanismos de parciais longitudinais/phantom com intensidade maior em graves fortíssimo, com anti-alias. Pode ser implementado por modes suplementares EXCITADOS FISICAMENTE, não simplesmente aumentar uma oitava de oscilador.

Fontes: https://pubmed.ncbi.nlm.nih.gov/15898667/ ; https://home.mit.bme.hu/~bank/publist/taslp10.pdf .

### L13 — P1 — Antialiasing e discretização do subsistema compartilhado não validados

Evidência: piano-resonance.js:24–30,117–128 roda a 1/4 da taxa de áudio com pré-filtro 1 polo (alpha .25) e média de 4 amostras. A 48k, Nyquist do corpo é 6 kHz. O filtro combinado atenua aproximadamente 6 kHz só ~12,7 dB, sem especificação de rejeição de alias.

Isso é RISCO DE PROJETO demonstrável analiticamente, não um artefato audível já diagnosticado. Exige teste isolado com sweep 6–20 kHz e FFT de saída de 0–6k, a 44,1, 48 e 96 kHz.

### L14 — P1 — Radiação espacial, tampa, ponte por registro e microfones

Evidência: physical-piano.js:232–244,439–465 usa panorama conforme nota, filtro simples por voz e ressonadores fixos. Não existe função calibrada entre região do cavalete/ponte e pares de microfones, incluindo fase e diretividade.

Teste: diferenças entre close/binaural/plateia de bitKlavier D e tampas BiVib, separando reverberação do corpo; comparar sinal por região e canal; não aplicar uma única IR de sala como se fosse o tampo.

Fonte: https://home.mit.bme.hu/~bank/publist/taslp10.pdf, seção sobre resposta de tampo por região.

### L15 — P2 — Ruídos mecânicos auxiliares e eventos

Evidência: physical-piano.js:253,313–314,418–429 e piano-resonance.js:91–99,165–175 geram ruído sintético de martelo/mecânica. Sem fonte real identificada para keybed, rebote, damper lift/drop e pedal por evento.

Teste: separar os eventos de press/release/pedal, filtrar somente resíduos reais e calibrar volumes; NÃO tentar corrigir timbre das cordas aumentando ruídos.

### L16 — P2 — Agrafe, capo, duplex scale, carcaça e agudos sem abafadores

piano-resonance.js:106 fixa últimos 18 agudos sem dampers, uma aproximação inicial razoável mas não identificada por piano. Demais estruturas e rigidez de terminação não são simuladas. Podem ser adiadas até validação perceptiva; não justificam um motor extra agora.

### L17 — P1 — Interface usa nomes físicos para controles perceptuais

Evidência: physical-piano.js:26–41,267–305 apresenta caráter japonês/americano/felt/upright, mas os multiplicadores de harmônicos, decay e cutoff são ajustados perceptualmente, inclusive uma janela especial ao redor de C4. O motor A é adaptação modal do Claude, não código original verificado. Não se pode atribuir parâmetros do Stage a valores reais Yamaha CFX ou Steinway D sem medição.

Teste: manifesto de parâmetros com unidade, origem medida/sintética e relação com tecla/velocity, validando fora de C4. Não promover "Yamaha CFX físico" por nome do preset.

### L18 — P1 — Arquitetura de síntese por registro e custo

C tem no máximo dois guias completos e 4–6 modos aditivos por voz, independentemente da complexidade de graves/médios/agudos. A tem até 28 parciais e 32 notas. Uma arquitetura híbrida com diferentes custos por registro pode ser melhor, mas só pode ser escolhida após medir fidelidade e CPU nas mesmas notas.

Teste: comparar modal, waveguide dispersivo e híbrido com mesmo pitch/velocity e mic; medir custo por render, memória, espectro, aftersound e avaliação auditiva.

## Dois perigos que não estavam suficientemente explícitos

1. **Passividade/energia:** clamp de amplitude no retorno do C evita grandes amplitudes numéricas, mas NÃO prova um sistema de feedback passivo. Um modelo fisicamente coerente deve respeitar balanço de energia: sem nova excitação e sem ação externa, não pode gerar energia ilimitadamente. Exigir polos estáveis, zero-input run, resposta a feedback por região e acordes fortes.
2. **Não identificabilidade:** um único sinal de microfone pode ser reproduzido tanto por um martelo mais brilhante quanto por um tampo com filtro mais aberto. Precisamos de captação e condições independentes, não de "otimizar tudo" até combinar um único FFT.

## Contrato experimental mínimo para P2 — não confundir com decisão de arquitetura

- Martelo: massa, velocidade, compressão unilateral, impulso de força, rebote; resolver OFFLINE primeiro e verificar dependência de velocity.
- Cordas: N_k=1/2/3 onde fisicamente apropriado; modos por parcial e polarização, com f, decay e fases identificáveis. Não obrigatório simular todos os modos em tempo real.
- Ponte: somar forças e obter velocidade por mobilidade causal/passiva com 2–4 regiões; o feedback entre cordas deve respeitar a física e não uma reação escalar global.
- Radiação: transformar velocidades por filtros espaciais por região e L/R; sala/reverb fora da malha de cordas.
- Damper: estado por tecla e pedal, ressonância simpática, agudos sem abafador, e depois CC64 contínuo/66/67.
- Longitudinal: derivar das transversais para graves fortes quando confirmado audivelmente, evitando alias.
- Perfis: Japanese/Yamaha, American/Steinway, Felt, Upright dentro do mesmo módulo Piano; não criar novas categorias, links ou telas.
- Processamento: 48k/128 frames, 32 notas simultâneas mínimas e 64 como meta, CPU de PC/Android e estabilidade sem estalos.

## Gates de aprovação e situação atual

| Gate | Condição objetiva exigida | Situação | Bloqueio |
|---|---|---|---|
| G0 Referência real | Captura legal/identificada, MIDI/velocity e mic/ambiente documentados, notas de diferentes registros | FONTES IDENTIFICADAS, condições e dinâmica ainda não emparelhadas | Antes de afirmar fidelidade |
| G1 Medição | Recuperar f1, B e envelopes de sinais sintéticos com verdade conhecida, ruído, duas cordas, B até 0,003 e erro/intervalos | NÃO VALIDADO; ±2,5% tem falso negativo previsível | **P0** |
| G2 Cordas | Uma parcial com double decay físico e batimentos de uníssono reproduzidos em 1–3 cordas | NÃO DEMONSTRADO | **P0** |
| G3 Martelo | Excitação força-contato validada em pelo menos grave, médio e agudo, várias velocidades | NÃO DEMONSTRADO | **P0** |
| G4 Ponte/tampo | Uma cadeia causal de carga da ponte, resposta física/passiva e radiação estável | NÃO DEMONSTRADO | **P0** |
| G5 Pedal | Press/release/sustain/ressonância e estados contínuos, reprodução MIDI consistente | PARCIAL, CC64 binário | Antes de versão completa |
| G6 Performance | 32–64 vozes sob AudioWorklet real, Chrome PC e Moto g04s, sem xrun/click e com efeitos ativos | NÃO HOMOLOGADO NESTA ETAPA | **P0 para merge** |
| G7 Escuta | Comparação cega e nivelada, notas e música, vários registros/dinâmicas/pedal, sem efeito de sala confundir | NÃO HOMOLOGADO | **P0 para alegar realismo** |

## Próximos experimentos sem alterar o DSP estável

**E1.0 — Correção de justiça do benchmark:** separar comparação de núcleo seco e saída final do aplicativo; garantir que A modal inclua seu corpo de convolução no teste de escuta, enquanto C inclui o próprio corpo, com FX de sala desligados, microfone/ganho documentados. Testar o uso dos envios auxiliares do worklet. Os dB E0 anteriores NÃO são comparações do som final.

E1.1 **Antes de mexer no timbre:** teste sintético do medidor para f1/B até 0,003, parciais que morrem rapidamente, batimento, desafinação e SNR. Reprocessar 33 E0 como diagnóstico após o conserto (preservar histórico).

E1.2 Selecionar poucos arquivos PCM originais licenciados de BiVib (duas Yamaha, 10 velocities), RWC (Steinway/Yamaha reais) e bitKlavier Model D (microfones distintos); não baixar datasets gigantes sem necessidade; não incorporar arquivos NC ou gravações do usuário no GitHub.

E1.3 Protótipo independente **uma nota e martelo**, uma/duas polarizações, perda modal e dispersão; demonstrar double decay no mesmo modo e velocidade real.

E1.4 Protótipo **três cordas e ponte** reduzida, teste de passividade e diferença de aftersound com outra corda amortecida; comparar com Weinreich.

E1.5 Radiação estéreo por regiões, isolamento da decimação/alias e da reverberação ambiente.

E2 Comparação A/B/C/P1/P2 no mesmo protocolo MIDI, FX desativados primeiro, escuta nivelada com vários registros e instrumentos. Sem P2 no aplicativo até critérios.

E3 Validação dos pedais, polifonia, CPU, latência, MIDI e estalos em PC e Moto g04s.

## O que podemos adiar

Simulação FEM/3D de todas as peças e acústica da sala em tempo real; reflexos específicos da carcaça inteira; todos os modos longitudinais do agudo; modelagem exata de agrafe/duplex; haptics e 88 curvas completas de feltro. Não são pré-requisitos de um primeiro modelo reduzido sério.

## Bibliografia primária

- Smith: https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html e https://www.dsprelated.com/freebooks/pasp/Piano_Hammer_Modeling.html
- Bank et al. 2003: https://home.mit.bme.hu/~bank/publist/jasp03.pdf
- Bank, Zambon e Fontana 2010: https://home.mit.bme.hu/~bank/publist/taslp10.pdf
- Weinreich: https://www.speech.kth.se/music/5_lectures/weinreic/motion.html
- Chabassier, Chaigne e Joly: https://juliettechabassier.perso.math.cnrs.fr/public/focus/2023/piano/
- Ege e colegas, ponte/tampo: https://www.sciencedirect.com/science/article/pii/S0022460X13002472
- Bank/Sujbert longitudinal: https://pubmed.ncbi.nlm.nih.gov/15898667/
- Cordas graves enroladas: https://doi.org/10.1051/aacus/2021002
- Part pedaling: https://pubmed.ncbi.nlm.nih.gov/19640015/
- Sustain: https://pubmed.ncbi.nlm.nih.gov/17927438/
- Yamaha pedais: https://hub.yamaha.com/keyboards/k-how-to/how-to-use-keyboard-pedals/
- Revisão de avaliação auditiva: https://reference-global.com/article/10.5334/tismir.267?tab=article

**Conclusão:** Não há falta de informação suficiente para impedir experimentos isolados; há falta de **provas físicas e de um instrumento de medição confiável** para promover o próximo motor como realista. Nenhuma alteração de código sonoro foi autorizada ou feita nesta pesquisa.
