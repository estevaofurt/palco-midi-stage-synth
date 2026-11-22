# Stage Synth v1.12.4 — comparação de três motores de piano

Em **Piano Acústico → Motor do piano**, selecione **A · Claude (modal)**, **B · Stage físico anterior (v1.9.5)** ou **C · Novo Stage mecânico**. O modo Clássico permanece como compatibilidade. Os três motores A/B/C utilizam DSPs efetivamente distintos, e B preserva o código v1.9.5 como AudioWorklet independente. Não são novos módulos; são opções do piano acústico.

**Nota:** B é a implementação histórica v1.9.5 recuperada do repositório, **não** o Novo Stage v1.11.0 da outra conversa. O código original do chamado “Novo Stage v1.11.0” de outra conversa não foi encontrado no repositório. C integra mecânica à linha v1.9.5. São experimentos: a ausência de estalos na v1.9.5 foi relatada pelo usuário, e a comparação em hardware real precisa ser refeita.

# Stage Synth v1.12.3 — A/B dentro do Piano Acústico

Esta é a versão integrada do aplicativo, baseada na linha experimental v1.9.5 com o acoplamento mecânico v1.12.2. O motor está **dentro de Piano Acústico → Identidade e dinâmica → Motor do piano**, sem novo módulo, novo link ou botão dedicado.

- **A · Claude (modal):** motor modal já existente e derivado; não é uma cópia bit a bit do motor original de outra IA.
- **B · Novo Stage (mecânico):** motor físico da base v1.9.5 com retorno de ponte/tampo e cordas simpáticas da v1.12.2, usando o mesmo AudioWorklet. Não é o código-fonte da outra linha externa v1.11.0, ainda não localizada.
- **Clássico · compatibilidade:** motor pré-existente, preservado para contingência.
- O controle **Acoplamento mecânico**, dentro do próprio Piano Acústico, permite desligar a física adicional para comparação.
- A escolha do motor é persistida; o perfil Leve no celular não a sobrescreve. FX continuam sob demanda.
- Polifonia planejada: 32 (econômico) ou 64 (estúdio), não homologada em aparelho físico.
- **Status:** o usuário confirmou ausência de estalos na v1.9.5, não nesta integração; manter backup e fazer teste em PC/Moto g04s antes de promover como nova referência estável.

---

# Stage Synth — integração mecânica experimental v1.12.2

**Base do aplicativo:** `physical-v1.9.5` (a versão em que o usuário relatou estalos eliminados no PC). **Não é a fonte original da linha Novo Stage v1.11**, que ainda não está centralizada no GitHub. Este experimento pode ser usado como referência e ser portado à linha v1.11 quando seu código estiver disponível.

## O que é novo

- `physical-piano.js` importa `PianoResonanceBody` de `piano-resonance.js` e o executa **dentro do mesmo AudioWorklet** das cordas, sem ligação de feedback entre AudioNodes.
- A ponte recebe a vibração seca das cordas, o corpo simula 12 modos globais e duas ressonâncias simpáticas por tecla; a reação limitada retorna ao buffer da corda no passo seguinte.
- Estados de teclas repetidas preservam o amortecedor quando outra voz do mesmo pitch é liberada. Pedal CC64 é encaminhado ao núcleo físico.
- O editor do piano inclui **Acoplamento mecânico: Ponte, tampo e cordas simpáticas / Som anterior · comparar**. O bypass preserva o áudio antigo no teste isolado, com transição suave entre algoritmos.
- A ressonância antiga é progressivamente substituída, em vez de misturada como novo reverb externo. FX pesados continuam sob demanda como na v1.9.5.

## Como testar

Abra `index.html` num servidor HTTPS ou `localhost` com AudioWorklet disponível; selecione **Piano Acústico** > **Motor do piano: Cordas físicas** > **Acoplamento mecânico**. Alterne entre as duas opções durante uma nota ou acorde. Com o sustain acionado, as cordas abertas podem ressoar; com o pedal solto, os amortecedores reduzem as ressonâncias. Desative FX durante a comparação A/B.

- `npm run check`: sintaxe JS e suite completa (76 testes nesta revisão).
- `node tests/benchmark_mechanical_v122.mjs`: benchmark offline com 32/64 notas, modo anterior vs acoplado.
- `python tests/browser_mechanical_v122.py`: UI no desktop e Android simulado.
- `python tests/browser_worklet_v194.py`: teste opcional de AudioWorklet real no Chrome quando a origem localhost não estiver bloqueada pelo ambiente.

## Limitações explícitas

