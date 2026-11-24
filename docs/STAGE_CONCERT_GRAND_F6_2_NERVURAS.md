# Stage Concert Grand — F6.2 nervuras de referência e modos generalizados

Data 24/11/2026. Base 6055dd6f6bc4d9af578df0ef82d6a4b034834c. Pesquisa offline. Nenhuma alteração em main, V10, DSP público, áudio ou UI. Nenhum WAV. F6 continua em andamento.

## Formulação e hipóteses
Fonte verificada orthotropic-plate.mjs 044ca9601e884ec15ee0ec8a10912e20d23d8562 e relatório F6.1 7f540b39d761bc67a7756b11f21399d0cca877db. Preservar parâmetros da placa retangular simplesmente apoiada de 1,4 x 1,1 m, espessura 8 mm, massa 5,2976 kg. Oito nervuras retas de vão completo na direção y (transversal às fibras do tampo), centros x=0,14/0,31/0,48/0,65/0,82/0,99/1,16/1,29 m. Largura 22 mm, altura 25 mm, rho=430 kg/m³, E longitudinal=11 GPa. Hipóteses autorais, não medidas Yamaha. Massa linear 0,2365 kg/m, EI=315,104167 N m² por nervura, massa individual 0,26015 kg, total 2,0812 kg; massa placa + nervuras=7,3788 kg. Aproximação de vigas Euler-Bernoulli em linha central, aderidas ao deslocamento transversal da placa; não inclui largura finita na integral de acoplamento, excentricidade, eixo neutro composto, torção, cisalhamento, inércia rotatória, coroa, pré-tensão ou bordas reais. A altura/largura apenas entra nas propriedades da seção. Não é modelo completo de nervura colada abaixo do tampo.
Base de Ritz de senos F6.1. Em cada bloco de índice n fixo, vetor b_m=sin(kx_m*x_r). Acrescentar M_r=mu_r*Ly/2*b*b^T e K_r=EI_r*Ly/2*ky^4*b*b^T. Para nervuras de vão inteiro e paralelas a y, ortogonalidade em y torna independentes os blocos n. Matrizes de massa e rigidez são positivas por construção; termos adicionais semidefinidos positivos. Resolver K*u=lambda*M*u com Cholesky M=L L^T, matriz simétrica L^-1 K L^-T e rotações de Jacobi; recuperar u=L^-T*v. Normalização u^T M u=1 (coordenadas mass-normalized, não deslocamento em metros; projeção modal tem unidade kg^-1/2). Forma espacial soma de senos ponderados pelo autovetor. Porta conjugada transformada pela mesma combinação de pesos espaciais da F6.1. Mobilidade de teste usa massa modal unitária e sigma=2+0,0005*omega, hipótese de perda modal estrutural, não integração temporal acoplada ou radiação. A enumeração usa frequências da placa SEM reforços; basisHz é corte da base original, não garantia de resolução até essa frequência do tampo reforçado. Modos ordenados não implicam identidade entre formas antes/depois de reforçar.

