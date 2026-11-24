# Stage Concert Grand — F2.2 evolução modal exata e primeiro acoplamento passivo (24/11/2026)

Base b2867ad26d69e3ddbbfcc7afeacaf570cadd0a33. Pesquisa isolada na rota autoral. F2 continua em andamento. Sem mudança de V10, DSP público, main, parâmetros C3X, áudio ou UI.

## Método e domínio
Auditoria: mechanical-reference.mjs blob 761a9d1247a4637ae40b277dc939486077f77ea1 e V10 shared_mechanics.py blob 185f1e7824e6f5c31ff3039c4984cef11eb3c046. V10 já utiliza evolução modal com força congelada; este trabalho acrescenta tratamento explícito dos três regimes de amortecimento, resposta numericamente estável em passos pequenos e acoplamento com balanço discreto demonstrável. Não é um simples port nem prova de correção da V10.

Oscilador linear SI m*x''+c*x'+k*x=F, k=m*(2*pi*f)^2. Solução analítica para força constante no passo, matriz de transição 2x2 pré-calculável e resposta afim. Regimes subcrítico, crítico e supercrítico: seno/cosseno, limite crítico por série, exponenciais reais com raiz lenta calculada sem cancelamento. Série da resposta ao degrau para passos pequenos; expm1 no regime supercrítico. Domínio de referência: m,f,dt positivos, c>=0, alpha*dt<=50, (omega*dt)^2<=100, entradas finitas; não é promessa de robustez para qualquer escala extrema. Não há suporte a massa livre f=0 nesta classe; referência F2.1 continua disponível. Sem aliasing garantido para forças variáveis, contato ou frequências acima de Nyquist. Exatidão refere-se somente ao sistema linear de coeficientes constantes com força constante por passo, dentro da precisão numérica.

Para dois modos, r=x_a-x_b. Força interna constante por passo f=-k_c*(r0+r1)/2-c_c*(r1-r0)/h. Como r1=r_free+(G_a+G_b)*f, obtém-se solução escalar implícita. Aplicar +f e -f aos modos. Trabalho interno f*(r1-r0)=-delta E_mola-c_c*(r1-r0)^2/h. Cada modo tem trabalho F*delta x e perda local integral c*v² dt. No código a perda local é computada por diferença de energia e trabalho; conferir independentemente por quadratura de velocidade, não tratar o balanço residual como prova independente por si só. O amortecedor de ligação usa velocidade média do passo, e não a integral exata do sistema acoplado contínuo. O método acoplado é aproximado; a evolução local é analítica.

## Resultados
14/14 verificações executadas em JavaScript V8 usando o código de referência recuperado do GitHub. A trajetória livre (0,1 s, 48kHz) foi comparada a solução analítica em cada passo: erro máximo relativo do estado 2,308e-13 (261,63 Hz), 1,711e-13 (1 kHz), 6,363e-13 (5 kHz), 1,276e-12 (10 kHz), 1,570e-12 (16 kHz). Energia de modo livre a 16 kHz durante 1 s passou tolerância relativa 1e-9. Não é teste de renderização acústica. A quadratura Simpson de 1024 intervalos confirmou a perda local para c=0,04, crítico e 2x crítico, erros relativos 4,54e-9, 7,12e-12 e 1,28e-11. A primeira tentativa de quadratura por ponto médio não passou a tolerância; foi substituída por Simpson para verificar a integral, sem afrouxar tolerância.

Par de modos hipotético: f=261,6255653 e 1100 Hz; m=0,002 e 0,004 kg; c=0,015 e 0,04 Ns/m; mola de ligação 2400 N/m, amortecedor 0,04 Ns/m; deslocamento inicial A=1e-4 m; duração 20 ms. Referência independente de ponto médio implícito a 1,536 MHz. Norma de erro (x, v/omega) relativa à amplitude inicial:

| Taxa | Erro relativo | Aumento máximo de energia (J) | Resíduo acumulado máximo (J) |
|---:|---:|---:|---:|
| 12000 | 0,02044879541 | 0 | 6,776e-20 |
| 24000 | 0,00511939594 | 0 | 2,541e-20 |
| 48000 | 0,00127733292 | 0 | 5,590e-20 |
| 96000 | 0,00031621390 | 0 | 8,132e-20 |

Convergência próxima de segunda ordem no cenário ensaiado. Perdas locais mínimas positivas nas quatro taxas. O teste com forças externas também respeitou balanço. Não extrapolar estabilidade, precisão ou custo para rede inteira, acoplamentos fortes, contato não linear, tampo ou 64 vozes. Nenhum benchmark de tempo real foi realizado.

## Reprodução e decisão
`node research/stage-concert-grand/exact-modal.test.mjs`
Commits 77afd13bcb02f94d903290a66b852d770c524ae9 e d32cafe4beb804da63fec73b1f28dc4bfc30dd92. Testes V8 antes da gravação; sem nova execução de Node/CI/hardware.

F2.2 entregue como laboratório. Próxima etapa F2.3: generalizar o acoplamento discreto de força constante para rede de vários modos e portas, com solução estruturada, comparação a referência densa refinada, testes de energia sob múltiplas forças e análise de condicionamento/custo. Só depois fechar F2 e iniciar F3. F1 permanece baseline de projeto, não homologação acústica. Sem samples, sem WAV até F8, F9/F12/F13 e meta 32–64 vozes preservadas.
