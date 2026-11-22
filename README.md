# Stage Synth · Palco MIDI

Versão **1.5.0** — reconstrução dos seis módulos a partir dos arquivos originais recuperados do Palco MIDI. O antigo site no ChatGPT Sites permanece independente; este código é destinado ao GitHub Pages.

**Aplicativo:** https://estevaofurt.github.io/palco-midi-stage-synth/

## Seis módulos

1. **Piano acústico:** Japanese Grand (referência de caráter brilhante e articulado), American Grand (mais encorpado), Felt Piano, Piano Upright. Controles de dinâmica, dureza, Hammer Noise, Pedal Noise, string resonance (ativada/desativada), release, brilho, ambiente e amortecimento. Inclui importação local de amostras WAV por instrumento e diferentes camadas de intensidade.
2. **Pianos elétricos:** Rhodes Tine Mark I/II, Wurly Reed 200A/140B, CP80, Clav e FM Full Tines/Dino EP/Ballad Key. Amplificador, microfone, preamp, **Auto-Pan com intensidade e velocidade**, tremolo, ruídos mecânicos e importação opcional de amostras WAV.
3. **Órgão:** B3 Jazz/Gospel com nove drawbars, percussão, vibrato, Leslie parada/lenta/rápida e key click; Church Organ com registros diferenciados.
4. **Synth:** formas de onda senoidal/triangular/serra/quadrada/pulso, pulse width, oitava/semitons/fine tune, uníssono 1–3, ruído branco/rosa, mixer OSC, VCF low/high/band/notch, filtro com envelope, ADSR, LFO para pitch/cutoff/amplitude, matriz de modulação limitada, modos mono/poly/legato, portamento, volume/pan. Hard sync é uma **aproximação digital por wavetable**, não sincronização analógica genuína.
5. **Leitor SF:** instrumentos internos de cordas, bells, sopros, metais e coral; importação local de **SF2 PCM descomprimido** até 100 MB, seleção de programas do banco e reprodução de zonas simples com faixas de notas e velocidade. A importação permanece na memória da sessão; **não** há upload para servidor. Formatos SF3, SFZ, moduladores SF2 avançados e todos os tipos de zonas ainda não são compatíveis.
6. **Efeitos:** rack com oito sessões independentes: Reverb 1/2, Delay 1/2, Modulação 1/2, EQ e compressor. Cada motor possui atalho **FX/FX OFF** para desligar somente seus efeitos, sem apagar endereçamentos; cada sessão pode ser endereçada simultaneamente a vários instrumentos.

### Recursos para tocar ao vivo

- Cenas e camadas dos cinco motores, volumes individuais, medidor de nível, máximo de 32 notas simultâneas, sustain e corte de som.
- MIDI via Web MIDI no Chrome/Edge e teclado virtual e de computador. MIDI físico ainda precisa ser homologado.
- **Arpejador** com BPM e divisão; **Chord Mode** maior, menor, sus2, sus4 ou quinta; **looper** de uma, duas ou quatro barras com gravação/reprodução em memória. Os loops não são persistidos ao atualizar a página.
- O menu **Instrumento** escolhe o modelo sonoro; **Preset** carrega configurações Natural, Suave ou Brilhante daquele instrumento. Configurações são salvas via `localStorage` e sinalizadas com `*` quando modificadas. Arquivos SoundFont, WAV e loops não são salvos; importe-os novamente ao abrir outra sessão.

## Execução e testes

Site estático sem instalação de bibliotecas de áudio. Hospede a pasta na raiz do GitHub Pages (`main`/`root`) ou execute `python -m http.server 8000` e abra `http://localhost:8000` em navegador com Web Audio e, para MIDI, Web MIDI. A URL precisa ser HTTPS ou localhost para permitir acesso MIDI.

- Node.js 22+: `npm test` (testes de lógica, cenas, efeitos, arpejador, acordes e parser SF2).
- Chromium com Playwright: `python tests/browser_smoke.py` e `python tests/browser_stress.py` (inicialização, todos os módulos, carregamento de SF2 sintético, controles de áudio, MIDI simulado, polifonia, layout móvel).

## Transparência sobre áudio

Os modelos **Japanese Grand** e **American Grand** são perfis de síntese desenhados para sugerir características de pianos de concerto; **não são** gravações ou emulações oficiais da Yamaha CFX ou Steinway. A versão recuperada não incluía a pasta de amostras de piano licenciadas. Portanto, `piano-bank.js` utiliza o sintetizador de fallback e o site evita carregar arquivos ausentes. Para integrar um banco de amostras original autorizado, instale os ativos e altere `<meta name="palco-piano-bank" content="synthetic">` para `content="samples"`.

A fidelidade dos timbres sintéticos depende de futura melhoria de modelagem e/ou inclusão de bibliotecas de amostras licenciadas. Por enquanto, a homologação foi feita com navegador de testes, não com um controlador e sistema de som reais.

## Amostras e limites de qualidade sonora

A interface de importação de WAV por instrumento foi retirada nesta versão, conforme solicitado. O Leitor SF continua aceitando bancos SF2 PCM. O motor modal é uma aproximação experimental de piano, não um modelo acústico validado contra gravações profissionais.

