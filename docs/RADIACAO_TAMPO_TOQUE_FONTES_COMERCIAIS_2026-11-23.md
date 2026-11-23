# Stage Synth — avaliação de radiador por posição, ação perceptiva e fonte CC0 Upright (23/11/2026)

**Tipo:** auditoria e preparação documental de pesquisa. **Nenhum DSP, MIDI, UI, FX, preset ou WAV do Stage alterado.**

**GitHub consultado antes desta mudança:** `main` commit `bfdc2478b95cd54d97ecdaa2e4c22015438e764c`, `package.json` v1.12.4, `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md`, `docs/PROXIMAS_ETAPAS.md` e protocolo M01–M09. A v1.9.5 permanece referência histórica de estabilidade *relatada*, e o motor A/B/C v1.12.4 **não** é promovido a estável. P1/P2 continuam congelados, sete R-GATEs globais integralmente bloqueados.

## 1. Evidência primária adicional e sua classificação

| ID | Fonte institucional/autoral | Evidência efetivamente verificada neste ciclo | Limite epistemológico e de direitos |
| --- | --- | --- | --- |
| N01 | Rolf Bader e Niko Plath, *Impact of Damping on Oscillation Patterns on the Plain Piano Soundboard*, **Acoustics** 2022, https://www.mdpi.com/2624-599X/4/4/62 , artigo **CC BY 4.0** | Medição de resposta do tampo em **14 pontos de excitação de ponte** em estágios de fabricação; T60 dos sinais acústicos de percussão aproximadamente 0,3 s no tampo bruto e 0,6 s no tampo pronto unido ao aro. A resposta depende do local de excitação e do estado de construção; tabela de coordenadas x/y dos 14 pontos publicada no texto. | São **medidas de som de tampo a impactos**, não tempos de decaimento das cordas, nem constantes universais; artigo e gráficos abertos não fornecem automaticamente séries brutas de força/velocidade complexa Yb(f). Não calibrar Stage somente com T60 ou gráficos. |
| N02 | Hans-Ulrich Berendes, Simon Schwär, Maximilian Schäfer, Meinard Müller, AudioLabs FAU/Fraunhofer IIS, *Towards Differentiable Piano Synthesis based on Physical Modeling* (2023), https://audiolabs-erlangen.de/resources/MIR/2023-ISMIR-PianoSynth/ | Medem **IR de um Yamaha C3** em quatro pontos usando alto-falante de contato sob o tampo, chirp 10 s / 20 Hz–20 kHz, captado por **par de microfones** com a tampa aberta. Os autores dizem que usaram apenas **uma IR** no protótipo, embora tenham medido quatro. | Captura inclui resposta de sala não anecoica; IR é resposta excitador elétrico→ar, **não mobilidade complexa da ponte v/F** nem F_h martelo. Não foram encontrados WAV originais de IR abertos/licença comercial neste ciclo; paper confirma procedimento, não dataset preparado. |
| N03 | Kaori Kuromiya, Yuya Kobayashi, Masato Hirano, Shinichi Furuya, *Motor origins of timbre in piano performance*, **PNAS** 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12501180/ ; dados: https://datadryad.org/dataset/doi:10.5061/dryad.95x69p8z3 | Experimento de movimento da tecla e percepção: velocidade/aceleração perto do escapamento, sobreposição de notas, intervalos entre teclas e ruídos de ação se relacionam com brilho/clareza/peso percebidos em testes controlados. O registro Dryad indica `data_study1.mat`, `data_study2.mat` e arquivos JSON de posição, e código MATLAB para figuras. | **O artigo é CC BY-NC-ND 4.0**; os **direitos do conjunto Dryad e de cada elemento não foram validados de forma independente**, logo NÃO usar o dataset para a calibração comercial por suposição. Relações perceptivas de performance não identificam F_h(t) ou Yb(f), nem provam modulação tímbrica livre para mesma força física. |
| N04 | Meta Creative Audio, `facebookincubator/Meta-open-sound`, https://github.com/facebookincubator/Meta-open-sound/tree/main/systems/instruments/meta-piano | **Manifesto original auditado via GitHub**: 352 nomes distintos WAV, todas as 88 notas A0–C8 presentes, quatro níveis pp/mp/mf/ff = 88×4; SFZ contém 352 regiões de amostras; `SHA256SUMS` tem 356 linhas (352 fontes WAV + quatro arquivos auxiliares). `manifest.json` declara **48 kHz, 24 bit**. `LICENSE` do instrumento é **CC0 1.0**, coerente com `catalog.json`. | Apenas **manifestos, arquivos textuais e licença** foram lidos. Não baixamos/verificamos WAV/ZIP/OGG, CRC, SHA256 real, duração, material original, microfone, velocity física, sala, normalização ou autenticidade da gravação de piano acústico; o nome “Meta Piano” e os quatro níveis não bastam para identificar equipamento. **NÃO acrescentar 352 ao acervo Stage de 50 WAV/FLAC originais validados**. É candidato comercial para benchmarking de piano vertical, não parâmetro físico. |
| N05 | Niko Plath/University of Hamburg, *Influence of Playing on the Tonal Characteristics of a Concert Piano* https://zenodo.org/records/3271370 | Reconfirmado arquivo `Data.zip` ~4,6 GB, com CSV 50 kHz sincronizando força de **tecla/base** [N], aceleração da **ponte** [m/s²] e pressão binaural [Pa] do mesmo piano em estados antes/depois de um ano de uso. | **Não é força de impacto direta na ponte**; dividir aceleração por força da tecla para obter “Yb=v/F” seria física incorreta. A versão da página exibiu campo Rights/License sem texto interpretável; **não foi verificada permissão comercial específica**. Não baixado/hasheado neste ciclo. |
| N06 | Hochschule der Künste Bern / MDW Vienna, `Bridge admittance measurements of a Moroccan rabāb`, https://zenodo.org/records/10079910 | Disponibiliza curvas **numéricas de magnitude, fase, partes real e imaginária** de medidas de ponte por martelo de impacto e acelerômetro, seis aquisições + média, arquivos `.via` ~871 kB. O procedimento define a conversão da resposta em aceleração para mobilidade em velocidade. | Instrumento é **rabāb, NÃO piano**. Pode servir apenas como exemplo de esquema de arquivos e validação dimensional, nunca parâmetros do Stage. Direito de reutilização comercial do corpus não confirmado; não baixado neste ciclo. |

