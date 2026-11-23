# PIANO V4 — MEDIDAS REAIS E DOCUMENTADAS DE PIANOS DE CAUDA YAMAHA

**Data de pesquisa:** 23/11/2026. **Tipo:** levantamento bibliográfico e auditoria de parâmetros, **sem mudança de motor**. **Branch:** `research/piano-v4-restart-physical-20261123`, PR #39 draft. O Stage público permanece inalterado.

## 1. Qual Yamaha escolher para fundamentar a V4?

**Sugestão de instrumento de referência de pesquisa:** **Yamaha Disklavier C6** (geração histórica empregada em laboratório, NÃO confundir com C6X). É o modelo Yamaha com a evidência pública mais valiosa encontrada para **cordas, amortecimento e velocidade de martelo sincronizada**, inclusive medições feitas ao longo do teclado.

**Instrumentos complementares — NÃO intercambiar parâmetros como se fossem o mesmo piano:**
- **Yamaha C7 grand:** impedância mecânica complexa da ponte grave e frequências de vibração do tampo medidas por impacto instrumentado (Espanha, 2008).
- **Yamaha Disklavier DC7M4Pro:** distribuição espacial da radiação do **Dó central C4**, três intensidades e mais de 450 pontos de microfone (EUA/NYU, 2013).
- **Yamaha Disklavier DC3 M4:** áudio binaural e vibração do teclado em dez intensidades (BiVib/Itália 2019); **gravações de referência APENAS para análise, nunca reprodução pelo motor físico**.
- **Yamaha C3/C3X:** especificações externas oficiais e relatos técnicos; **nenhuma ficha de fábrica verificada foi encontrada com tensão, comprimento vibrante e massa do martelo C4 de um C3X atual**. Uma tabela fornecida por técnicos na PTG em março/2026 declara explicitamente **incerteza quanto a ser realmente de um C3**, portanto **NÃO é uma escala calibrada do C3X**.

## 2. Medidas oficiais de modelos atuais: dimensões EXTERNAS

**Fonte Yamaha Brasil:** https://br.yamaha.com/pt/musical-instruments/pianos/explore/size-comparison/

| Modelo | Comprimento | Largura | Altura | Peso | Origem |
|---|---:|---:|---:|---:|---|
| C3X | 186 cm | 149 cm | 101 cm | 320 kg | fabricante, atualizado |
| C6X | 212 cm | 154 cm | 102 cm | 405 kg | fabricante, atualizado |
| C7X | 227 cm | 155 cm | 102 cm | 415 kg | fabricante, atualizado |
| CFX | 275 cm | 160 cm | 103 cm | 485 kg | fabricante, atualizado |

**ATENÇÃO:** comprimento externo do móvel **NÃO** é comprimento vibrante de uma corda C4. Peso total **NÃO** é massa vibratória do tampo ou massa efetiva na ponte. Os modelos históricos C3/C6/C7/Disklavier não são idênticos às séries CX e CFX atuais, mesmo que os tamanhos se aproximem.

## 3. Yamaha Disklavier C6 — referência primária com sensores, Marselha/Stanford (2003)

**Artigo primário integral:** Julien Bensa, Stefan Bilbao, Richard Kronland-Martinet e Julius O. Smith III, *The simulation of piano string vibration: From physical models to finite difference schemes and digital waveguides*, *JASA* **114(2)**, 1095–1107 (2003), DOI **10.1121/1.1587146**.

PDF publisher's version via University of Edinburgh: https://www.pure.ed.ac.uk/ws/files/11222473/1.1587146.pdf

**Instrumento utilizado na etapa experimental:** **Yamaha Disklavier C6 grand**, Laboratoire de Mécanique et d'Acoustique, Marselha, França.

**Medido diretamente ou adquirido em sinais:**
- Sensor óptico MTI 2000 (probe 2125H) próximo ao martelo mede **velocidade do martelo** pela passagem de dois refletores.
- Escolhido martelo em cerca de **2,2 m/s**, aproximadamente **MIDI 80**, média mf **desse Disklavier/ensaio**, com tolerância desejada **±0,1 m/s**. Não converter 80 MIDI em 2,2 m/s para qualquer Yamaha por fórmula universal.
- Acelerômetro B&K 4374 junto à **ponte no ponto da corda**; coleta **44.100 amostras/s, 16 bit** para estimar frequências de parciais, inarmonicidade B e amortecimento. Em multi-corda a aceleração contém vibração de cordas e ponte acopladas, não propriedades de uma corda desacoplada.
- Outros sinais (vibrometria laser e microfone de cabeça artificial) foram adquiridos no laboratório, mas **o artigo trata principalmente os sinais de aceleração**; **não afirma que o PDF publica todos os WAVs/dados brutos ou tabelas por cada uma das 88 teclas**.
- Frequência modal de parciais, B por nota e duas taxas de perda (b1/b2) ajustadas por análise de sinais. A perda equivalente combina corda, ponte, uníssonos/polarizações (dependendo da nota), **não** apenas dissipação intrínseca de fio de aço.

