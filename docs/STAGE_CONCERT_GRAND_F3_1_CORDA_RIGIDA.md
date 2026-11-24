# Stage Concert Grand — F3.1 corda rígida física do Dó4

Data 24/11/2026. Base 136001aa011c4b6996d9c273efd2c4564bed7385. Pesquisa autoral offline. Nenhuma alteração em main, V10, C3X, DSP público ou UI. Nenhum WAV ou sample gerado/importado. F3 em andamento.

## Dependências verificadas
c4-design.mjs blob f17a9e7e5f5aa0c9f9394105164aefad3603b4b5; c4-wire-consistency.mjs blob 8ae5b2bb81a2374ad0cc9bc88030b1c2d20b935a; exact-modal.mjs blob 5421be767601a96fab1e430453dc5e9b9ea1e2f1; modal-port-network.mjs blob 33eb53b38f47a78d9b8ab50c3d90007f533dfb70. Reutilizados os parâmetros próprios e a evolução modal F2, não dados proprietários Yamaha.

## Equações e hipótese
Uma corda uniforme, circular, maciça, pequena amplitude, uma polarização transversal, tensão constante e apoios simples ideais: y=0 e y_xx=0 nos dois extremos. PDE sem perdas mu*y_tt=T*y_xx-EI*y_xxxx+f(x,t). Expansão y=sum(q_n*sin(k_n*x)), k_n=n*pi/L. Massa modal m_n=mu*L/2, rigidez K_n=L*(T*k_n²+EI*k_n⁴)/2, omega_n²=K_n/m_n. Energia=sum((m_n*v_n²+K_n*q_n²)/2). Frequência independe de amplitude no regime linear. Frequência natural sem amortecimento difere ligeiramente da frequência amortecida. Dispersão omega(k)=sqrt((T*k²+EI*k⁴)/mu), v_fase=omega/k, v_grupo=(T+2EI*k²)/(mu*v_fase). Perdas hipotéticas distribuídas sigma_n=sigma0+sigma2*k_n²; sigma0=0,4 s^-1, sigma2=0,0002 m²/s, c_n=2*m_n*sigma_n. Não são perdas medidas em Yamaha; não interpretar T60 modal como decaimento acústico. Não há calibração por parcial nem EQ.

Força total F aplicada uniformemente em largura w centrada em x0: peso b_n=sin(k_n*x0)*sinc(k_n*w/2), limite pontual w=0. Força modal b_n*F e deslocamento médio sum(b_n*q_n), conjugados energeticamente. Evolução F2.2 exata para força constante por passo, perdas calculadas por trabalho menos variação de energia; confirmar monotonicidade e comparação de trajetória com rede F2.3. O carregamento retangular é aproximação de contato espacial, não modelo de feltro. Força exercida pela corda no apoio direito ideal: -T*y_x(L)+EI*y_xxx(L). Este observável não é ainda condição de contorno móvel, mobilidade da ponte nem pressão sonora. Termo de perdas implementado em coordenadas modais; não se alega reação de uma terminação viscoelástica completa.

## Resultados
Baseline autoral C4 L=0,65 m, d=0,00096 m, T=657,083171860 N, mu=0,005682010137 kg/m, EI=0,008338440354 N m², B=0,000296440484. Massa modal 0,001846653295 kg. Corte estrito min(16000,0,4*fs), máximo de modos configurável. A 48 kHz: 47 modos, último 15815,804613 Hz; modo 48=16289,170469 Hz excluído. O corte reduz banda representada, não prova ausência de aliasing de forças variáveis e contatos futuros.

| n | frequência Hz | fase m/s | grupo m/s | fração flexão na rigidez |
|---:|---:|---:|---:|---:|
|1|261,625565|340,113235|340,214028|0,00029635|
|8|2112,452590|343,273546|349,664938|0,01861895|
|16|4341,296886|352,730372|377,610520|0,07053588|
|32|9557,195843|388,261081|478,674304|0,23286708|

T60 do envelope modal subcrítico (ln(1000)/sigma), n=1/8/16/32: 17,0700/9,8822/4,3281/1,3325 s. Hipótese para corda isolada, não timbre aprovado.

Convergência estática: flexibilidade em x0=0,13L; referência série 4096 modos (não valor exato infinito). Em 47 modos falta 0,559633% da flexibilidade pontual e 0,146972% da flexibilidade média de uma carga de largura 12 mm. 12 mm é hipótese de ensaio, não medida de feltro. Isso não garante convergência de força de apoio, impacto ou radiação, que podem ser mais sensíveis aos modos altos.
Conferência independente da dispersão espacial: autovalor da diferença central lambda=4sin²(n*pi/(2N))/dx²; omega_FD²=(T*lambda+EI*lambda²)/mu. Para n=12, N=32/64/128/256 intervalos, erro de frequência -5,896929/-1,497168/-0,375746/-0,094028%, aproximação de segunda ordem. É verificação analítica da discretização espacial, não execução de solver PDE em malha.

## Testes e decisão
19/19 verificações executadas em V8 antes da gravação: frequência fundamental, expressão B, massa modal, rigidez, limite flexível, velocidades de dispersão, corte, contorno, integral de área de contato, conjugação de potência, silêncio, conservação, dissipação, trabalho, comparação com F2.3, força de apoio, convergência estática e espacial, entradas inválidas.
Reprodução: `node research/stage-concert-grand/stiff-string.test.mjs`. Commits c07c0e9c18a879c5d963225fc11819010be7e313 e 99c3005c9cf0d02a8ae0d2a504b78c34c783c65f. Sem novo CI ou hardware.

F3.1 entregue; F3 continua em andamento. F3.2: avaliar trajetória temporal e identificação limitada das perdas usando referências acústicas C5, não igualar perdas da corda a envelope do microfone; testar sensibilidade de força de apoio e excitação temporal ao truncamento; acrescentar duas polarizações e tricórdio com parâmetros explícitos, sem fingir acoplamento simpático antes da ponte. Preservar F4–F9 sequenciais e F12/F13 bloqueados. Sem WAV de piano até F8. Meta 32–64 notas ainda não homologada.
