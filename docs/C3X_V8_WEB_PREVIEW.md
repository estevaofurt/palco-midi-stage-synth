# Stage Synth — Yamaha C3X V8 Web · Prévia

**23/11/2026.** O usuário pediu integrar o piano V8 e remover A/B/C/D.

## Proveniência e limite fundamental

O **V8 Python original** está em um ZIP separado, `Stage_Synth_C3X_Etapa_08.zip` (referenciado pelo projeto, mas **não está no repositório web ou disponível como arquivo nesta execução**). Sua afinação 88/88, otimização de integrador, timbre dry e 92 testes são resultados da implementação Python, **não são transferidos automaticamente ao navegador**.

A nova página `v8-preview.html` usa um **motor Web Audio físico independente, escrito para esta prévia**. Ele respeita o desenho de martelo/feltro, modos de cordas inarmônicos, tampo harmônico com saída dry e abafamento dinâmico CC64, e pré-calcula coeficientes por nota. **Não é uma transcrição nem reprodução numericamente idêntica do código V8 Python, e o timbre NÃO está homologado por escuta.** Não usar o nome “V8 finalizado” ou prometer a afinação/benchmark da Etapa 8 neste protótipo.

## Escopo e entrega

- Página separada `v8-preview.html` no mesmo Stage, com **somente Yamaha C3X V8 Web (prévia)** no módulo Piano acústico; sem seletor A/B/C/D/E/Clássico.
- Não importa nenhum DSP antigo nem samples de piano; não tem reverb de sala interno. Rack FX permanece independente, desligado por padrão.
- Preservados os demais módulos Electric/Organ/Synth/SF2, teclado virtual, MIDI, sustain, presets de outros instrumentos, arpejador, chord mode e looper.
- Site principal `index.html` permanece intacto até teste perceptivo e paridade com o Python V8 original. Arquivos históricos preservados como backup.
- Testes `node --test tests/v8_web_preview.test.mjs`, mais suíte antiga, checam notas, energia, pedal, polifonia declarada e isolamento. 32/48/64 vozes ainda carecem de validação em hardware real.

## Próximos critérios para o V8 original

Com o código Python da Etapa 8, traduzir integrador, forças de martelo, massas, acoplamentos, tampo e pedal sem alteração de parâmetros. A/B PCM nas mesmas notas/velocidades sem FX, auditoria de afinação 88/88, dinâmica, decaimento, CPU real, escuta humana, e só então substituir `index.html`.
