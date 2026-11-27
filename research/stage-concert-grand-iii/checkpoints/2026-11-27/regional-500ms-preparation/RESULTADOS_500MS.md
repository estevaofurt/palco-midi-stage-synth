# Concert Grand III — ensaio regional de 500 ms

Em 27 de novembro de 2026, o executor `private_run_500ms.py` do checkpoint `19fb3673bfd1c2578931ec01a47cb528e81d6dff` concluiu os **576.000 passos** previstos. Foram 192.000 passos em cada caso: misto contínuo, uniforme contínuo e misto com retomadas. A configuração original usa 384 kHz, sete notas, 18 cordas, 369 portas e 127.825 estados acústicos. O ZIP de entrada foi verificado pelo SHA-256 `1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192` e pelo manifesto de 182 entradas.

| Critério do executor | Resultado | Evidência |
|---|---|---|
| Auditoria física | Aprovada | Dez janelas causais de 50 a 500 ms, comparação espectral, conservação, dissipação, causalidade e pressão completa passaram. |
| Prefixo histórico de 250 ms | Reprovado | 0 de 10 hashes NPY coincidiram. |
| Retomada em 500 ms | Aprovada | Cinco sinais idênticos bit a bit ao caso misto contínuo e 18 indicadores físicos mais comandos iguais. |
| Aceitação geral | Reprovada | O protocolo exige os três critérios. O último checkpoint integralmente aprovado permanece em 250 ms. |

Aos 500 ms, os erros relativos de pressão causal entre o caso misto e o uniforme foram **0,127874%** e **0,113653%** nos dois microfones, ante o limite de 1%. Para a pressão completa, foram 0,127874% e 0,113653%, com arredondamento a seis casas decimais em porcentagem. O maior erro relativo de balanço de energia foi (6,99 × 10⁻¹³). Após 200 ms, todos os abafadores estavam fechados, a força dos martelos era zero e a injeção de energia permanecia constante. A pressão calculada após a janela assume fluxo zero.

Os estados nos passos 22.000, 96.000 e 153.600 foram salvos e verificados pelo SHA-256. Os cinco prefixos de cada snapshot coincidiram com os sinais contínuos e retomados. No primeiro estado, o martelo de MIDI 48 estava ativo. Nos outros dois, os martelos estavam inativos e todos os abafadores fechados.

A regressão original de 18 ms do pacote também divergiu nos cinco hashes de dados brutos neste ambiente, sem depender da reconstrução de cabeçalhos NPY usada no teste de 250 ms. Na comparação direta com as pressões arquivadas de 250 ms, o maior erro relativo L2 no trecho causal foi (2,55 × 10⁻¹³). Esses dois diagnósticos mantêm em aberto a origem da divergência de hashes e o resultado do critério de equivalência bit a bit. O ambiente executado usou Python 3.12.14, NumPy 2.2.6, SciPy 1.15.3 e Numba 0.61.2.

A evidência cobre o modelo regional com cauda fechada e a referência uniforme de 128 modos por nota. Os parâmetros físicos e os critérios de precisão foram preservados durante toda a execução.
