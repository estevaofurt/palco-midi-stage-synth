# C3X F1.7 — matriz de evidências e sensibilidade da inarmonicidade (24/11/2026)

**F1 PENDENTE; F2–F13 não avançam.** Base F1.6: a59771b69a12565399709b16c43d758b12303cc0. Pesquisa independente, sem novo motor, sem mudança da V10, sem samples ou alteração da aplicação. Complementa, não substitui, F1_INVENTARIO_PARAMETROS_C3X.csv e F1_PARAMETROS_C4_PENDENTES.csv (16 lacunas). O titular não dispõe da amostra C3X C4 e autorizou continuar com C5 para análise comparativa.

## Verificação de fontes públicas
- Yamaha USA, consultada 24/11/2026: https://usa.yamaha.com/musical-instruments/pianos/products/grand-pianos/cx-series/ — informa alteração construtiva do apoio traseiro (~20% mais espesso nos C3X e maiores, em relação ao anterior), fabricação da curvatura do tampo derivada do CFX e alterações na união de tampo/nervuras/ponte. Feltro relacionado ao CFX com ajustes por modelo; curso de tecla nominal 10 mm. São características de projeto publicadas, NÃO espessuras absolutas, constantes elásticas, curva de contato ou medições do exemplar. Não converter 20% de espessura em 20% de rigidez.
- Rigaud, David, Daudet (2013), https://pubmed.ncbi.nlm.nih.gov/23654413/ — método de estimação de inarmonicidade/afinação por notas gravadas; referência metodológica, não medição C3X. Nenhum código/dado copiado.
- Busca dirigida por escala de cordas C3X, medições de ponte/tampo e Dó4 isolado: não localizamos nesta busca um conjunto de dados C3X suficiente, identificado, instrumentado e com direito comercial comprovado. Não é prova de inexistência de dados.
- C5: Alexander Holm, Salamander Grand Piano v3, CC BY 3.0; https://github.com/sfzinstruments/SalamanderGrandPiano, commit 3382bf9496bba2486f5ab0de55a264d1dfc38404. Usados apenas números arquivados no arquivo C5_C4_verified_numeric_report.json (blob 63e893d8cfff79c247c0ea76b944885669a8249f), cuja aquisição original foi verificada em https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313270498. Não houve nova aquisição de FLAC nem uso de amostras na síntese.

## Matriz de evidências: C4 MIDI 60

| Família | C3X real conhecido | V10 (software, sem aceite) | O que o C5 permite | Controle de incerteza proposto |
|---|---|---|---|---|
| Instrumento | Modelo nominal; exemplar não identificado | Perfil estimado | Outro modelo; não substitui C3X | Identidade, condição, afinação e licença |
| Geometria de cordas | Desconhecida | L=0,545 m; diâmetro=1,032895 mm; 3 cordas | Não identificar diretamente | Medidas independentes por corda, repetição |
| Tensão e massa linear | Desconhecidas | 702,63 N; 0,00864001 kg/m derivada da afinação alvo | Frequências restringem combinações de parâmetros, não cada valor | Propagação de incerteza de L, mu e f; evitar circularidade |
| Inarmonicidade B | Desconhecida | 0,000528449 configurado | Ajuste de picos acústicos e sensibilidade a janela e parcial | Resíduos, leave-one-out, cordas isoladas, repetição |
| Perdas e uníssonos | Desconhecidos | Aproximações | Envelope e batimentos aparentes da saída; não perdas individuais | SNR, janelas, resolução, repetição; separação de cordas |
| Martelo | Feltro/curso descritos qualitativamente ou nominalmente | Massa 0,010125 kg; expoente 2,6875 estimados | Ataque e espectro por camada, não força/velocidade física | Força, compressão, velocidade e histerese calibradas |
| Ponte | Construção qualitativa; mobilidade desconhecida | Acoplamento aproximado | Não separar Y=v/F da saída acústica | Força/velocidade simultâneas, fase e ganho calibrados |
| Tampo e nervuras | Método construtivo publicado; propriedades e modos desconhecidos | Modos sintéticos | Não separar formas modais e rigidez | Mapa espacial, espessura, orientação, perdas |
| Radiação | Pressão sincronizada e resposta espacial desconhecidas | IR modal sintética | Níveis relativos e trajetória de parciais, não Pa absoluto nem transferência | Calibração por frequência, posição, ruído, F1.6 |
| Pedais e amortecedores | Tipos documentados; resposta temporal desconhecida | Aproximações de ação | Três notas pressionadas não identificam pedais | Medir deslocamento/tempo, repetir |

