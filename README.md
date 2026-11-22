# Stage Synth · Palco MIDI

Versão **1.3.0** — reconstrução dos seis módulos a partir dos arquivos originais recuperados do Palco MIDI. O antigo site no ChatGPT Sites permanece independente; este código é destinado ao GitHub Pages.

**Aplicativo:** https://estevaofurt.github.io/palco-midi-stage-synth/

## Seis módulos

1. **Piano acústico:** Japanese Grand (referência de caráter brilhante e articulado), American Grand (mais encorpado), Felt Piano, Piano Upright. Controles de dinâmica, dureza, Hammer Noise, Pedal Noise, string resonance (ativada/desativada), release, brilho, ambiente e amortecimento.
2. **Pianos elétricos:** Rhodes Tine Mark I/II, Wurly Reed 200A/140B, CP80, Clav e FM Full Tines/Dino EP/Ballad Key. Amplificador, microfone, preamp, panorâmica, tremolo, velocidade e ruídos mecânicos.
3. **Órgão:** B3 Jazz/Gospel com nove drawbars, percussão, vibrato, Leslie parada/lenta/rápida e key click; Church Organ com registros diferenciados.
4. **Synth:** formas de onda senoidal/triangular/serra/quadrada/pulso, pulse width, oitava/semitons/fine tune, uníssono 1–3, ruído branco/rosa, mixer OSC, VCF low/high/band/notch, filtro com envelope, ADSR, LFO para pitch/cutoff/amplitude, matriz de modulação limitada, modos mono/poly/legato, portamento, volume/pan. Hard sync é uma **aproximação digital por wavetable**, não sincronização analógica genuína.
5. **Leitor SF:** instrumentos internos de cordas, bells, sopros, metais e coral; importação local de **SF2 PCM descomprimido** até 100 MB, seleção de programas do banco e reprodução de zonas simples com faixas de notas e velocidade. A importação permanece na memória da sessão; **não** há upload para servidor. Formatos SF3, SFZ, moduladores SF2 avançados e todos os tipos de zonas ainda não são compatíveis.
6. **Efeitos:** rack com oito sessões independentes: Reverb 1/2, Delay 1/2, Modulação 1/2, EQ e compressor. Cada motor possui botão **FX**, e cada sessão pode ser habilitada e endereçada a um motor.

### Recursos para tocar ao vivo

- Cenas e camadas dos cinco motores, volumes individuais, medidor de nível, máximo de 32 notas simultâneas, sustain e corte de som.
- MIDI via Web MIDI no Chrome/Edge e teclado virtual e de computador. MIDI físico ainda precisa ser homologado.
- **Arpejador** com BPM e divisão; **Chord Mode** maior, menor, sus2, sus4 ou quinta; **looper** de uma, duas ou quatro barras com gravação/reprodução em memória. Os loops não são persistidos ao atualizar a página.
- Presets, parâmetros de efeitos e preferências são salvos via `localStorage`; arquivos de SoundFont e loops não são salvos.

## Execução e testes

Site estático sem instalação de bibliotecas de áudio. Hospede a pasta na raiz do GitHub Pages (`main`/`root`) ou execute `python -m http.server 8000` e abra `http://localhost:8000` em navegador com Web Audio e, para MIDI, Web MIDI. A URL precisa ser HTTPS ou localhost para permitir acesso MIDI.

- Node.js 22+: `npm test` (testes de lógica, cenas, efeitos, arpejador, acordes e parser SF2).
- Chromium com Playwright: `python tests/browser_smoke.py` e `python tests/browser_stress.py` (inicialização, todos os módulos, carregamento de SF2 sintético, controles de áudio, MIDI simulado, polifonia, layout móvel).

## Transparência sobre áudio

Os modelos **Japanese Grand** e **American Grand** são perfis de síntese desenhados para sugerir características de pianos de concerto; **não são** gravações ou emulações oficiais da Yamaha CFX ou Steinway. A versão recuperada não incluía a pasta de amostras de piano licenciadas. Portanto, `piano-bank.js` utiliza o sintetizador de fallback e o site evita carregar arquivos ausentes. Para integrar um banco de amostras original autorizado, instale os ativos e altere `<meta name="palco-piano-bank" content="synthetic">` para `content="samples"`.

A fidelidade dos timbres sintéticos depende de futura melhoria de modelagem e/ou inclusão de bibliotecas de amostras licenciadas. Por enquanto, a homologação foi feita com navegador de testes, não com um controlador e sistema de som reais.
