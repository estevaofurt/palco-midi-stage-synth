# F9.13 — ressonância simpática com martelo e pressão acústica

Base ad216a908c7a1e13b1dabf9a8a3ecee5ee1b73e7. F9.12: 7 testes e 3 ensaios mecânicos aprovados; +50 cents recebeu mais energia que frequência livre nominal, hipótese de modos acoplados, não recomendação de desafinação. Feedback: forte F9.10 audível menos de 14 s; F9.10b corrigindo ganho de comparação ainda em execução. Preservar B.

Acoplar martelo original à rede multiponto por complemento de Schur da mesma matriz simétrica de elos, incluindo forças de contato na previsão livre. Solução simultânea; apenas tricórdio C4 percutido, corda secundária inicialmente em repouso. Contabilizar trabalho positivo e negativo na porta vertical secundária, perdas e energia total incluindo martelo. Checkpoint guarda ambas as pontes, tampo, perdas, martelo, configuração de conexão. Otimizar somente solve do tampo multiponto com respostas lineares pré-computadas. Usar mesma malha/radiação/337 modos de tampo <3 kHz, cordas <16 kHz, mecânica 96 kHz e estéreo 48 kHz de B, mesma posição dos ouvintes e ganho 0,36767023440034063. Sem loop, EQ adicional, ganho variável ou alteração dos coeficientes de B. Três casos: secundária desligada, ligada nominal, ligada +50 cents (somente sensibilidade). Corda hipotética de 1,3 m com P2 nominal 261,6256 Hz e segunda porta (.96,.46) m; não escala real Yamaha. Sem abafadores, pedal ou 88 notas.

Critérios prévios: paridade pressão relativa L2 <1e-7 e energia com F9.8 B em 25 ms quando desligada; passividade, checkpoint, trabalho secundário e estado em repouso desligado. 20 s contínuos, PCM16/24 e float, ganho comum, comparar primeiros 500 ms, níveis absolutos 10–19 s (especialmente 14 s) e P1–P10/contrastes. Excluir fade, não inferir audibilidade. B só poderá ser superado após escuta e ganho consistente sem deteriorar ataque. A corda secundária pode reduzir a sustentação; não presumir benefício. Testes e renderizações configurados, pendentes na criação. Renderizador novo isolado, dívida técnica de duplicação a resolver depois de paridade. Main e versões estáveis intactas; polifonia 32–64 ainda não demonstrada.

## Resultados confirmados

CI [45420741878](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45420741878), 23 testes Node (7+7+9), três renders 20 s concluídos sem clipping. Paridade desligado L2 2.50844e-14. Ganhos absolutos em ganho fixo (dB):

| Caso | Inicial | 14 s | 19 s | Trabalho entrada/saída porta secundária (J) |
|---|---:|---:|---:|---|
| off | 0.000 | 0.000 | 0.000 | 0.00000e+0/0.00000e+0 |
| nominal | -0.082 | -0.394 | -0.852 | 3.55242e-4/3.37419e-4 |
| offset50 | -0.354 | -0.104 | -0.115 | 4.88298e-4/4.58780e-4 |

Transferência bidirecional confirmada; não promove nominal nem +50 cents, não há ganho absoluto tardio. Preservar infraestrutura e B. Artefatos [off](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45420741878/artifacts/14934635835), [nominal](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45420741878/artifacts/14933478660), [offset50](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45420741878/artifacts/14934466033). F9.14 testa abafadores isolados, sem alegar aumento de sustain livre. Main intacta.
