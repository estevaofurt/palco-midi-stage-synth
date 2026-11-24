# Stage Synth — C3X V8 Web 1.13.2 (sem motor sampleado)

## O que foi alterado em 24/11/2026
Pedido do usuário: **retirar o modelo de samples, pois a implementação E não funcionou bem**. A página ativa de prévia `v8-preview.html` voltou a expor **apenas o motor C3X V8 Web físico e dry**. Não há motor E, carregamento local de WAVs, banco de amostras, opções A/B/C/D nem menu de comparação nessa prévia. Foram restaurados os módulos `app-v8-web.js`, `acoustic-v8-web.js`, `patches-v8-web.js` de uma revisão anterior à integração do E; o import map também deixa de referenciar `sample-library.js`. São mantidos teclado virtual, MIDI/CC64, perfis, cenas, efeitos, Electric, Organ, Synth e SF2.

## Restrição crítica do motor V8 original
O usuário informou que o pacote `Stage_Synth_C3X_Etapa_08.zip` **está disponível na conversa anterior**. A referência textual a `sandbox:/mnt/data/Stage_Synth_C3X_Etapa_08.zip` foi recuperada do histórico. Porém, **o arquivo não está montado na sessão atual, não aparece na Biblioteca nem no repositório GitHub**. Portanto, **não foi possível abrir, comparar, compilar nem portar a implementação Python original**.

O módulo `piano-c3x-v8-web.js` é uma modelagem física experimental de navegador; o usuário já relatou que **não corresponde ao timbre integral do V8 original**. Esta alteração **não afirma recuperar tal timbre nem equivalência com os testes/afinação V8 Python**. O código original precisa ser fornecido como anexo acessível ou adicionado ao repositório para portar fielmente o DSP, comparar PCM e afinação 88 notas e validar a escuta.

## Preservação
A antiga página principal `index.html` v1.12.10 permanece inalterada como versão histórica legada. Isso inclui implementações antigas A/B/C/D/E; **não confundir a rota histórica com a prévia V8-only**. A remoção do motor de samples aqui se aplica à **página V8 ativa `v8-preview.html`**, não é exclusão irreversível de históricos de projeto.

## Validação
`node --test tests/v8_web_preview.test.mjs` e `npm run check` (quando executados pelo CI) garantem que a prévia usa apenas o C3X V8 Web, sem caminho sampleado, e que as versões históricas continuam testáveis. Escuta no navegador, CPU real 32/48/64 vozes, e paridade com Python V8 não estão homologadas.