### 3.1 Fórmulas ajustadas às medições C6 e seu alcance

O artigo, equações **37a/37b**, apresenta aproximações lineares ao amortecimento equivalente das notas ao longo do registro estudado:

```text
b1(f0) = 4,4×10⁻³ f0 − 4×10⁻²     [s⁻¹]
b2(f0) = 1,0×10⁻⁶ f0 + 1×10⁻⁵     [m²/s]
f0 em Hz (fundamental idealizada)
perda modal no modelo 2003: sigma(beta) = -b1 - b2*beta²
```

Essas curvas são **ajustes empíricos do comportamento percebido nas vibrações medidas**, não leis universais da física do aço. Os autores destacam que variações locais refletem a razão de impedâncias cordas–tampo ao longo da ponte e que **as curvas NÃO são medidas diretas da impedância complexa no mesmo ponto**.

Para f0 nominal C4 ≈ 261,63 Hz, apenas como **avaliação matemática da reta ajustada**, e NÃO medição individual C4:

- b1(C4) ≈ **1,11 s⁻¹**;
- b2(C4) ≈ **2,72×10⁻⁴ m²/s**.

### 3.2 Tabela I do artigo — **híbrida, não geometria medida C6**

| Parâmetro PDE | C2 | C4 | C7 | Unidade |
|---|---:|---:|---:|---|
| L (comprimento vibrante de exemplo) | 1,23 | 0,63 | 0,10 | m |
| c (velocidade ideal da onda) | 160,9 | 329,6 | 418,6 | m/s |
| κ (rigidez de dispersão da PDE) | 0,58 | 1,25 | 1,24 | m²/s |
| b1 (perda) | 0,25 | 1,1 | 9,17 | 1/s |
| b2 (perda dispersiva) | 7,5e−5 | 2,7e−4 | 2,1e−3 | m²/s |

**PROVENIÊNCIA EXATA:** o artigo declara na seção V que os valores desta tabela são **tomados de Chaigne e Askenfelt**, EXCETO o parâmetro b2, derivado da calibração apresentada na seção VI. Logo **L(C4)=0,63 m NÃO é uma medição direta comprovada do Yamaha C6** e nem c, κ, b1 representam necessariamente a escala original dele. Esta tabela pode apoiar **BENCHMARK DE EQUAÇÕES**, não definir uma ficha “Yamaha C6 medido”.

As fórmulas de b1/b2 em §3.1 estão ancoradas nas curvas de perda equivalente medidas no C6, e são preferíveis para identificação do amortecimento do Yamaha de laboratório, **desde que se respeitem a estimativa e seu âmbito**.

## 4. Yamaha C7 grand — **impedância da ponte e modos de vibração realmente medidos** (Espanha, 2008)

**Artigo primário:** L. Ortiz-Berenguer, F. Casajus-Quirós, E. Blanco-Martín e D. Ibáñez-Cuenca, *Modeling of piano sounds using FEM simulation of soundboard vibration*, Acoustics'08 Paris, Universidad Politécnica de Madrid.

PDF: https://dael.euracoustics.org/confs/acoustics2008/data/articles/002811.pdf

**Piano Yamaha C7 de 2,27 m**, não necessariamente C7X. Ensaio **com piano montado e cordas instaladas**, impacto B&K 8202 na região da ponte grave correspondente à **24ª nota** (referência de contagem do artigo), vibrometria laser Polytec próxima ao golpe. Dois sinais sincronizados (força em N, velocidade em m/s), 44,1 kHz, 16 bit, para obter impedância complexa `Z(f)=F(f)/V(f)` em **N·s/m = kg/s**, incluindo fase.

