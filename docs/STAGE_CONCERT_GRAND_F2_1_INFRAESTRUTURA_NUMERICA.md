# Stage Concert Grand — F2.1 infraestrutura numérica (24/11/2026)

Base 6d0a50aaabf70c3fbf47be4118cc0405481bf158. Rota autoral aprovada; nenhuma alteração da V10, C3X original, main, DSP, áudio ou UI. F2 em andamento, não homologada integralmente.

## Auditoria e método
Verificados os arquivos research/passive-string-bridge-cell.mjs (blob b03c3e308306c508045cc0bc4df56c7d1fc842e6), research/shared-passive-piano-bridge.mjs (blob 0062b72be55068750bc8ac755f92926364af8dc8) e V10 shared_mechanics.py (blob 185f1e7824e6f5c31ff3039c4984cef11eb3c046). Os primeiros usam ponto médio implícito com parâmetros normalizados, o segundo deles usa redução de Schur O(N). V10 usa evolução modal com forças congeladas por passo; não equivale a um integrador acoplado que garante exatamente o balanço discreto. Não substituir nem homologar V10 por esta auditoria.

Novo MechanicalReference em research/stage-concert-grand/mechanical-reference.mjs: referência densa offline, coordenadas translacionais SI, massas positivas diagonais, molas/viscosidade não negativas, conexões iguais e opostas. K e C são semidefinidas positivas por construção. Cholesky de A=M+hC/2+h²K/4, definida positiva com massa positiva. Resolver A*v_mid=M*v_n+h*(F_mid-K*x_n)/2, x_next=x_n+h*v_mid, v_next=2*v_mid-v_n. E=(v^T M v+x^T K x)/2; delta E=h*(F_mid^T v_mid-v_mid^T C v_mid). Força assumida constante no passo; não se provou balanço de sistemas não lineares, contato unilateral, coeficientes variáveis ou radiação. Os valores da comparação com solvers legados são normalizados, não medições SI reais. Implementação densa é referência de precisão, não caminho de tempo real.

## Resultados executados
16/16 verificações em ambiente JavaScript V8, incluindo soluções de massa livre, oscilador analítico, energia conservada por 48000 passos, dissipação monotônica e trabalho externo, troca de momento, amortecedor entre coordenadas, convergência, fase, dados inválidos e comparação com código legado obtido diretamente do GitHub.
- Solver compartilhado, 3 notas, 4800 passos: diferença máxima de posição 1,071e-18, velocidade 8,682e-16; energia 6,522e-18, trabalho 6,353e-22, perdas 1,701e-18 (unidades normalizadas). 
- Célula 4DOF, 2400 passos: posição 5,336e-20, velocidade 8,847e-17.
- Oscilador 261,6255653 Hz, duração 10 ms, erro de norma de estado (x,v/omega) relativo à amplitude inicial: 12kHz 0,02563329460; 24kHz 0,00642199855; 48kHz 0,00160634928; 96kHz 0,00040164034. Razão próxima de quatro em cada refinamento.

## Limitação decisiva: estabilidade não implica precisão
Para oscilador linear não amortecido, ponto médio implícito tem frequência numérica f_num=(fs*S/pi)*atan(pi*f/(fs*S)), S subpassos. A frequência calculada é inferior à física; energia pode estar perfeitamente conservada mesmo assim. Orçamento ilustrativo de erro de fase/frequência de 1 cent (não critério acústico aprovado pelo titular, nem medição Yamaha):
| f (Hz) | erro a 48 kHz (cents) | S mínimo | erro com S (cents) |
|---:|---:|---:|---:|
| 261,6255653 | -0,169183 | 1 | -0,169183 |
| 1000 | -2,467442 | 2 | -0,617718 |
| 5000 | -59,107598 | 8 | -0,964933 |
| 10000 | -210,604506 | 16 | -0,964933 |
| 16000 | -447,966393 | 26 | -0,935492 |

Subpassos corrigem a fase mas podem inviabilizar custo para 32–64 vozes. O cálculo vale para oscilador isolado não amortecido, não é benchmark de CPU ou qualidade do timbre. Não aplicar midpoint global de 48 kHz cegamente a parciais altos; investigar evolução modal exata (incluindo amortecimento e força constante), divisão de operadores/acoplamento passivo, precisão e convergência do contato. Exigir balanço de energia e comparação com referência refinada em vez de presumir que composição seja passiva ou precisa.

## Reprodução e decisão
`node research/stage-concert-grand/mechanical-reference.test.mjs`
Commits 4fd0286aa2a4f59c97a85e670774798134360e09 e 953c2bad78d44713387d4c7c80a29c0990248aae. Testes executados no ambiente V8 antes da gravação; não alegar novo CI Node ou hardware.
**F2.1 entregue, F2 ainda em andamento.** F2.2: evolução modal exata com trabalho/perdas verificáveis, incluindo limites de amortecimento crítico/supercrítico e força externa; medir erros de acoplamento e comparar com referência refinada. Somente depois avançar F3. Sem WAV até F8 conforme roteiro autoral. F9, F12, F13 e 0/7 gates de produto preservados. Meta 32–64 notas não homologada.
