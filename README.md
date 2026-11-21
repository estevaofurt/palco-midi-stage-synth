# Palco MIDI · Stage Synth

Versão **1.1.0** — estabilização e recuperação do aplicativo Palco MIDI, usando o código fornecido pelo proprietário. O antigo site do Palco MIDI permanece independente.

**Site (GitHub Pages):** <https://estevaofurt.github.io/palco-midi-stage-synth/>

## Recursos implementados e testados

- Cenas, camadas dos quatro motores, volumes independentes e seleção de timbres
- Piano acústico sintetizado, piano elétrico, órgão com drawbars e sintetizador
- Teclado na tela, oitavas, sustain, comando de pânico e entrada MIDI Web MIDI (quando disponível)
- Editor de timbres com presets e preferências salvas localmente
- Interface responsiva, incluindo uma oitava de teclado em telas estreitas

## Instalação / desenvolvimento

É um site estático. Hospede a pasta na raiz de um servidor HTTPS, como o GitHub Pages (`main` / `root`). Para executar em um computador com Python instalado: `python -m http.server 8000` e abra `http://localhost:8000` no Chrome ou Edge. Abrir `index.html` por `file://` pode bloquear os módulos ES JavaScript.

**Testes de lógica:** instale Node.js 22+ e execute `npm test`.

**Testes com navegador:** a revisão funcional foi realizada com Chromium/Playwright, incluindo inicialização, teclado na tela, os quatro motores e layout móvel. Um teclado MIDI físico ainda precisa ser testado.

## Informações importantes

- **Biblioteca de piano ausente:** faltam os arquivos `piano/banco.json`, `piano/ataques.ogg` e gravações complementares. Por isso o motor acústico usa síntese de fallback. Não são feitas tentativas repetidas após constatar a ausência do banco.
- Não há dependências externas de bibliotecas de áudio para os quatro motores incluídos. Para carregar bibliotecas reais e estender o projeto com SF2/SFZ será necessária implementação específica.
- O módulo de efeitos avançados, o leitor SoundFont, o looper e o arpejador pertencem ao plano de expansão, **não** a esta versão estável.
- Conexões MIDI exigem navegador com suporte Web MIDI, permissão do usuário e controlador compatível.

Consulte [CHANGELOG.md](CHANGELOG.md) para as correções e limites verificados.