**Região do ponto da ponte grave, faixa dependente da frequência:**
- componente real resistiva R aproximadamente **menor que 100 até ~4.000 N·s/m**, variando com frequência;
- componente imaginária reativa X aproximadamente **±1.000 N·s/m** na maioria da faixa mostrada.

Esses são valores de **um ponto e direção de excitação** e NÃO uma mola/amortecedor constante. O **sinal reativo muda** de acordo com a frequência.

**Dez frequências de picos modais reportadas na Tabela 3 na medição desta configuração:** **115, 165, 215, 265, 298, 338, 382, 445, 490 e 540 Hz**. São picos observáveis nesse experimento/ponto — **não uma lista universal dos dez primeiros autovalores do tampo de qualquer Yamaha**. Verifique os modos espaciais e a geometria antes de usá-los para modelagem C4.

**Limitação valiosa dos próprios autores:** a placa FE escolhida (1,75 × 1,46 m) tinha área diferente da região medida do Yamaha C7 (1,55 × 1,46 m na comparação publicada), e as curvas simuladas tinham diferenças modais importantes; isso evidencia por que **não se devem simplesmente copiar os autovalores FE como se fossem medidos no C7**.

## 5. Yamaha Disklavier DC7M4Pro — radiação real da nota C4 (EUA/NYU, 2013)

**Artigo primário:** Agnieszka Roginska, Justin D. Mathew, Jim Anderson & Alex U. Case, *High resolution radiation pattern measurements of a grand piano — The effect of attack velocity*, *Proceedings of Meetings on Acoustics* **19**, 035006, DOI **10.1121/1.4800047**.

Texto acessível: https://www.academia.edu/86956110/High_resolution_radiation_pattern_measurements_of_a_grand_piano_The_effect_of_attack_velocity

**Instrumento:** Yamaha C7 Disklavier DC7M4Pro, com **tampa removida**, sala do estúdio da NYU **não anecoica**. Nota **C4 (Dó central)** em três níveis MIDI: **15 (pp), 60 (mf), 127 (ff)**, sustentada 3 s; região inicial de 2 s analisada.

**Medição:** conjunto com **32 microfones**, espaçamento de **2 polegadas = 5,08 cm**; grade sobre o instrumento abrangendo cerca de 38 polegadas de largura e 88 de comprimento; **pontos a cada 2 e 8 polegadas**, respectivamente, com microfone cerca de **2 polegadas acima da borda do piano sem tampa**; **mais de 450 posições**, 44,1 kHz. O trabalho apresenta distribuições dos harmônicos dependentes da intensidade e da posição do ouvinte/microfone.

**Cuidado:** as três velocidades são valores **MIDI 15/60/127**, **não velocidades medidas do martelo em m/s**. Normalizações de nível efetuadas para comparar padrões relativos, então não usar os mapas para inferir diretamente SPL absoluto da dinâmica. Para a V4 a utilidade é **validar diretividade e o ataque em C4**, não substitui mapa de mobilidade da ponte nem dados completos da placa.

## 6. Yamaha Disklavier DC3 M4 — dado adicional de áudio binaural + vibração de teclado

**BiVib:** *Design and Application of the BiVib Audio-Tactile Piano Sample Library*, 2019, https://www.mdpi.com/2076-3417/9/5/914 e conjunto https://zenodo.org/records/2573232.

Piano **Yamaha Disklavier DC3 M4** de cauda em Pádua, Itália; vibração do **TECLADO** mais som nos dois ouvidos do ouvinte artificial, dez níveis de MIDI velocity por nota, múltiplas configurações de tampa, gravação 24 bit/96 kHz. O conjunto está identificado como licença **CC BY-NC-SA 4.0**. **Não mede força instantânea martelo–corda ou admitância complexa de ponte.** Jamais usar os WAV como sample playback no motor V4: apenas análise/escuta externa conforme licença.

## 7. Yamaha C3/C3X — escala de cordas ainda não comprovada

Encontrado registro de técnico na **Piano Technicians Guild**, março de 2026: https://my.ptg.org/discussion/yamaha-c3-stringing-scale-anomaly-question-1.

- O autor descreve a medição por micrômetro de fios de algumas notas de seu Yamaha C3, incluindo **0,038 polegadas** em determinado grupo de cordas (na medição descrita; pode ter passado por manutenção).
- Outro participante apresenta tabela de escala por notas, mas declara **explicitamente não estar 100% seguro de que a tabela pertence a um Yamaha C3**. Portanto é **FONTE DE CONFIRMAÇÃO PENDENTE**, NÃO escala original Yamaha e NÃO parametrização do C3X.
- A numeração de tecla, a geração, a distinção de diâmetro métrico/fiação AWG e a tensão calculada precisam ser verificadas no instrumento real.

