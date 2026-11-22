# Motor físico v1.9.2 — avaliação do timbre

## Problema identificado

A versão anterior usava uma excitação simplificada da corda cujo pico mais forte podia estar no 3º harmônico; vários harmônicos compartilhavam o mesmo decaimento. Isso não é representativo da evolução complexa de uma nota de piano.

## Alterações desta revisão

O motor usa uma linha de atraso dispersiva por corda (duas nos modos superiores) com 4, 5 ou 6 ressonadores adicionais, de frequências levemente inarmônicas e envelopes independentes. O pulso de excitação agora equilibra melhor os primeiros harmônicos; o contato do martelo é um filtro de energia com duração variável conforme força e feltro, ainda **não** uma simulação iterativa da equação de colisão martelo–corda. A radiação na ponte recebe filtragem de baixa ordem. O tampo mantém os ressonadores compartilhados existentes.

As estruturas são pré-alocadas por voz e o processamento no AudioWorklet não depende de amostras de piano gravadas.

## Polifonia e custo

- Econômico: 32 notas, 1 corda detalhada + 4 parciais por tecla.
- Equilibrado: 48 notas, 2 cordas + 5 parciais.
- Estúdio: 64 notas, 2 cordas + 6 parciais.

Benchmarks geram 1 s de áudio, não medem latência. Os resultados no computador de desenvolvimento não provam execução sem falhas em Android. Evitar combinar Estúdio, vários sintetizadores e FX em celular básico até medição real.

## Pendências para um piano convincente

1. Gravações de referência legalmente autorizadas em C2, C4 e C6 com pelo menos três velocidades para comparar espectro, ataques e decaimento.
2. Martelo de massa com compressão do feltro e reação da corda, com integração somente durante o ataque.
3. Dispersão por tecla ajustada à inarmonicidade e interação real entre 2–3 cordas.
4. Modelagem da ponte/tampo baseada em respostas calibradas, com modelos de radiação estéreo de baixo custo.
5. Escuta A/B às cegas e avaliação de desempenho real no Moto g04s antes de integrar à versão principal.

**Limitação:** alterações de espectro observadas no teste não são prova de que o usuário ouvirá um piano realista. Este é apenas um protótipo experimental, preservando os caminhos de versão anterior.

# Atualização do motor físico — v1.9.1 (experimental)

**Polifonia:** 32 notas mínimas no perfil Leve/Econômico; até 64 notas no perfil Completo/Estúdio. Equilibrado: 48 notas físicas (o limite global no celular continua em 32). O contador global representa notas MIDI, não quantidade de cordas calculadas nem osciladores de outras camadas. Camadas e FX podem elevar a carga de CPU. Não está garantida execução sem dropouts no Moto g04s sem teste físico.

**Timbre:** a excitação inicial da corda foi trocada de um triângulo de deslocamento (caráter dedilhado) para dois pulsos de força com média zero, separados pela posição do martelo, com largura dependente do feltro. Dureza/velocity aumentam conteúdo agudo em vez de escurecer a nota. Incluído batimento leve de uma corda secundária pelo modo fundamental no perfil Econômico, e processamento de 2 cordas nos perfis mais detalhados. Ganho de mistura suavizado acompanha a densidade do acorde.

**Verificações locais:** 45 testes de lógica aprovados; browser com interface de Android simulada e desktop aprovado, mas o navegador do ambiente bloqueou localhost para testar AudioWorklet real. Benchmark Node.js: uma passagem sintética de 1 s (48 kHz, 32 notas no perfil Econômico) ~33 ms; 64 notas Estúdio ~83 ms em ambiente de desenvolvimento. Isto não mede a latência nem a confiabilidade do Moto g04s.

**Limite do realismo:** não se trata de piano acústico calibrado. Falta colisão física iterativa martelo–corda, transferência de energia entre cordas, inarmonicidade variável medida, tampo amplo e pedal com ressonância simpática por nota. Precisamos ouvir/comparar com gravações de referência autorizadas, instrumentar espectro/decay por registro e aferir CPU/jitter no aparelho.

