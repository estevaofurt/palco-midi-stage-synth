# Reprovação técnica preliminar da camada aditiva de madeira — Stage D

**23/11/2026.** Feedback prioritário do titular depois de ouvir o Stage Synth v1.12.7: **"ainda está longe do som do piano real, parece estar faltando o som da madeira e os harmônicos. Continua parecido com um violão."**

**Regra:** A/B/C/Clássico, MIDI, FX, UI, presets, v1.12.6 e v1.12.7 publicados continuam **intactos**. Este ramo é uma PESQUISA ISOLADA e **NÃO DEVE SER INTEGRADO NO APP** enquanto não houver demonstração auditiva e fundamentação física. Repetir o erro de som de violão adicionando mais um falso "wood preset" não é progresso.

## I. Diagnóstico estrutural

O **D atual** sintetiza modos inarmônicos (cordas) e os soma diretamente às saídas L/R. O ramo usa `this.body.step(dryL*.65,dryR*.65)` e acrescenta `wet*.48`, mas a contribuição do corpo não é a verdadeira transformação dominante da força na ponte para pressão sonora irradiada. `dry` mistura modos transversais e ruído de mecanismo, **não** representa grandeza calibrada em m/s ou N. O estado `PianoResonanceBody.reaction` **não** retorna aos modos de corda. Portanto acrescentar simplesmente modos mais altos/mais reverb **não** equivale a um tampo de madeira real.

O grave também carece de **movimentos longitudinais e parciais fantasmas** (transverse→longitudinal não linear), porém incluir 2 ressonadores inventados em 1–4kHz **não calibra** sua afinação física, modos, excitação e intensidade. Fontes primárias:
- Ege et al., *Vibroacoustics of the piano soundboard: reduced models, mobility synthesis, and acoustical radiation regime*, https://arxiv.org/abs/1305.3057 — placa ortotrópica, densidade modal, ponte/impedância.
- Bank & Sujbert, *Generation of longitudinal vibrations in piano strings: from physics to sound synthesis*, https://pubmed.ncbi.nlm.nih.gov/15898667/ — mecanismos não lineares de parciais fantasmas, não apenas sumário do equalizador.
- Bank, Zambon & Fontana, *A Modal-Based Real-Time Piano Synthesizer*, https://home.mit.bme.hu/~bank/publist/taslp10.pdf — modos transversais + longitudinais, soundboard modelável por convolução/Filtros de segunda ordem.
- Ege et al., *Dynamical properties of piano soundboards*, https://pubmed.ncbi.nlm.nih.gov/23556610/ — radiação depende de campo de velocidade e filtragem espacial da ponte.
- Giordano et al., *Separation of piano keyboard vibrations into tonal and broadband components*, https://www.sciencedirect.com/science/article/pii/S0003682X0600137X — "knock" de banda larga diferente do espectro tonal, também no corpo.

## II. Experiência isolada efetivamente implementada

Ramo `experiment/stage-d-wood-longitudinal-bass-20261123`:
- `piano-bass-wood.js`: (A) banco compartilhado de 12 modos de radiador de placa amortecida, alimentado **somente pelos graves** e com pré-filtragem antialiasing antes da decimação; (B) dois modos quadráticos não lineares representando **apenas a hipótese** de componente longitudinal. Sem IR, sample, licença restrita ou importação de gravações originais.
- `physical-piano-hybrid.js`: comutação **OFF por padrão**, `wood`, `longitudinal`, `combined` apenas para estudos offline. A componente `wood` redistribui cerca de 17% do sinal direto dos graves para um radiador amortecido, mas seus parâmetros são **não identificados**. `off` reproduz v1.12.7 **bit a bit**; C4+ isolado permanece igual em TODOS os estudos.
- `physical-piano-hybrid-v127.js` é o **controle arquivado exato** e não modifica o motor original publicado.
- `tests/piano_bass_wood_longitudinal_experiment.test.mjs`: reprodução bitwise OFF em 63 cenários × 3 intensidades, proteção de C4+ em todos os experimentos, finitude e decaimento 2s do tampo, energia limitada e teste de 64 vozes.
- `scripts/render_bass_wood_longitudinal_abcd.mjs`: WAV 24 bits, estéreo 48kHz, com as **MESMAS** notas e o mesmo ganho linear; quatro modelos de ~19,5 s e comparador sequencial de ~80,7 s. Áudio do próprio Stage, sem Steinway ou outra gravação de terceiros.
- `.github/workflows/piano-bass-wood-experiment.yml`: **133/133 testes Node** aprovados, validação de cabeçalhos WAV, volume compartilhado e quatro casos diferentes; execução [45166377734](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45166377734).
- `.github/workflows/piano-bass-wood-iowa.yml`: 15 AIFF originais Iowa com SHA256 conferidos novamente, PCM removido do runner, artefato apenas numérico, execução [45166795332](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45166795332) bem-sucedida.

