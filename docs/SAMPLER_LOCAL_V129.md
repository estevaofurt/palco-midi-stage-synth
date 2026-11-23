# Stage Synth v1.12.9 — Piano sampleado E (WAV local)

**Data:** 23/11/2026. Atendendo à solicitação do titular de incluir o motor sampleado aprovado em escuta (experiência E2.7), adicionamos **E · Piano sampleado · WAV local** ao seletor do próprio módulo Piano acústico, sem alterar A/B/C/D/Clássico. **Padrão permanece C.**

## Como usar
1. Abrir Stage Synth e ativar áudio.
2. Na cena Piano acústico, escolher motor **E**.
3. Escolher Japanese Grand, American Grand, Felt Piano ou Upright.
4. Em **Banco de amostras · motor E**, selecionar as notas WAV com nomes como `MIDI60_v60.wav`, `MIDI60_v110.wav` ou `C4_v60.wav` do piano escolhido (vários arquivos juntos).
5. Tocar no teclado virtual, via teclado do PC ou MIDI; sustain CC64, arpejador, chord mode, looper e FX usam o fluxo normal do Stage. Para outro piano, trocar o instrumento e importar seu banco específico.

## Privacidade e limites
As **48 notas/camadas privadas** do estudo E2.7 (12 por American, Japanese, Felt e Upright) e a demo aprovada não estão no repositório. **Nenhum áudio do usuário é incluído no site ou enviado a servidores**: o navegador lê os arquivos por File API e decodifica com AudioContext na sessão. Após recarregar, importe novamente. Os arquivos de origem têm **direitos comerciais não comprovados**; esta integração não autoriza redistribuição do banco.

É um player de samples: escolhe raiz MIDI e camada nominal de velocidade, transpõe até 12 semitons. Sem sample ou raiz próxima, fica silencioso (sem síntese artificial substituta). Os marcadores v60/v110 são nominais e não certificam velocity real. O **V4 físico permanece independente, sem samples**. A/B/C/D e o motor D v1.12.8 continuam com DSP inalterado; históricos v1.12.6 e v1.12.7 não são editados.

## Verificação
Testes de regressão Node, seleção e migração, upload local e bancos por instrumento, roteamento sem sample para outros motores. A validação perceptiva do E no navegador e em hardware MIDI com os WAVs privados ainda é necessária.