- **Ainda não é um piano realista:** não corrige inarmonicidade inadequada da linha de atraso, calibração apenas local à região média, nem perdas dependentes de frequência; não há garantia perceptual.
- A resposta mecânica e os coeficientes do corpo são **aproximações** ainda sem ajuste por notas secas de referência; não há um modelo completo de impedância real da ponte.
- Cada nota segue representada por uma ou duas linhas de atraso no motor físico. As 176 ressonâncias são **parciais simpáticas compartilhadas**, não 176 cordas de waveguide completas.
- O tempo por bloco foi medido offline em Node.js, **não** no Moto g04s físico ou Chrome real com interface de áudio. O navegador disponível neste ambiente bloqueia localhost (`ERR_BLOCKED_BY_ADMINISTRATOR`), portanto a execução real do AudioWorklet ficou pendente.
- **Mínimo requerido:** 32 notas; **meta:** 64 notas, a serem comprovadas com som sem estalos nos dispositivos reais.
- Presets e FX originais são preservados, mas importação de valores antigos de `localStorage` depende do navegador; a nova opção possui valor padrão em presets do experimento.
- WAVs do usuário não são redistribuídos nem embutidos.

## Integração real ao Novo Stage v1.11

A versão v1.11 do Novo Stage foi publicada em outro ambiente e seu código completo **não está na branch `main` deste repositório**. Antes de integrar este módulo à v1.11, será necessário localizar seu código atualizado, comparar APIs do processador e parâmetros MIDI e reexecutar os testes. Não renomear este experimento como se a integração tivesse sido realizada.

## Fontes do projeto

Documentação central: `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md`, `docs/PROXIMAS_ETAPAS.md`. Núcleo anterior: `experimental/mechanical-resonance-v1.12.1/`. Experimento estável-base: `experimental/physical-v1.9.5/`.

---

# Stage Synth v1.9.2 — teste de timbre físico

Esta é uma versão **experimental**, isolada da aplicação principal. A resposta à crítica de que o som ainda não se parece com um piano é uma mudança no processo de excitação, no equilíbrio harmônico e no decaimento. Não alegamos realismo final nem compatibilidade garantida com Moto g04s.

No editor Piano Acústico: escolha Motor do piano → Cordas físicas e Detalhe físico → Econômico (32 notas) para começar. A opção Estúdio mantém 64 notas, mas com carga maior. Para avaliar o timbre, desligue FX e mantenha somente o piano ativo.

Detalhes: `MOTOR_FISICO.md`. Código: `physical-piano.js`. Testes: `npm run check`, `node tests/benchmark_physical.mjs` e demos geradas em `demos/`.

A v1.9.1 e a versão principal do site permanecem inalteradas.

---

# Stage Synth v1.9.1 — motor físico experimental (32/64 notas)

Perfil **Leve:** mínimo de 32 notas MIDI simultâneas (uma corda waveguide por nota, ressonância de corpo compartilhada e modo de batimento leve). Perfil **Completo:** até 64 notas MIDI simultâneas; qualidade do motor **Estúdio** usa duas cordas waveguide por nota. Os limites são de alocação, não garantia de execução livre de falhas em hardware de entrada.

A excitação martelo/corda foi modificada para uma força de contato bipolar, com largura dependente da velocidade/dureza e posição do martelo; a saída recebeu headroom gradual para acordes densos. O timbre é prototípico, ainda não é o som realista de um piano de concerto. Não utiliza samples comerciais.

**Testes:** `npm run check` (45 testes de lógica) e `python tests/browser_physical_ui_v19.py`. Benchmark Node e demos podem ser regenerados com `node tests/benchmark_physical.mjs` e `node tests/render_physical_demo.mjs`. AudioWorklet real e Moto g04s físico não foram homologados.

---

## Stage Synth v1.8.4 — Modo Leve (Moto g04s)

Em Android, o aplicativo seleciona **Áudio: Leve · celular** automaticamente. Este perfil limita a polifonia a 8, desliga a modelagem modal e as convoluções de piano, usa menos osciladores, desliga oversampling e não instancia FX desativados. Os efeitos começam em bypass por motor na primeira abertura do perfil Leve e podem ser ativados individualmente. A seleção de tipo, roteamento e parâmetros permanece disponível. Para recuperar o áudio de 32 vozes e motor modal, escolha **Completo · computador**. Trocar de perfil reinicia o aplicativo e encerra as notas em andamento.

O modo Leve pode apresentar latência um pouco maior que o modo Completo. O áudio dependerá do navegador, da temperatura e do estado de bateria do celular. O perfil não garante eliminação de estalos com efeitos demais ligados.

# Stage Synth · Palco MIDI

Versão **1.8.2** — reconstrução dos seis módulos a partir dos arquivos originais recuperados do Palco MIDI. O antigo site no ChatGPT Sites permanece independente; este código é destinado ao GitHub Pages.

**Aplicativo:** https://estevaofurt.github.io/palco-midi-stage-synth/

## Seis módulos

1. **Piano acústico:** Japanese Grand (referência de caráter brilhante e articulado), American Grand (mais encorpado), Felt Piano, Piano Upright. Controles de dinâmica, dureza, Hammer Noise, Pedal Noise, string resonance (ativada/desativada), release, brilho, ambiente e amortecimento. Inclui importação local de amostras WAV por instrumento e diferentes camadas de intensidade.
2. **Pianos elétricos:** Rhodes Tine Mark I/II, Wurly Reed 200A/140B, CP70, Clav e E. Piano 1 (Full Tines), E. Piano 2 (Dino EP) e E. Piano 3 (Ballad Keys). Amplificador, microfone, preamp, **Auto-Pan com intensidade e velocidade**, tremolo, ruídos mecânicos e importação opcional de amostras WAV.
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


