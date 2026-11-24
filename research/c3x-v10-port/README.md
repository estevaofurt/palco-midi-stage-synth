# STAGE SYNTH C3X V10 — Etapa 11A (pesquisa)

Este diretório é uma prova de conceito **somente de agendamento MIDI**, independente do motor físico offline V10 em `research/c3x-python/v10/`. Não gera áudio, não altera a prévia V8 Web, não implementa AudioWorklet e **não deve ser anunciado como motor em tempo real funcional**.

## Uso

`node --test research/c3x-v10-port/midi-block-scheduler.test.mjs`

O escalonador atribui eventos note-on, note-off, CC64 e all-notes-off a frames absolutos e os distribui em blocos de 64/128/256 amostras. Os eventos mantêm a ordem de chegada quando simultâneos e não perdem o estado de notas pressionadas ou posição do pedal entre blocos. Eventos atrasados são rejeitados explicitamente nesta versão.

## Próximos marcos

1. Portar o integrador DSP V10 para AudioWorklet/C++/WASM, com conservação real dos estados de corda, martelo, ponte e tampo de bloco para bloco.
2. Implementar fila pré-alocada e sem ordenações/alocações no callback de áudio. **A estrutura JS desta pesquisa não é RT-safe.**
3. Acoplar teclado virtual e MIDI físico ao motor portado, sem mexer no app publicado antes dos testes.
4. Comparar WAVs offline V10 × Web portado por nota, parciais, afinação, ataque e decaimento. Monitorar CPU, latência, dropouts e memória em hardware real.
5. Manter o som dry e o reverb exclusivamente nos efeitos opcionais.

**Licenças e marca:** não importar WAVs de terceiros, nem atribuir endosso à Yamaha. A V10 é referência experimental não calibrada com medições internas do fabricante.