### Auditoria textual reproduzível do Meta Piano (N04)

- Repositório: `facebookincubator/Meta-open-sound`, branch `main`.
- `systems/instruments/meta-piano/manifest.json`, blob SHA `9ffa15b7a00a7cdfe210fb062929118000a3786b`.
- `systems/instruments/meta-piano/README.md`, blob SHA `6fd3d271b14df110853e53488054c586ca57f695`.
- `systems/instruments/meta-piano/LICENSE`, blob SHA `0e259d42c996742e9e3cba14c677129b2c1b6311`.
- `systems/instruments/meta-piano/SHA256SUMS` declara checksums, **mas os bytes de WAV não foram verificados**.
- `catalog.json` declara CC0-1.0, e `meta-piano.sfz` traz o mapeamento por 352 samples.
- Confirmação estrutural: 352 arquivos distintos em manifesto, 88 pitch tags, 88 entradas por layer 01/02/03/04, 352 linhas `sample=` no SFZ e 356 linhas no SHA256SUMS.
- Verificar **proveniência acústica e captação** e passar pela etapa de download seguro/integridade só se esse candidato representar benefício sobre o Knight/Kawai/Felt já disponíveis; não usar modelo de piano desconhecido para calibrar timbre Yamaha CFX ou Steinway.

## 2. Implicações científicas para o Stage Synth

1. **Ponte/tampo (L03) — variação espacial é requisito de estudo, não sinônimo de filtro de reverb:** amostrar força e velocidade em ao menos regiões diferentes da ponte (graves, tenor e agudos, e pontos próximos de transição). N01 mostra por que um único `bodyFilter` para todas as notas simplifica demais o sistema. Se não puder medir 14 posições, justificar o número de pontos pelo piloto e reportar incerteza.
2. **Radiação sonora (M05) deve ser medida separadamente da mobilidade mecânica (M04):** N02 confirma que IR sonora de tampo inclui posição de microfone, alto-falante de contato e sala; NÃO equivale a `Y_bridge(f)` sem força instrumentada e sinal da velocidade na ponte. Comparações do Stage devem separar secura/corda, resposta de ponte e campo acústico/ambiente.
3. **T60 acústico de tampo não é o T60 por parcial da corda:** evitar ajustar `loopGain` por valores de percussão do tampo de N01. Perdas espectrais de cordas exigem vibração por parcial e notas com abafadores identificados.
4. **Ação e ruído (M09):** N03 sugere priorizar timing, velocidade/acceleração do escapamento e ruídos de tecla como dimensões **perceptuais** distintas. A entrada MIDI note-on/velocity não identifica o movimento contínuo da tecla; oferecer apenas o que o controlador realmente informa, sem inferir sensores inexistentes.
5. **Benchmark vertical:** N04 é possível nova referência com CC0 e cobertura de 88 notas, mas só se os arquivos reais, a origem, nível, microfone/edição e licença forem conferidos. A meta do Stage é fidelidade **sem necessariamente embarcar samples**.
6. **Calibração física e licenças:** R-GATE-2 segue insatisfeito; fontes N05/N06 NÃO resolvem FRF complexa de **piano** com força aplicada na própria ponte. Não classificar artigo publicado ≡ dados autorizados para derivar produto pago.

