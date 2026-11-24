# Stage Synth — C3X V8 Web + E sampleado (prévia 1.13.1)

## O que foi recuperado

O **código real do sampler E** foi reencontrado no repositório (`SampleLibrary`) e reconectado à prévia `v8-preview.html`. Os bancos `American`, `Japanese`, `Felt` e `Upright` são separados, carregados pelo usuário como WAV local; não são publicados no GitHub. Sem áudio importado o E fica silencioso, mas a tecla virtual é destacada e aparece aviso específico. O motor E não depende do AudioWorklet do piano V8.

## O que NÃO foi recuperado

O **V8 Python aprovado na Etapa 8** era distribuído como `Stage_Synth_C3X_Etapa_08.zip`, contendo código e relatórios. O nome e a documentação foram encontrados no histórico da conversa, **mas o ZIP não estava acessível pelo sistema de arquivos atual, arquivos da conversa, Biblioteca, nem repositório GitHub**. Portanto esta entrega **NÃO restaura o timbre original do V8**; o seletor `C3X V8 Web (prévia)` conserva uma modelagem física web experimental, declarada explicitamente como não equivalente.

O usuário relatou que o timbre da prévia não reproduz todas as qualidades do original. Esse parecer é válido e requer a transposição do **código Python original**, não especulação ou retimbragem arbitrária.

## Como usar

1. Abrir `v8-preview.html`, ativar áudio.
2. Escolher **Motor do piano**: `C3X V8 Web · físico experimental` ou `E · Piano sampleado · WAV local`.
3. No E, selecionar **Piano sampleado**: American, Japanese, Felt ou Upright.
4. Descompactar `Stage_Synth_E_48_Amostras_Privadas_para_Importar.zip` que já foi gerado e importar as notas WAV da pasta correspondente, em `Carregar notas WAV`. Arquivos nomeados `MIDI60_v60.wav` etc.
5. Notas/velocidades, sustain/teclado/MIDI, FX e demais instrumentos continuam integrados. O arquivo WAV fica apenas na sessão, não no GitHub e não persiste após atualizar a página.

## Próximo passo técnico fiel ao pedido

O titular deve anexar **`Stage_Synth_C3X_Etapa_08.zip`** à conversa atual ou colocá-lo no projeto/repositório. Só com fonte/coeficientes reais é possível portar integralmente o V8 a AudioWorklet/WASM, comparar PCM/afinação 88 notas/ataque/caudas/harmônicos com as referências originais e então torná-lo motor principal sem o qualificativo de prévia.

A antiga rota principal `index.html` permanece intacta por segurança até o V8 original ser acessado e reproduzido. A/B/C/D não aparecem na prévia V8+E. O sampler está independente e funcional com banco local.