## III. Resultados reais — NÃO confundir mudança com melhora

**Resultados dos 15 originais Iowa Steinway B (5 notas C2..C6 × pp/mf/ff, mesmas âncoras calibradas, MIDI nominal NÃO calibrado e microfones/sala incluídos):**

| Experimento | Erro médio de parciais iniciais (dB) | Erro médio de parciais sustentados (dB) | Erro envelope grave 0–12ms (dB) |
| --- | ---: | ---: | ---: |
| D v1.12.7 controle | **4,3008** | **10,4920** | 2,9633 |
| + madeira aditiva | 4,9436 | 11,1556 | 2,6600 |
| + longitudinal quadrático | **4,2239** | **10,4508** | 2,9483 |
| + ambos | 4,8665 | 11,1235 | **2,6433** |

**Interpretação:** a "madeira" inventada muda o som mas **piora os espectros**. A redução de erro temporal do início não comprova maior naturalidade. Os modos longitudinais melhoraram menos de **0,08dB no erro inicial** e **0,05dB no sustentado**, alteração muito pequena para justificar lançamento. Essas medidas são **in-sample**, não avaliação cega nem estimação de impedância.

**Magnitude real das diferenças no comparador offline, RMS relativo ao D atual:**
- `wood`: **21,58%** (mudança ampla e não equivalente a fidelidade)
- `longitudinal`: **0,875%** (efeito mais sutil)
- `combined`: **21,68%** (dominado pelo novo radiador)

A avaliação subjetiva do usuário sobre se a madeira soa natural permanece **desconhecida**; não fazer publicidade ou declarar melhor piano real. **Decisão da auditoria: NÃO MESCLAR a experiência.**

## IV. Próximo modelo físico fundamentado — requisito antes de implementação

**Foco: construir transferência ponte→tampo→ar, não misturar modos de corda diretamente como se já fossem pressão acústica.**

1. Separar no D as variáveis ***força/velocidade da ponte*** (proxies dimensionalmente definidos) e saída irradiada para o alto-falante; impedir retorno positivo instável. O `dry` somado atual não é força.
2. Obter dados com **origem e licença comercial explícitas**: mobilidade/admitância da ponte, FRF de placa de madeira, função de radiação por região, transientes no corpo e relação pressão/velocidade. As gravações Iowa de saída microfonada, sozinhas, **não identificam essas funções**. Medição própria é alternativa.
3. Desenvolver modelo reduzido **passivo** de ponte, placa ortotrópica e modos densos de radiação, em vez de mais 12 ressonâncias arbitrárias. Modos transversais+longitudinais devem receber energia de um acoplamento causal não linear de corda.
4. Acrescentar o precursor/knock de banda larga pela via mecânica/ponte, mas calibrá-lo separadamente de ruído de tecla e ruído de sala; **não adicionar um clique arbitrário de madeira**.
5. Homologar em testes unitários de energia e frequências, matriz real (idealmente notas fora das âncoras), A/B ouvido pelo usuário, benchmark 32/64 vozes em PC/Moto g04s, CC64/corte de notas; não lançar sem escuta confirmada.

**Status do Stage público:** `main` permanece **v1.12.7** e seus controles A/B/C/D/Clássico continuam. R-GATEs **0/7 completos**; estudo não representa um produto comercial nem Steinway/Yamaha calibrados. O usuário relatou timbre de violão; **sem validação contrária, esse feedback é o critério decisório**.
