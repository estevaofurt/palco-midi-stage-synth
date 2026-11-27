# Concert Grand III — checkpoint regional aprovado em 500 ms

A reexecução com SciPy 1.17.0 concluiu 576.000 passos físicos a 384 kHz, com 192.000 passos em cada caso (misto contínuo, uniforme contínuo e misto retomado). Foi usado o executor privado do checkpoint `19fb3673bfd1c2578931ec01a47cb528e81d6dff` e o ZIP físico original verificado pelo SHA-256 `1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192`.

| Critério | Resultado |
|---|---|
| Auditoria física | Aprovada nas dez janelas de 50 a 500 ms e na pressão completa. |
| Prefixo histórico | 10 de 10 hashes NPY idênticos à referência de 250 ms. |
| Retomada | Cinco sinais idênticos bit a bit ao caso contínuo, 18 indicadores físicos e os comandos iguais. |
| Aceitação geral | Aprovada. |

Aos 500 ms, os erros relativos de pressão causal entre o modelo misto e a referência uniforme foram 0,127874% e 0,113653%, abaixo do limite de 1%. O erro relativo máximo no balanço de energia foi 6,88 × 10⁻¹³. Após 200 ms, os abafadores permaneceram fechados, sem força de martelo nem nova injeção. A aceitação cobre o modelo regional de sete notas, 18 cordas, 369 portas e 127.825 estados acústicos, com cauda fechada.

As retomadas ocorreram nos passos 22.000, 96.000 e 153.600. Foram verificados os hashes dos estados salvos e dos prefixos, além dos nove conjuntos de saídas registrados pelo executor.

Ambiente da reexecução em Linux x86-64 com Python 3.12.14, NumPy 2.2.6, SciPy 1.17.0, Numba 0.61.2 e llvmlite 0.44.0. As configurações de threads foram `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1` e `NUMBA_NUM_THREADS=2`. A execução anterior com SciPy 1.15.3 permanece arquivada com seu próprio resultado de aceitação.
