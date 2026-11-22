# Atualização v1.9.1 — modelagem e 32/64 vozes
A qualidade Econômico passou a 32 vozes, Equilibrado a 48 e Estúdio a 64. O limite global de notas MIDI é 32 Leve / 64 Completo. A excitação triangular foi substituída por força de contato bipolar na posição de impacto do martelo, alterada pela dureza; compensação de fase, batimentos e ganho adaptativo são mantidos. Ainda faltam martelo de colisão iterativa, medições de cordas reais, tampo com acoplamento detalhado e ressonância simpática por nota. A comparação com piano real e o teste no Moto g04s são indispensáveis.

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
