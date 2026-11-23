# Stage Synth — feedback auditivo do experimento de madeira e longitudinais

**23/11/2026 | etapa encerrada sem integração sonora.** O titular ouviu as quatro variantes do motor D e relatou: *“Soam praticamente iguais. Agora é possível ouvir um harmônico agudo junto à nota principal, mas ele está parecendo um ruído. Ainda não tenho sensação de madeira; o som ainda parece redondo.”*

**Decisão:** o efeito adicional agudo não foi identificado com segurança como harmônico musical, ruído mecânico ou vibração longitudinal. É inadequado reforçá-lo, alterar seus ganhos arbitrariamente ou afirmar que melhora o timbre. A sensação de `madeira` não deve ser implementada como reverb, equalizador genérico ou 12 frequências constantes inventadas. O experimento `wood/longitudinal/combined` foi **reprovado para lançamento**. Manter PR #26 em DRAFT, com parâmetros `bassStudy='off'` por padrão, e **manter a main em v1.12.7** (A/B/C/D/Clássico preservados).

## 1. Confirmação por análise direta dos WAVs, além da escuta

Os WAVs foram gerados com o mesmo MIDI, sem FX, com um único ganho compartilhado. O procedimento objetivo `scripts/measure_bass_abcd_similarity.mjs` produz `waveform_similarity_numeric_only.json`, usa PCM24 estéreo convertido em mono apenas para a medida, e inspeciona o intervalo **200–550 ms** depois do note-on; [CI 45169153078](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45169153078) — **133 testes Node aprovados**, 5 WAVs 24-bit validados e 7 notas × 3 variantes analisadas.

| Nota | Correlação com D atual: madeira | Correlação com D atual: longitudinal | Energia RMS com madeira vs D | Energia RMS longitudinal vs D |
| --- | ---: | ---: | ---: | ---: |
| C1 | 0,997193 | 0,999962 | 89,95% | 99,46% |
| A1 | 0,992894 | 0,999982 | 77,84% | 99,70% |
| C2 pp | 0,977136 | 1,000000 | 85,69% | 99,94% |
| **C2 mf** | **0,977792** | **0,999985** | **79,62%** | **99,74%** |
| C2 ff | 0,978246 | 0,999922 | 78,79% | 99,50% |
| **C3 mf** | **0,999397** | **0,999998** | **85,75%** | **99,92%** |
| C4 mf | 1,000000 | 1,000000 | 100,00% | 100,00% |

**Interpretação estrita:** correlação de ondas altas indica sinal **muito semelhante** nessas janelas — não uma medição de perceptibilidade nem identificação de fenômeno físico. O radiador chamado `madeira` diminuiu sobretudo o nível do material existente (especialmente C2 mf, ~20%) sem modificar sua estrutura de maneira suficiente para o usuário perceber um piano real. Longitudinal é virtualmente inaudível no WAV completo.

Medida adicional independente, Python/SciPy, `sosfilt` Butterworth 4ª ordem (sem ganho em bandas), intervalo **200–550ms**: razão RMS **1–4,5kHz** / **100–900Hz** para C2 mf: D **−34,40 dB**, madeira **−34,35 dB**, longitudinal **−34,40 dB**; para C3 mf: D **−25,0 dB**, madeira **−25,24 dB**, longitudinal **−24,98 dB**. A relação espectral quase não se alterou. Esses cálculos não isolam os primeiros 12ms do martelo, não provam causalidade e não fornecem resposta da placa.

### Característica do agudo que exige cautela

O protótipo `piano-bass-wood.js` fixa modos longitudinais em **`f=clamp(1400+49*(key-36),730,2150)`** e **`2f`**. Esses valores **não derivam** de comprimento, densidade, tensão, energia, condição de contorno ou modos longitudinais medidos, nem estão necessariamente associados aos parciais do piano naquela nota. Portanto, a contribuição **pode ser percebida como uma frequência solta/ruído**, mas **não foi provado** que seja ela o ruído agudo observado: o D anterior já gera parciais altos e ruído de tecla. Para investigar, capturar separadamente resíduo `experimental - baseline`, identificar transientes de ruído e parciais estáveis; reconhecer a frequência teórica real antes de adicionar ganho.

As fontes acústicas comprovam que vibrações longitudinais são excitadas de maneira não linear pelos movimentos transversais, mas o protótipo não representa a integral espacial da inclinação das cordas. A modelagem deve conservar o vínculo causal e energético com a vibração, em vez de criar senoides agudas soltas.

## 2. Referência nova — dados de PONTE e AR no mesmo instrumento

**Fonte promissora para o próximo modelo (direitos NÃO esclarecidos):**