Todos os campos C3X desconhecidos permanecem desconhecidos. A especificação do fabricante não prova valor no exemplar. Não há tolerância física aprovada nesta fase. Para planejamento instrumental apenas: erro de fase residual <=5 graus (F1.6) e erro de ganho diferencial <=1 dB por frequência como hipóteses iniciais de ensaio, não padrões Yamaha. Ausência de calibração significa não avaliado. Para amplitude, usar razão de ganhos calibrados, em dB, e somar limites absolutos distintos; para fase somar limites residuais independentes de origem sem contar o mesmo atraso duas vezes. Registrar faixa de frequência, validade, SNR/coerência, repetibilidade e intervalo de incerteza. Não confundir contraste espectral do C5 com incerteza calibrada.

## Ajuste independente de B
Modelo de corda rígida idealizado: f_n = n*f_ideal*sqrt(1+B*n²). Regressão linear não ponderada de (f_n/n)² contra n²; B=inclinação/intercepto; f1=f_ideal*sqrt(1+B). Não é reexecução da FFT nem método original de ajuste não linear. Picos arquivados: n=2..8, contraste >=20 dB e nível relativo >=-60 dB; excluímos fundamental de contraste insuficiente no ataque e selecionamos faixa fixa antes do cálculo. Exigir >=4 parciais distintos por ajuste; repetir removendo um parcial por vez. Janelas e camadas do mesmo conjunto de gravações não são replicações independentes nem intervalos de confiança.

| Camada | Ataque B × 1e6 | Corpo | Cauda |
|---|---:|---:|---:|
| v1 | 284,096 | 277,037 | 310,843 |
| v8 | 295,613 | 275,619 | 300,295 |
| v16 | 304,385 | 287,063 | 297,320 |

Nove ajustes: B 0,000275619–0,000310843. Removendo cada parcial separadamente: 0,000265097–0,000324388. Resíduo RMS em Hz: 0,256–0,557 (mínimo 0,256114; máximo 0,557077). V10 parâmetro 0,000528449 permanece acima de todos os ajustes; ~70–92% acima do intervalo principal. Isso é robustez à seleção de um parcial e à janela dentro do acervo C5, NÃO erro de C3X validado. Uníssonos, mistura espacial e picos não resolvidos podem deslocar a estimativa. O intervalo leave-one-out não é incerteza física nem validação com gravações independentes.

## Testes e governança

14/14 verificações executadas no ambiente JavaScript V8 antes de gravar os arquivos; recuperação de B conhecido, convenção f1, resíduo, invariância de ordem/escala, outlier, rejeição de entradas, nove janelas reais arquivadas, identidade e fronteira de evidência C3X. Não afirmar CI novo ou reexecução de áudio. Reproduzir em Node:
`node research/c3x-physical/c5-b-sensitivity.test.mjs`

Commits: 01eef2a4d690985c68f1ea67ee2475632cb43e9b e 031c1909468f96b4754de9ae3b241e8859858aa7.

**Decisão:** F1 não concluída. Não copiar B do C5 para C3X, não alterar IR nem motor V10, não avançar F2–F13, não publicar V11. Próximo estudo F1.8: quantificar sensibilidade teórica de frequências de parciais a B e distinguir dispersão de erro de afinação, preparando critérios de validação de corda; buscar evidência C3X independente. Meta 32–64 notas não alterada nem homologada.