---

# Stage Synth · Motor físico econômico v0.2

## Objetivo

Piano tocável **sem amostras** com computação previsível em celulares de entrada, preservando a possibilidade de aumentar a qualidade no desktop e portar futuramente um núcleo equivalente a C++/WASM, iOS e VST3. A implementação atual é **Web Audio AudioWorklet** em JavaScript, não é um VST e ainda não foi calibrada com gravações de referência.

## Arquitetura — o que existe

- `physical-piano.js`: DSP original, independente do DOM, com motor `PhysicalPianoEngine`, registro de `AudioWorkletProcessor` e áudio renderizável em Node.js para testes.
- Uma ou duas cordas por nota: **waveguide digital**, com atraso fracionário por allpass (magnitude unitária), filtro de perdas e dispersão por allpass. A correção da fase no fundamental preserva melhor a afinação.
- Excitação localizada na posição do martelo e aproximação do contato não linear do feltro com `compressão³`. A física completa de massa de martelo + corda acoplada ainda não foi implementada.
- 3–7 ressonadores do tampo compartilhados **por instrumento**, em lugar de convolução individual por nota.
- Declínio das cordas ajustável com pedal de sustain, abafamento e release. Controle de brilho e envio à ressonância nas notas já sustentadas.
- Buffer de corda e vozes **pré-alocados**. Nenhuma criação de osciladores, AudioNodes, Arrays ou objetos no loop `render()`. As mensagens de controle e encerramento podem usar estruturas alocadas fora do caminho contínuo de amostras.
- Mudanças graduais por amostra para ganho/envio e dissipação, buscando evitar estalos.
- Vozes são roubadas de maneira determinística ao exceder o limite; vozes liberadas são priorizadas para roubo.
- O motor acústico antigo permanece disponível se o AudioWorklet falhar.

## Qualidade / custo

| Qualidade | Cordas por nota | Vozes máximas DSP | Ressonadores compartilhados | Indicação |
|---|---:|---:|---:|---|
| Econômico | 1 | 8 | 3 | Moto g04s e similares |
| Equilibrado | 2 | 16 | 5 | Celulares intermediários / laptop |
| Estúdio | 2 | 24 | 7 | Computadores com folga de CPU |

O limite global do Stage Synth continua sendo de 8 vozes no perfil Leve, podendo cair para 6 ou 4 com múltiplas camadas. Selecionar qualidade alta do piano **não elimina** o limite global do Stage.

## Resultados desta versão

No ambiente de desenvolvimento (Node 22, não celular), renderização de 10 segundos a 48 kHz com oito notas simultâneas: **Econômico ≈ 51,5 ms, Equilibrado ≈ 86,0 ms, motor modal anterior ≈ 98,5 ms**. Valores dependem do hardware, compilação JIT e perfil de notas; não equivalem a latência de áudio ou autonomia da bateria.

- `npm run check`: 43 testes automatizados aprovados.
- `python tests/browser_physical_ui_v19.py`: inicialização da interface no Chromium simulado Android/desktop, seis módulos, seleção do motor e qualidade, sem erros de JavaScript.
- `tests/physical_worklet.test.mjs`: simulação do protocolo do AudioWorklet, inicialização de nota e encerramento.
- O acesso a **origens locais seguras** foi bloqueado pelo ambiente de navegador, portanto **o AudioWorklet em execução real (HTTPS/Chrome) não foi homologado nesta sessão**.
- **Moto g04s físico e MIDI real: ainda não testados.**

## Limitações que ainda separam o som de um piano de concerto

1. A força do martelo é uma aproximação não linear espectral; não há simulação de massa, ricochete e feltro dependente de histórico da compressão.
2. A dispersão usa um allpass de primeira ordem, em vez de uma cascata por registro calibrada para a rigidez das cordas de piano.
3. Uníssono de duas cordas sem troca física de energia entre elas; o tampo usa sete modos fixos em vez de múltiplas frequências e amortecimentos medidos.
4. Ressonância simpática existe como envio global ao tampo; ainda não calcula todas as cordas liberadas por pedal.
5. Não existe simulação completa de `una corda`, abertura de tampa medida, ruído de abafador dependente da altura ou mapeamento de múltiplas regiões mecânicas da escala.
6. Caráter japonês/americano/felt/upright é aproximado por parâmetros, não por reprodução nem medição de modelos comerciais específicos.