- **Niko Plath (2019)**, [Influence of Playing on the Tonal Characteristics of a Concert Piano — Dataset, versão 1.0.1](https://zenodo.org/records/3274772), DOI 10.5281/zenodo.3274772. **50.000 amostras/s**, notas gravadas com sensor de **aceleração na ponte [m/s²]**, dois microfones de **pressão sonora [Pa]** e sensor de **força no teclado/apoio [N]**, em ambiente anecoico. O download completo tem aproximadamente **4,6 GB**. Não confundir a força do apoio da tecla com a força do martelo ou a força aplicada à ponte. A página exibe campo “License” sem licença explicitamente identificável: **NÃO AUTORIZAR uso comercial, redistribuição, treinamento comercial ou incorporação de parâmetros/áudio sem verificar os direitos junto ao titular**. Nem um sample desse dataset foi baixado ou incluído no Stage.
- **Berendes, Schwär, Schäfer & Müller, ISMIR (2023)**, [Towards Differentiable Piano Synthesis based on Physical Modeling](https://audiolabs-erlangen.de/resources/MIR/2023-ISMIR-PianoSynth/). Demonstram **banco de síntese modal + filtro linear** formado por medição da **resposta impulsiva de um Yamaha C3**, excitando o tampo por alto-falante de contato em quatro posições e captando pressão por microfones acima do piano; **não** equivalem a uma mobilidade de ponte ideal e contêm certa contribuição de sala. Os IRs não foram identificados como assets com licença comercial; **não incorporar** seu áudio ou código.
- **Boutillon & Ege (2013)**, [Vibroacoustics of the piano soundboard: reduced models, mobility synthesis, and acoustical radiation regime](https://www.sciencedirect.com/science/article/pii/S0022460X13002472). O timbre irradiado é produto de excitação pelas cordas, ponte e uma placa espacial; a mobilidade da ponte modifica decaimento e resposta.
- **Bank & Sujbert (2005)**, [Generation of longitudinal vibrations in piano strings](https://pubmed.ncbi.nlm.nih.gov/15898667/). Orienta modelagem de excitação longitudinal a partir da vibração transversal com modos físicos, não ressintonia de som de corda.
- **Julius O. Smith**, [Piano Synthesis / Nonlinear Strings](https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html): transientes iniciais por propagação longitudinal, diferença entre banco modal e radiação, importância de múltiplas polarizações e dos estados do martelo.

## 3. Próximo passo de engenharia: inverter a arquitetura, não somar efeitos

### Modelo proposto (em ramo separado, não como release)

```text
MIDI/tecla -> contato martelo F_h(t) -> modos de cordas transversais
                                      |   (polarizações / uníssono)
                                      v
                  reação na ponte <-> admitância mecânica passiva
                                      |
                                      v
            resposta espacial medida ou identificada do tampo
                                      |
                                      v
                  pressão acústica radiada + direcionalidade
```

* O som deve ser gerado prioritariamente por `ponte -> tampo -> ar`, enquanto uma eventual via direta das cordas recebe justificativa física e energética; não simplesmente somar filtros decorativos à mistura `dry`.
* Deixar `PianoResonanceBody.reaction` desconectada **até que sua unidade, sinal, passividade e estabilidade sejam validados**. O áudio atual não mede `força` ou `velocidade` de ponte; conectá-la como feedback não é física.
* Usar medidas **pareadas** de aceleração da ponte e pressão radiada para estimar **transferência empírica**, com janela por nota/posição, delay alinhado, regularização `H(f)=S_pa(f)/(S_aa(f)+λ)`, inspeção de coerência e erro em notas **não usadas no ajuste**. Esta é transferência **aceleração→pressão observada**, **não mobilidade mecânica força→velocidade**. A operação é exploratória e condicionada a direitos e dados.
* Experimentar **decaimento em duas fases** e polarizações sem inventar picos agudos; preservar C4–C6 bit a bit enquanto a nova cadeia grave é testada. Criar comparadores incluindo acústica real com teste ABX, não apenas 15 notas in-sample, e consumo de CPU em PC/Android.
* Não aumentar ruído de martelo nem tentar imitar madeira com reverb. Uma componente aguda só é aprovada se estiver vinculada a uma causa física, tiver frequência/cauda plausíveis, não soar como ruído e for aprovada pelo usuário.

## 4. Regra de liberação

**Não fazer merge da PR #26. Não declarar v1.12.8, não mudar default e não subir áudio arbitrário na versão pública.** A main v1.12.7 mantém as melhorias antes percebidas nos médios/agudos e a versão histórica v1.12.6 para comparação. Gates comerciais **0/7 integralmente fechados**.

**Aceite para o próximo experimento:** respostas de ponte e tampo rastreáveis (licença comercial aprovada ou medição própria), testes de passividade e saída sem notas presas, parciais medidos em diferentes tempos e intensidades, comparação independente sem degradação C4–C6, custo 32–64 vozes e avaliação auditiva explícita de grave com impressão de piano real.