## v1.8.1 — Onde escolher os tipos de efeito
Abra o módulo **Efeitos**. Logo abaixo de **Reverb 1**, **Reverb 2**, **Delay 1**, **Delay 2**, **Modulação 1**, **Modulação 2** e **Equalizador**, aparece um seletor grande **TIPO DE ...**. Escolha o algoritmo antes de marcar os instrumentos atendidos pelo efeito. O Compressor tem um único tipo, sem seletor.


## v1.8.2 — acesso com cache separado

- Página versionada: https://estevaofurt.github.io/palco-midi-stage-synth/v1.8.2.html
- O rodapé apresenta a versão de fato carregada.
- CSS, módulo principal e importações locais usam identificação da versão no endereço dos recursos.
- Os instrumentos e efeitos são os mesmos da v1.8.1; nenhuma configuração salva é apagada.


## v1.8.3 — Proteção de saída e estabilidade do áudio

- Sinal que passa de 0 dBFS pode estalar, especialmente com camadas e retornos FX.
  A saída agora passa por `antclip.js`: ganho de segurança de 0,72 antes de
  saturação suave com teto matemático de 0,94 (oversampling 2x).
- Medidor passou a mostrar o sinal após a proteção, não antes dela.
- Respostas dos reverbs tiveram cálculo de cauda e reflexões iniciais otimizado;
  ajustes de tempo são arredondados a 0,1 s e reconstrutores são desacelerados
  para reduzir picos de CPU ao girar knobs.
- Motor modal usa no início 28 parciais e até 32 vozes internas, reduzindo custo.
- `v1.8.3.html` abre esta versão com importações versionadas.

**O que os testes provam:** em renderizações offline com acordes e múltiplos FX,
nenhuma amostra ultrapassou 1,0. Isso mitiga clipping digital, mas não comprova
que o hardware do usuário esteja livre de interrupções por CPU, driver ou latência.

## Experimental v1.9.0 — motor acústico original

O novo **motor `Cordas físicas · otimizado`** é um processador compartilhado de modelagem física por waveguide em `physical-piano.js`, em três níveis de qualidade. No perfil Leve, o Moto g04s tentará esse motor por padrão, caindo para a Síntese clássica se o AudioWorklet não iniciar. O modal antigo continua disponível no perfil Completo como comparação.

Esta **é uma experiência separada** da aplicação principal; a qualidade sonora ainda não foi aprovada por comparação auditiva. Veja [MOTOR_FISICO.md](./MOTOR_FISICO.md) para arquitetura, benchmarks, limites e próximos testes. As demos WAV originais deste protótipo ficam em `demos/`.

## v1.9.3 experimental — referência CFX

Recebemos uma gravação de referência do Yamaha CFX. O Japanese Grand foi recalibrado para ter harmônicos mais presentes nos agudos e ataque mais variável de acordo com nota e velocidade; **nenhum trecho do MP3 foi incorporado** ao projeto. Veja `CFX_REFERENCIA.md` para dados, método e limitações. O motor ainda não tem realismo acústico homologado e o Moto g04s físico não foi testado.

## v1.9.4 — calibração com quatro WAVs originais (experimental)

Esta versão calibra **Japanese Grand, American Grand, Felt Piano e Upright Piano** com espectros e envelopes independentes, extraídos de trechos sincronizados das referências fornecidas pelo usuário, contendo os efeitos originais dos instrumentos. **Nenhuma gravação é embutida no sintetizador.** Consulte `CALIBRACAO_194.md` e `CALIBRACAO_194.json` para as medições, ressalvas e limites de realismo.

- **32 notas** no Econômico, **48** no Equilibrado e **64** no Estúdio, como na versão anterior.
- Testes: `npm run check` e `python tests/browser_physical_ui_v19.py`.
- A publicação permanece separada em `experimental/physical-v1.9.4/`; a versão principal não é substituída.


## Experimento v1.9.5 — estabilidade e organização dos elétricos

- A síntese de cordas físicas é o padrão somente em sessões novas; sessões antigas mantêm suas preferências, que podem ser alteradas no seletor **Motor do piano**.
- EQ e compressor por insert, reverb, delay e modulações são montados sob demanda, quando ativos e roteados a um instrumento com FX habilitado. O piano físico não alimenta convoluções auxiliares duplicadas da versão anterior.
- Processamento das vozes físicas somente das notas ativas em cada bloco de áudio.
- **CP70** substitui CP80. **E. Piano 1 = Full Tines; E. Piano 2 = Dino EP; E. Piano 3 = Ballad Keys.** Sessões antigas CP80 são migradas para CP70 com preservação das edições.
- As identidades dos elétricos refletem as capturas de referência, mas a síntese ainda não foi recalibrada nesses timbres.
- Os testes de lógica passam; Chrome com AudioWorklet em origem local não pôde ser homologado neste ambiente por restrição do navegador. Não foi validado em PC ou Moto g04s físicos.
