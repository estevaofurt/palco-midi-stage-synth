# Stage Concert Grand — F2.3 rede multimodal passiva (24/11/2026)

Base 69aa0bd08b5dc99c24b43ed68892e85fb713e0be. Rota autoral, sem alteração de main, V10, áudio, UI, efeitos ou motores publicados. Fontes locais verificadas: exact-modal.mjs blob 5421be767601a96fab1e430453dc5e9b9ea1e2f1; mechanical-reference.mjs blob 761a9d1247a4637ae40b277dc939486077f77ea1; c4-design.mjs blob f17a9e7e5f5aa0c9f9394105164aefad3603b4b5.

## Formulação
N modos lineares com coeficientes fixos em SI e P portas lineares com pesos adimensionais B_ip. Deslocamento de porta r=B^T*x, energia de mola 0,5*k*r², amortecimento viscoso c>=0. Força modal interna B*f, com f=-k*(r0+r1)/2-c*(r1-r0)/h por porta. Evolução modal exata sob força constante: x1=x_free+G*B*f (G diagonal não negativa). Definir D=diag(k/2+c/h)>0 para portas não nulas, S=sqrt(D), f=-S*z. Resolver (I+S*B^T*G*B*S)*z=S*r_free+S^-1*(K_port/2-C_port/h)*r0. Matriz simétrica definida positiva, lambda_min>=1 em aritmética exata. Cholesky pré-calculada; limite superior da condição espectral <= norma infinita da matriz, pois lambda_min>=1. Portas nulas omitidas. Pesos não precisam ser diferenças unitárias: permitem projeção modal conjugada de deslocamento e força. Não representa ainda uma ponte/tampo específicos.

Balanço discreto: energia total = modos + molas de porta; trabalho externo=sum(F_ext*delta x); perda local calculada por diferença trabalho-energia, e perda das portas=sum(c*delta r²/h). Não confundir resíduo de balanço construído dessa forma com prova independente: passividade testada por monotonicidade, perdas locais, soluções analíticas, comparação de trajetória com referência F2.1 e especialização F2.2. Perda das portas aproxima o sistema contínuo, não integral exata. Forças constantes por passo. Coeficientes fixos; contato unilateral, parâmetros variáveis e radiação permanecem fora do domínio.

Complexidade por passo O(N+nnz(B)+P²); montagem O(sum_i degree_i²+P³). O(P²) é a solução triangular densa no espaço das portas, não dos modos. Armazenamento O(N+nnz(B)+P²). Benefício condicionado a P pequeno e estrutura esparsa. Arrays de estado pré-alocados; não alegar ausência completa de alocações internas JS nem implementação AudioWorklet. Limites atuais N<=16384 e P<=128 são limites de entrada, não capacidade de tempo real.

## Ensaios
13/13 verificações executadas no ambiente JavaScript V8 antes de gravação. Incluem especialização par, zero, portas vazias, convergência, passividade, múltiplas forças, porta ponderada com modo normal analítico, orientação, portas duplicadas, energia sem perdas, rede grande, rejeições.

Cenário hipotético 4 modos 261,6255653/540/1100/2200 Hz, massas 0,002/0,0025/0,003/0,0035 kg, amortecimentos 0,015/0,018/0,021/0,024 Ns/m, 3 ligações 2400/1200/1600 N/m e 0,04/0,02/0,03 Ns/m. Duração 10 ms. Referência F2.1 a 1,536 MHz. Erro de norma de estado normalizado pelo deslocamento inicial 1e-4 m:

| Taxa | Erro relativo | Aumento max E (J) | Resíduo max (J) | Limite superior condição |
|---:|---:|---:|---:|---:|
| 12000 | 0,01256891892 | 0 | 1,440e-20 | 1,007711 |
| 24000 | 0,00314157076 | 0 | 1,440e-20 | 1,002517 |
| 48000 | 0,00078341538 | 0 | 1,779e-20 | 1,000914 |
| 96000 | 0,00019380105 | 0 | 1,779e-20 | 1,000370 |

Convergência próxima de segunda ordem, sem aumento energético observado. Teste adicional de múltiplas forças (4800 passos), perdas positivas dentro da tolerância e balanço; rede sem perdas passou erro relativo de energia <1e-9.

Stress: 128/512/2048 modos, 4 portas, 2048 passos, 48 kHz, frequências 260 a 10600 Hz, pesos normalizados e acoplamento ilustrativo fraco. Resíduos 3,205e-20/3,508e-20/6,498e-19 J, sem crescimento de energia. Limites de condição ~1,000118. Cronometragem bruta V8 incluindo duas avaliações de energia por passo: 503/1909/7963 ms, respectivamente, para apenas 42,667 ms de tempo simulado. Aproximadamente linear em N neste ensaio, mas MUITO aquém do tempo real; não é benchmark isolado do step(), Node, browser ou hardware alvo. Não extrapolar esses números a 64 vozes. Acoplamentos fortes, redes de muitos portos, contato, aliasing e desempenho ainda exigem ensaios nas respectivas fases.

## Reprodução e decisão
`node research/stage-concert-grand/modal-port-network.test.mjs`
Commits 0bc39089ddac26c58737636f578a5841b080c0c8 e ebf9af76ea7404368aa6cb1ca9aad2e5f9ca4773. Sem CI Node novo ou hardware. F2.1–F2.3: 43 verificações de pesquisa aprovadas (16+14+13), infraestrutura linear offline suficientemente estabelecida para iniciar F3 no escopo autoral; aceite técnico interno restrito a este domínio, não aprovação física/acústica final. Manter referência densa para regressão e revisitar integradores ao introduzir física não linear. F3 próxima: construir corda rígida C4 a partir de L,d,rho,E,T do baseline, massa modal e funções de forma, dispersão, força conjugada, perdas passivas, truncamento espectral e convergência. Não ajustar cada parcial arbitrariamente. Sem WAV de piano até F8. V10 intacta, 0/7 gates do produto, F9/F12/F13 e meta 32–64 notas preservados.