## 3. Preparação experimental do E1.1 — critérios escritos, sem programar o motor

**Testar primeiro os medidores, não o timbre.** Especificação de verdade conhecida:

- Sinais artificiais de parciais `f_n = n·f_0·sqrt((1+B·n²)/(1+B))`, com `B = 0, 0.0004, 0.0012, 0.003`, varrendo registros C2/C4/C6.
- Incluir individualmente e em combinações: duas/ três cordas com desafinação pequena e fases diferentes, H/V com dois decaimentos na **mesma parcial**, parciais de ataque que desaparecem antes de 180 ms, ruído de martelo, reverberação estéreo e truncamento; randomização reproduzível. Conferir que o algoritmo não confunde formantes de tampo com parciais de corda.
- **Separar duas métricas:** (a) f1/B/decay/partial tracking do **núcleo seco**; (b) imagem espectral/temporal da cadeia A/B/C **exatamente como no aplicativo**, FX off e ganhos equiparados. Uma cadeia não deve ser usada para julgar parâmetros da outra.
- Exigir relatório de erro, intervalo de confiança, falha/falso positivo por condição, sem introduzir “score de piano realista” deduzido de diferença em dB de canais/velocities não pareados.
- Protocolo FRF M04: medir `F_bridge(t)` e `a_bridge(t)` no mesmo ponto, sincronizados; calcular `H_af(f)=A(f)/F(f)`, integrar para mobilidade `Y(f)=H_af(f)/(j·2πf)` com banda útil, coerência, regularização apropriada, fase, unidades `(m/s)/N`, passividade física na frequência de interesse e incerteza por impactos. Nunca substituir `F_bridge` por `F_keybed`.
- Aceitação futura de modelos reduzidos: simular energia de sistema passivo, excitar com onda conhecida, medir erro de fase/magnitude de `Y(f)` e confirmar que a soma de modos compartilhados não adiciona energia; monitorar callback p95/p99 e underrun em Chrome/PC/Moto g04s, 32–64 vozes. **Não inventar tolerâncias dB ou p99 antes do piloto e de especificações de hardware**.

**Estado:** E1.1 definido metodologicamente mas **não executado**. O motor, os scripts de medição e os dados de áudio permanecem inalterados; não há aprovação dos R-GATEs por formalizar ensaios.

## 4. Próximos passos de evidência autorizada

- [x] Confirmar dependência de posição/estágio do tampo (N01) e a natureza não mecânica da IR Yamaha C3 (N02).
- [x] Incorporar evidência sobre movimento de tecla e timbre (N03), distinguindo publicação NC e direitos de dados não verificados.
- [x] Auditar metadados originais e CC0 de Meta Piano (N04) em 352 nomes, sem afirmar hashes dos WAV.
- [x] Qualificar N05 (força tecla/base ≠ força de ponte) e N06 (FRF de rabāb ≠ piano).
- [ ] Obter medições licenciadas de `F_h(t)`, compressão e rebote, junto a H/V e uníssonos (M01–M03).
- [ ] Obter medições do **próprio piano** de mobilidade complexa `Y_bridge(f)` por pelo menos regiões graves/tenor/agudos, controle de coerência e vibração radiada (M04–M05).
- [ ] Confirmar direitos comerciais dos corpora N03/N05/N06 **antes** de seu uso em calibração; se não necessário, manter somente bibliografia.
- [ ] Somente se necessário, auditar bytes originais CC0 do Meta Piano e origem acústica sem alterar o acervo de 50 até evidência plena.
- [ ] Executar E1.0/E1.1 **fora** do motor protegido quando o processo de preparação permitir; resultados medidos ≠ autorização para DSP.
- [ ] Passar R-GATE-1..7 e pedir autorização expressa ao titular; nenhum merge de novo DSP antes disso.

**Contabilidade sem inflação:** acervo de 50 gravações originais de seis pianos previamente verificado continua sendo o único conjunto contado como tal; nenhum WAV novo foi baixado/conferido nesta etapa. **0/7 R-GATEs integralmente aprovados**. A meta de 32–64 notas depende de testes físicos futuros, não de benchmarks isolados.
