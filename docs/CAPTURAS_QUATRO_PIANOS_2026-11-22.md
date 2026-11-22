# Stage Synth — Capturas de referência dos quatro pianos (22/11/2026)

As referências foram fornecidas pelo usuário no desenvolvimento do motor próprio de modelagem física: `Japanese.wav`, `American.wav`, `Felt.wav` e `Upright.wav`.

**Não incluir os quatro arquivos WAV no repositório:** têm aproximadamente 98 MB cada e destinam-se apenas à análise e calibração; não presumir direitos de redistribuição.

## Formato e condições

- Todos os arquivos: WAV PCM 24-bit, 44.000 Hz, 2 canais, 386,911 s.
- Eventos sincronizados no tempo; o mesmo trecho pode ser comparado entre os quatro timbres. Não foi confirmado se os efeitos externos estavam desligados.
- As comparações por janela não equivalem à medição de uma única corda sem reverberação.

## Medições

| Piano | Pico digital | RMS global (dBFS) | Correlação L/R | Amostras no teto | Segundo harmônico vs fundamental, trecho ~82,9s |
|---|---:|---:|---:|---:|---:|
| Japanese | 0,629 | -31,47 | 0,57 | 0 | +4,5 dB |
| American | 0,713 | -31,38 | 0,56 | 0 | -14,8 dB |
| Felt | 0,555 | -31,60 | -0,12 | 0 | -10,1 dB |
| Upright | 1,000 | -26,89 | -0,18 | 71 | -3,3 dB |

Os harmônicos acima se referem a uma passagem de registro médio próxima de 262 Hz (não são constantes do instrumento). A comparação espectral foi feita com FFT e janela Hann de aproximadamente 0,45 s, buscando máximos perto dos múltiplos da fundamental. Há possibilidade de mistura com reverberação e notas anteriores.

Na passagem iniciada aproximadamente em 70,8 s, entre janelas relativas de 1,0–1,5 s e 2,2–2,7 s, a queda RMS foi:
- Japanese: -6,8 dB
- American: -8,1 dB
- Felt: -14,1 dB
- Upright: -11,8 dB

A medição não é T60 nem tempo físico exato de amortecimento, pois note-off, pedal e efeitos não estão documentados.

## Pontos de atenção

1. **Felt:** silêncio significativo no início, até aproximadamente 20 s. Verificar a extensão pretendida do instrumento em vez de sintetizar graves que a referência não contém.
2. **Upright:** 71 amostras em amplitude ±1; para calibração de ataques fortes, considerar nova captura com pelo menos 3 dB de headroom.
3. **Felt e Upright:** correlação L/R média negativa. Testar soma mono no Moto g04s; o número sozinho não comprova erro de fase.
4. Evitar interpretar diferenças do nível RMS global como características timbrais sem igualar volumes e registrar as velocidades MIDI.
5. Se os efeitos de reverb, chorus, EQ ou compressor estavam ativos na captura, separá-los do comportamento do piano antes de ajustar os parâmetros físicos.

## Processo de desenvolvimento

- Identificar notas e velocidades conhecidas, separar transientes e corpo e calcular envelopes/espectros por região de teclado.
- Ajustar submodelos específicos por instrumento: martelo, rigidez, posição de impacto, cordas acopladas, amortecimento frequencial, ponte/tampo e release.
- Comparar sintetizador e capturas com a mesma sequência MIDI e níveis igualados; evitar simples EQ global.
- Preservar o motor sem samples: estas capturas servem como **referência**, não como banco sonoro embutido.
- Otimizar o AudioWorklet para um mínimo funcional de 32 vozes, com 64 como meta e verificação em Moto g04s físico.

**Situação:** referências analisadas e métricas iniciais registradas. Calibração objetiva do motor e validação auditiva ainda não concluídas.
