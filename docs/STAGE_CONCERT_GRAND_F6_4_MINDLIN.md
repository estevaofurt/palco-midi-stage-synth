# Stage Concert Grand — F6.4 placa com cisalhamento e inércia rotatória

Data 24/11/2026. Base 46a60d2de1c3201344414932594eca82bd81685a. Preservada a linha autoral, F6.3 e toda versão pública. Novo modelo opcional de pesquisa, não troca automática da base. Sem áudio/PCM.

## Escopo e hipóteses
Referência metodológica: Chabassier, Chaigne, Joly, Modeling and simulation of a grand piano (2013), https://pubmed.ncbi.nlm.nih.gov/23862839/ ; Time domain simulation of a piano, Part 1 (2014), https://www.numdam.org/item/M2AN_2014__48_5_1241_0/. Modelos científicos de placa ortotrópica Reissner–Mindlin; nossa implementação é simplificada e não reproduz geometria, parâmetros ou metrologia dos autores.
Dependências verificadas: orthotropic-plate.mjs 044ca9601e884ec15ee0ec8a10912e20d23d8562, ribbed-plate.mjs 2d375941ac32a66962fbe9f28b1fa176641a116e, board-coupling.mjs c6776df1a4000a4462e326d71cbfce7f78275703, F6.3 db0bda9be1b305d0a81b5af14be61b2e6f3a3c5a. Mesmos 1,4 x 1,1 m, 8 mm, placa 5,2976 kg e oito nervuras 2,0812 kg da F6.2. Novas hipóteses não medidas: Gxz=0,65 GPa, Gyz=0,06 GPa, fator de cisalhamento 5/6; nervuras G=0,65 GPa. Não transferir propriedades ao Yamaha real.
Três campos por par (m,n): deslocamento normal W*sin(kx*x)*sin(ky*y); rotações Rx*cos(kx*x)*sin(ky*y) e Ry*sin(kx*x)*cos(ky*y). Convenção de rotações como inclinações da normal. Cisalhamentos proporcionais kx*W-Rx e ky*W-Ry. Energia de flexão com D11,D22,D12,D66 F6.1, inércia rotacional por área rho*h³/12. Integral comum A/4. Nervuras de linha centradas com flexão EI*ky²*Ry², cisalhamento Timoshenko kappa*G*A_r*(ky*W-Ry)² e inércia rotatória rho_r*I_r, além da massa translacional anterior; integram em y, acoplam índices m com mesmo n. Sem excentricidade, torção, espessura local real, coroa, pré-tensão, contornos irregulares. Subespaço Navier restrito a m,n>=1, não enumera famílias rotacionais puras com índice zero; não alegar espectro completo de placa espessa. Base original continua definida pelo corte da placa fina; três campos por par, corte ativo por frequência reforçada. Matrizes positivas por energias de flexão/cisalhamento/cinética; autoproblema generalizado em blocos, reutilizado Cholesky/Jacobi F6.2, limite de dimensão por bloco 192. Modos normalizados em massa; componentes de W mantêm interface de porta F6.3. Rotações não irradiar como deslocamento normal. Hipótese de perda modal estrutural F6.3 preservada.

## Resultados comparativos
Base original 4 kHz, 516 pares, 1548 autovetores no subespaço. Comparação ordenada (não correspondência por forma):
| ordem | Kirchhoff Hz | Mindlin Hz | diferença % |
|---:|---:|---:|---:|
|1|27,447327|27,346727|-0,36652|
|10|228,300509|222,731275|-2,43943|
|30|559,346939|546,225124|-2,34592|
|60|931,468922|877,937641|-5,74697|
|100|1286,725189|1191,675782|-7,38692|
|200|2123,275254|1904,457001|-10,30569|
|300|3144,887650|2722,547452|-13,42942|
Contagem ativa abaixo de 250/500/1000/1500/2000/4000 Hz: anterior 13/28/66/124/184/356, novo 13/29/75/140/211/380. Não indica convergência até 4 kHz.
| pares base | maior erro relativo primeiras 10 vs base 516 (%) | flexibilidade estática m/N |
|---:|---:|---:|
|59|0,900927|2,061296358e-5|
|123|0,899477|2,075457938e-5|
|253|0,829530|2,080893026e-5|
|516|referência finita|2,083915397e-5|
Resíduo máximo autoproblema 4,61166e-8, ortogonalidade de massa 2,10942e-14. Enriquecimento reduz frequências ordenadas e aumenta flexibilidade. Limite de cisalhamento muito rígido (escala 100) e pequena inércia rotatória (escala 0,01), placa sem nervuras: erro relativo máximo primeiras dez frequências 5,99595e-5 frente Kirchhoff. Teste de sensibilidade Gyz=0,03/0,06/0,12 GPa, base original 2 kHz: frequência ordenada 60=886,522/895,101/901,249 Hz; contagem abaixo 1 kHz=75/74/73. Hipóteses, não incerteza metrológica. Não se pode inferir qual é mais fiel ao piano real.

## Integração e regressão
BoardPort anterior recebe os novos modos diretamente; ligação, cordas, martelo e integrador de referência preservados. Impacto 1 m/s durante 12 ms, base original 4 kHz:
| modelo | corte ativo | taxa | modos | energia tampo mJ | deslocamento máximo na porta µm |
|---|---:|---:|---:|---:|---:|
|Kirchhoff F6.3|1000|96000|66|0,350409705|18,923513|
|Mindlin|1000|96000|75|0,331746666|18,925301|
|Mindlin|1500|96000|140|0,339735174|19,118166|
|Mindlin|2000|96000|211|0,344871521|19,051649|
|Mindlin|1500|192000|140|0,339939454|19,109080|
Pico a 96 kHz ~11,546167 N em todos. Resíduo energético máximo nos novos impactos 8,590e-15 J, aumento observado zero, resíduo de força <1e-8 N, rebote e soltura. Reproduz energia anterior F6.3 dentro de 1e-12 J. Diferença de energia de 1,5 para 2 kHz ~1,49% relativa a 2 kHz; não valida resposta modal/radiação em banda completa. Não extrapolar precisão de pico ou energia para fase. Erros de fase midpoint F5.3 seguem abertos.

## Testes e decisão
11 verificações de autoproblema, limites, convergência, sensibilidade e porta, e 2 verificações adicionais de regressão F6.3 e impactos integrados. 13/13 executadas em V8, integração usando fontes recuperados do GitHub. Reprodução: node research/stage-concert-grand/mindlin-plate.test.mjs. Commits 51ec425618acdae3bef157d477138353fd430632, b5f48edeebbdf4a02086226b62c35b2280470dc7 e 7f6c46b5e67215bcaade4dcea671590c8260e7b9. Sem nova execução Node/CI/hardware. F6.4 candidata para pesquisa offline; preservar referência Kirchhoff. Não afirmar validação de alta banda. Prosseguir na F7 com radiação espacial de referência, explicitamente limitada à banda estrutural ensaiada e comparando resoluções; antes da demonstração de banda completa, aprofundar convergência, propriedades de madeira, geometrias de ligação e precisão temporal. Não compensar lacunas com filtros por parcial. F8 primeiro WAV, F9 validação auditiva, F12/F13 e meta 32–64 notas não homologadas.