**Validação v1.4:** `npm run check` executa 17 testes de lógica; `python tests/browser_v14.py` valida layout entre 390 e 1600 px, presets, Auto-Pan e upload WAV; `python tests/browser_stress.py` valida 60 notas MIDI simuladas, sustain, modo Duo e corte de som. Teclado físico e qualidade acústica subjetiva ainda precisam de testes em campo.


## v1.5.0 — Experimental

- Piano Acústico: motor modal em `AudioWorklet` (alocação de vozes e ressonância auxiliar). `Síntese clássica` segue disponível como fallback. Ainda não reproduz o realismo de um piano de concerto; não há amostras comerciais incluídas.
- Rack FX: cada sessão recebe uma seleção **múltipla** de instrumentos. O botão **FX** de cada módulo continua sendo bypass próprio; desligá-lo mantém o som original daquele instrumento, sem silenciar os demais.
- Configurações antigas do rack com destino único são migradas automaticamente.
- A interface de upload manual de WAV foi ocultada nesta iteração, mantendo a importação SF2 no Leitor SF.

### Edição v1.5.0

- **Clique duplo em knobs, drawbars, sliders de volume ou controles deslizantes do rack:** restaura o valor inicial do preset ou do efeito.
- Alterações de filtros, Leslie, drawbars, Auto-Pan, tremolo, Synth (filtros/ondas/LFO) e FX são enviadas ao motor durante a execução. Alguns parâmetros físicos de ataque (martelo/dinâmica) só afetam notas iniciadas depois da alteração.
- O botão **FX** de cada motor é um atalho para ativar/desativar a influência do rack inteiro *naquele motor*, preservando valores e destinos. Efeitos com caudas (reverb/delay) podem continuar decaindo por um instante após o bypass.

## v1.8.0 — Controles durante notas sustentadas

O painel agora atualiza as vozes em execução ao mover knobs/seletores de timbre contínuos. A modificação ocorre de forma suavizada, sem reiniciar as notas. Entre os controles validados estão Pickup do elétrico, abafamento do piano, drawbars do órgão, afinação/volume/ruído/sustain do Synth e brilho/release do Leitor SF. O bypass FX por módulo e o endereçamento múltiplo seguem independentes.

**Limites físicos:** tocar mais forte, modificar o impacto inicial do martelo ou acrescentar novas cordas/osciladores a uma nota já atacada exigiria reconstruir o ataque. Assim, ruídos de ataque, velocity e contagem de uníssono só mudam na próxima nota. Mudar o tipo de instrumento ou preset é estrutural; filtros e parâmetros contínuos correspondentes passam a atuar nas vozes existentes, mas a fonte sonora original não é substituída enquanto toca.

**Testes:** `npm run check`; `python tests/browser_live_v16.py`; `python tests/browser_v15.py`; `python tests/browser_stress.py`. A calibração auditiva com controlador MIDI físico e a execução de `AudioWorklet` em HTTPS real continuam pendentes.


## Stage Synth v1.8.0 — Organ B3 e síntese ao vivo

- Órgão: seletor **B3 Jazz / B3 Gospel / Church Tubos** independente dos presets Natural, Suave e Brilhante.
- Atualização do registro e drawbars em notas sustentadas; migração automática dos ajustes de versões anteriores (sem apagar presets salvos).
- Synth: agora o **Uníssono 1/2/3** funciona durante notas sustentadas, adicionando osciladores com fade-in e silenciando os excedentes ao reduzir o número de vozes.
- Matriz de modulação com **Velocity e Aftertouch** pode ser reconfigurada em tempo real.
- **Portamento** agora também atua no modo Polifônico, entre notas consecutivas do mesmo controlador/canal. O controle de tempo afeta a próxima transição entre notas, e não desloca a altura de uma nota imóvel.
- Ao trocar de Polifônico para Mono/Legato, notas extras em andamento são liberadas.
- Panic e desconexão MIDI limpam o histórico de notas do glide.
- 27 testes de lógica e testes de navegador específicos para seleção, glide, uníssono, matriz e panic.

**Limites:** uníssono dinâmico aumenta uso de CPU nas notas ativas; testar em controladores físicos e celulares antes de uso ao vivo. O código não transforma timbres modelados em amostras de piano real.

## Rack de efeitos v1.8.0

O rack preserva oito sessões independentes: Reverb 1/2 (Hall, Room, Plate, Spring, Church e Shimmer aproximado), Delay 1/2 (Tape, Analog e Digital), Mod 1/2 (Chorus, Flanger, Phaser e Wah-Wah automático), Equalizador (paramétrico de 3 bandas ou gráfico de 7 bandas) e Compressor.

Cada sessão pode endereçar vários motores e o botão FX do motor elimina todos os efeitos de sua saída, sem alterar os outros instrumentos. EQ e compressor operam como inserts de sinal completo (mix 100% em novos presets); nos valores intermediários, o mix permite processamento paralelo intencional.

**Compressor:** Threshold (-50–0 dB), Ratio (1–16), Attack (1–200 ms), Release (20–1000 ms), Knee (0–30 dB) e Makeup (-12 a +18 dB). O compressor master de proteção da saída continua separado. Recomenda-se começar com Threshold -18 dB, Ratio 3:1, Attack 10 ms, Release 200 ms e Makeup 0 dB, evitando clipping ao elevar Makeup.

O tipo Shimmer utiliza uma resposta harmônica brilhante, sem transposição de oitava genuína. Para obter um shimmer convencional com pitch shift +12 semitons em feedback será necessária implementação dedicada posterior.