## Roteiro recomendado

1. Comparar demos com gravações próprias/autorizadas: FFT da nota, evolução espectral, envoltória e frequências dos parciais por registro.
2. Ajustar rigidez, perdas e duplas cordas por regiões (graves, médios e agudos) em vez de parâmetros uniformes.
3. Modelar martelo com integração discreta de contato não linear (não apenas envelope de força), mantendo custo só durante o ataque.
4. Acoplamento cordas–tampo e ressonância simpática dinâmica sob pedal; manter opção de desligar no modo Econômico.
5. Medir x-runs, temperatura, CPU e latência com MIDI no Moto g04s; ajustar parâmetros de qualidade com base nesses dados.
6. Depois da aceitação sonora, portar um núcleo equivalente em **C++ puro** para VST3, app Android/iOS e possivelmente WebAssembly. Não duplicar regras sem testes vetoriais cruzados.

## Como testar

1. Use `v1.9.0.html` no site experimental em HTTPS.
2. Ative o áudio e o módulo Piano Acústico; desligue as demais camadas e FX.
3. No editor, selecione **Motor do piano → Cordas físicas · otimizado** e **Detalhe físico → Econômico · celular**.
4. Compare Japanese Grand, American Grand, Felt Piano e Upright com a opção Síntese clássica.
5. Teste acordes de três a oito notas, sustain e mudança de brilho com a nota pressionada.
6. Se ouvir falhas: compare a mesma passagem em Síntese clássica e informe se os estalos ocorrem sem FX.

## Referências de fundamentos

- Julius O. Smith, *Physical Audio Signal Processing*, seções de digital waveguides e piano: https://www.dsprelated.com/freebooks/pasp/
- Bensa et al., *From the Physics of Piano Strings to Digital Waveguides*: https://quod.lib.umich.edu/cgi/p/pod/dod-idx/from-the-physics-of-piano-strings-to-digital-waveguides.pdf?c=icmc;idno=bbp2372.2002.009;format=pdf
- Web Audio `AudioWorkletProcessor`: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletProcessor

O motor é um trabalho de implementação independente, não contém código, modelos ou samples do Pianoteq.

### v1.9.4 — referências dos quatro instrumentos

O motor mantém linhas de atraso e ressonadores compartilhados. Quatro perfis independentes foram ajustados a partir do trecho sincronizado de C4 em capturas com os efeitos originais. A nova modelagem do ataque para o corpo utiliza atenuação exponencial por voz com multiplicação por amostra e filtragem leve por registro, sem samples em runtime. Ver `CALIBRACAO_194.md` para dados e limitações.


## Etapa v1.9.6 — contato do martelo

Agora existe um submodelo físico em `hammer-contact.js`: força unilateral `F=K·max(0,δ)^p`, em que `δ` representa compressão do feltro; um martelo de massa aproximada perde velocidade pela reação do contato, enquanto parte da energia é transferida à corda por impedância transversal efetiva. O modelo usa integração curta com supersampling e termina quando o martelo rebate.

As forças são calculadas antecipadamente em uma grade de registros, velocities e durezas; há interpolação contínua. A forma de força é dobrada em um período da linha de atraso no momento de ligar a nota (**síntese comutada**) para manter o custo da sustentação. O modelo deliberadamente ignora reflexões da corda enquanto o martelo ainda está em contato: portanto é uma aproximação, não solução completa de acoplamento bidirecional. Constantes são parâmetros de projeto, não coeficientes medidos de um Yamaha CFX.

Não usa arquivos WAV da referência na execução. As quatro gravações continuam exclusivas da análise privada. A comparação v1.9.5/v1.9.6 deve usar níveis equalizados e as mesmas notas. A v1.9.5 foi preservada no GitHub como fallback.
