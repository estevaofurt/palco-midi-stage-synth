# Palco MIDI — Stage Synth

Projeto independente recuperado a partir dos arquivos fornecidos pelo proprietário. Este repositório **não substitui e não altera o site Palco MIDI anterior**.

## Site

Quando o GitHub Pages estiver habilitado para a branch `main`, usando a pasta `/ (root)`, o endereço será:

`https://estevaofurt.github.io/palco-midi-stage-synth/`

> Esse endereço só funciona depois que o repositório existir, os arquivos forem enviados e o GitHub Pages for ativado.

## Recursos recuperados

- Interface e estilo visual originais (`index.html`, `panel.css`)
- Controle de cenas, teclado virtual e MIDI (`app.js`, `patches.js`)
- Motor de áudio (`stage.js`, `voice.js`)
- Instrumentos piano acústico/elétrico, órgão e synth
- Editor de timbres (`panel.js`)

## Executar

Hospede em HTTPS (GitHub Pages é adequado). Para testar localmente: `python -m http.server 8000`, abrindo `http://localhost:8000` no Chrome/Edge. Abrir diretamente `index.html` usando `file://` pode bloquear imports JavaScript e MIDI.

## Limitações conhecidas

- As amostras opcionais do piano, normalmente disponíveis na pasta `piano/`, **não foram recuperadas**. O motor utiliza síntese alternativa.
- A conexão MIDI depende do navegador, permissões e hardware do usuário.
- Os seis módulos expandidos da futura versão Stage Synth ainda **não** estão incluídos neste projeto recuperado.
- Não houve validação final com teclado MIDI físico.

## Publicação

No GitHub, acesse **Settings → Pages**, selecione **Deploy from a branch**, escolha `main` e `/ (root)` e salve. Mantenha o repositório público caso o plano GitHub exija isso para Pages.

## Preservação

O arquivo `creditos.html` descreve a procedência e as limitações do áudio. Arquivos originais do projeto antigo não são modificados.