**Faltam para C3X moderno:** comprimento vibrante por nota, diâmetro e massa linear C4, tensão por corda, massa efetiva de martelo C4, posição de golpe, três cordas e suas perdas/polarizações, modos de tampo e mapa da ponte.

## 8. Yamaha Corporation já executa modelagem física completa — referência de arquitetura

Yamaha R&D descreve **simulação de grande escala do piano inteiro** com martelos, abafadores, cordas, tampo, quadro de ferro, aro, nervuras **e ar**, calculando pressão acústica em pontos de observação. Fonte oficial: https://www.yamaha.com/en/tech-design/research/technologies/piano-simulation/

Isso corrobora nossa meta de arquitetura totalmente acoplada, mas **não publica** aqui os coeficientes proprietários e parâmetros medidos para copiar no V4. Não confundir existência de pesquisa da fabricante com licença para reproduzir seu código.

## 9. Quadro de aplicabilidade ao plano Stage Synth V4

| Grandeza requerida | C6 (2003) | C7 (2008) | DC7 (2013) | C3X (oficial) | Uso agora |
|---|---|---|---|---|---|
| Comprimento do móvel | histórico C6, 212 cm típico | C7 227 cm diretamente documentado | C7 histórico, ~227 cm | 186 cm, exato modelo atual | contexto, **não corda** |
| Velocidade do martelo | **2,2 m/s ±0,1** sob mf aprox. | não | MIDI 15/60/127; m/s não medido | não | condições de comparação |
| Frequências/B dos parciais | **estimados de acelerometria da ponte** | impedância causa alterações | radiância dos harmônicos por posição | não | parametrizar e validar C6 |
| Perdas equivalentes b1/b2 | **ajustes quantitativos publicados** | não | não | não | candidato para bancada C6, com limitações |
| Admitância Z(f), fase | **NÃO é medida diretamente em C6 no estudo** | **SIM, um ponto da ponte grave** | não | não | validar interface física C7 |
| Modos da placa | não completos nesse artigo | 10 picos reportados | padrões acústicos, não mapa de vibração de placa | não | referência modal C7 |
| P(mic) espacial | cabeça artificial, dados não integralmente publicados neste artigo | não | **>450 pontos C4** | não | validação de radiação DC7 |
| Geometria de feltro/haste | não parametrizada com dados de manufatura | não | não | não | necessita medição nova |
| 88 notas com geometria completa no mesmo piano | dados de harmônicos parciais para várias teclas, sem tabela de 88 comprimentos | não | um Dó central | não | **NÃO DISPONÍVEL em pacote público único** |

**Proposta técnica:** usar o **Yamaha Disklavier C6 como referência inicial do subsistema de cordas/contato de martelo**; manter os ensaios C7 e DC7 **como verificações independentes de conceitos** de ponte e radiação. NÃO fundir impedância do C7, parâmetros de corda híbridos da Tabela I e mapas de radiação do DC7 afirmando que descrevem um único Yamaha.

## 10. Próximos dados a procurar para reduzir os K01–K09

1. Dados originais (se disponíveis sob licença) da campanha Bensa em LMA/CCRMA: matrizes `B(note)`, `b1(note)`, `b2(note)` e séries sincronizadas de aceleração/velocidade de martelo. O artigo publica gráficos e curvas, **não garante dataset original disponível**.
2. Desenho de escala C6 específico do período, de um piano identificado por número de série: `L`, raio `r`, `T`, `mu`, ponto de impacto, número de cordas por nota.
3. Curva força/deformação de feltro C6 em velocidades físicas reais e estado de harmonização, com massa da haste e martelo por tecla.
4. Mobilidade vetorial `Y(f)` perto de C4 do **mesmo C6** (não reutilizar medida grave do C7 como se fosse C4/C6).
5. Vibração do tampo e radiação do mesmo piano/sala e note-on, separando etapas temporais.

**Resultado:** encontramos medidas de Yamaha grand que já tornam nosso trabalho menos hipotético, **mas ainda não há um atlas completo de geometria/ação/ponte/tampo do mesmo instrumento**. Estas são **FONTES para calibração e teste**, não autorização para gerar de novo um WAV como “piano Yamaha fiel”.