## Resultados
Base de 123 modos (corte original 1 kHz):
| ordem | placa Hz | apenas massa Hz | apenas rigidez Hz | completo Hz |
|---:|---:|---:|---:|---:|
|1|12.034311|10.141913|32.568585|27.448801|
|2|22.730253|19.155851|50.246410|42.203596|
|3|39.840742|33.461226|92.115800|77.027674|
|4|42.540404|35.850461|123.040037|103.748573|
|5|48.137243|40.428887|131.365515|110.444777|
|6|64.861379|54.473794|155.645025|129.658055|
|7|70.949434|59.790786|155.766355|130.324878|
|8|86.715978|72.510722|203.144321|169.178080|
|9|90.921013|76.356910|239.050323|198.766701|
|10|94.055053|78.646776|274.711840|228.329104|
A massa isolada não eleva frequências ordenadas; rigidez isolada não reduz, em todos os modos da base de ensaio. Com ambas, não impor monotonicidade relativa à placa. Nenhum ajuste por parcial. Não afirmar que a frequência fundamental calculada coincide com instrumento real.
Convergência Ritz com bases aninhadas, referência finita de 516 modos:
| corte da base original Hz | N | primeira Hz | maior erro relativo primeiras 10 (%) | resíduo relativo max |
|---:|---:|---:|---:|---:|
|250|27|27.448841109|0.125960912|1.514669e-13|
|500|59|27.448806107|0.110423310|4.984300e-13|
|1000|123|27.448801250|0.107422857|1.495071e-12|
|2000|253|27.448715925|0.100327863|1.140999e-11|
|4000|516|27.447327163|0.000000000|6.555758e-11|
Ortogonalidade de massa erro absoluto max 7.771561e-15. Valores de Ritz não crescentes ao enriquecer a base para os índices comuns, conforme princípio minimax. Não são erros contra solução contínua ou piano real. Flexibilidade estática média da porta x=0,83 y=0,46 dx=0,04 dy=0,025 m:
- 250 Hz: 2.008152784e-5 m/N; diferença relativa à referência 4 kHz 2.462897%.
- 500 Hz: 2.041302987e-5 m/N; diferença relativa à referência 4 kHz 0.852773%.
- 1000 Hz: 2.053485538e-5 m/N; diferença relativa à referência 4 kHz 0.261060%.
- 2000 Hz: 2.057651343e-5 m/N; diferença relativa à referência 4 kHz 0.058725%.
- 4000 Hz: 2.058860401e-5 m/N; diferença relativa à referência 4 kHz 0.000000%.
Mobilidade contínua recíproca com parte real PSD em 5 frequências (30/100/261,63/500/1000 Hz), para duas portas. Erro recíproco zero observado. Não é comparação com mobilidade medida. O sinal de forma modal é arbitrário, usar mesma orientação na excitação e observação.
Limite de placa fina: indicador geométrico k*h=h*sqrt(kx²+ky²) na base da placa original, não autovetor reforçado. O valor 0,2 é marcador ilustrativo de auditoria, não limite universal de erro.
| corte original Hz | modos | kh máximo | modos kh>0,2 |
|---:|---:|---:|---:|
|250|27|0.163916|0|
|1000|123|0.346925|57|
|4000|516|0.710331|449|
|16000|2116|1.420662|2049|
A 16 kHz, kh máximo 1,42: não há base para assumir teoria de placa fina válida na banda completa. Também há limites da aproximação de viga delgada e da geometria de linha. F6.3 pode iniciar acoplamento de referência de baixa banda, mas precisa documentar faixa utilizável e F6 não deve ser considerada validada em banda completa. Comparar modelo de cisalhamento/inércia (Mindlin/Timoshenko) ou método de elementos finitos e geometria mais realista antes de homologação sonora; não extrapolar convergência matemática para precisão física. Tampo será compartilhado; não duplicar por tecla.

## Testes e decisão
12/12 verificações em V8, repetidas com fontes recuperados do GitHub: limite sem nervuras, massa, rigidez, resíduo do autoproblema, ortogonalidade, enriquecimento, flexibilidade, reciprocidade, normalização de porta, entradas inválidas e indicador kh. Reprodução: `node research/stage-concert-grand/ribbed-plate.test.mjs`. Commits 3d0cb4ac31aa289e4c74fe2088cfa501e3e15667 e cb5f119acb27f9913ab1983a4bbd41f4fe701ed3. Sem nova execução Node/CI ou hardware.
F6.2 entregue no escopo simplificado de nervuras em linha. F6.3: acoplar ponte F5 à superfície mass-normalized com força e deslocamento conjugados, considerar substituição (não duplicação) de rigidez/amortecimento provisórios, verificar passividade, mobilidade, trabalho e limite rígido. Manter referência offline refinável; decidir modelo de banda superior em etapa explícita, sem alegar fidelidade física não demonstrada. F7 radiação, F8 WAV completo, F9 comparação e aprovação, F12/F13 e meta 32–64 notas não homologadas. 
