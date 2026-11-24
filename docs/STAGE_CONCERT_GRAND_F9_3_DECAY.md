# Stage Concert Grand F9.3 — análise de sustentação e recorte PCM

Base imutável: dc44eae13caa3514d130a7f09e37f0ccf41c6452 (F9.2). F9 permanece aberta: timbre preliminarmente favorável, comparação independente com C5/V10, avaliação de sustentação e abafador físico pendentes. F10 não liberada. Nenhum DSP, parâmetros, arquivos de áudio de referência, main, UI, MIDI, FX ou presets alterados.

## Diagnóstico numérico
Dados de pressão RMS por segundo do manifesto F9.2, anteriores ao fade editorial. Referência relativa: RMS de 0–1 s, não pico. Regressões lineares em dB nos centros das janelas 0–3 s e 3–10 s: -9.378 e -3.879 dB/s, respectivamente; R² 0.997 e 0.971. Janela 4–5 s: -32.01 dB; 9–10 s: -49.80 dB. RMS decrescente em todas as dez janelas. Isso evidencia mudança de taxa de decaimento global no modelo, não prova dois mecanismos físicos isolados, sustain perceptivo suficiente, T60 de sala ou equivalência Yamaha. Os dados C5 publicados anteriormente usam outras janelas e níveis; não comparar diretamente nem calibrar com eles sem extração compatível. V10 continua sem WAV original acessível nesta sessão.

## Ferramentas e testes
- `node research/stage-concert-grand/f9-decay-analysis.test.mjs` — 12 verificações executadas em JavaScript V8 nesta sessão sobre o mesmo código, fixture PCM sintética; Node/CI não executados.
- `node research/stage-concert-grand/f9-excerpt.mjs research/stage-concert-grand/audio/C4_medio_R_10s.wav C4_medio_R_5s.wav` — utilitário local para recorte exato de 240000 frames, preserva cada amostra e ganho, não sobrescreve destino. Sem fade novo; final é corte editorial. Também mede RMS PCM por janela completa no original. Não foi executado no WAV real: o conector não retornou bytes binários. Não confundir utilitário com WAV efetivamente gerado.

Próxima validação: extrair PCM real, conferir SHA e comparar decaimento por parcial em janelas idênticas de C5/V10/Stage, com onsets alinhados e ganhos documentados, além de escuta do titular. Só então autorizar F10. Meta de 32–64 vozes continua pendente de hardware real.
