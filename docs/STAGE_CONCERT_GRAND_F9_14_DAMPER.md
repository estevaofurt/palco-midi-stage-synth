# F9.14 — abafador localizado passivo e pedal

Base 973f784cb6587c2e4d50d148927dc764a73d3724. F9.13 acústica concluída, transferência bidirecional verificada, mas sem ganho absoluto de cauda; preservar B. F9.10b concluiu ganho pareado. F9.14 isola somente controle de extinção da nota, não mecanismo de aumento de sustain quando cordas livres.

Abafador inicial puramente viscoso, força f=-c*deltaY/h resolvida implicitamente no porto vertical de contato existente com matriz G+h/c I, usando compliance da rede e deslocamento livre. Potência de contato não positiva, dissipação c*deltaY²/h contabilizada separadamente, verificação de trabalho. c máximo 1 N s/m por corda, hipótese, posição/área igual ao porto do martelo (0,13 L, 12 mm) provisória, não localização medida de abafador. Sem massa de feltro, contato unilateral, rigidez elástica, histerese, ruído, força do mecanismo ou amortecimento horizontal direto. Não simular golpe de abafador. Abafamento exclusivamente após martelo destacado, chave mantida desabilita contato, rampa prescrita 25 ms; pedal 0/0,5/1, relação linear experimental, não calibração de meio pedal. Soltura tecla 0,5 s, pedal 1,5 s. Corda secundária desconectada em todos os casos; pedal global e outras cordas serão tratados depois. Preservar B e F9.13. Checkpoint guarda agenda e perda acumulada, rejeita mudança. 3 s, mesmo ganho e exportador PCM16/24, sem EQ ou boost. Testes sintéticos, paridade ataque aberto, passividade, dissipação, bypass pedal, energia após soltura e checkpoint configurados. CI ainda pendente no commit. Não afirmar melhoria audível, integração pública, pedal real completo ou homologação. Main intacta.

## Resultados CI confirmados

CI [45423116521](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45423116521): 22/22 testes Node (9+6+7) e três renders de 3 s sem clipping. Paridade ataque aberto aprovada, dissipação contabilizada, pedal completo mantém perda de abafador zero no primeiro segundo; resíduo máximo 8.59035e-15 J.

| Pedal | Perda acumulada abafador em 1 s (mJ) | Em 3 s (mJ) | Pico acústico bloco 1–2 s (Pa) |
|---|---:|---:|---:|
| 0 | 0.982384 | 1.041096 | 0.079640 |
| 0.5 | 1.003072 | 1.041274 | 0.069765 |
| 1 | 0.000000 | 0.438756 | 0.257767 |

Meio pedal não mostrou resposta intermediária monotônica: no bloco 1–2 s pico menor que sem pedal, dissipação inicial maior. Passividade não garante naturalidade; hipótese viscosa e posição provisória não calibradas. Não homologar meio pedal. Investigar mobilidade de contato e dependência de força, posição, geometria, e comparar janelas RMS/partiais antes de alterar modelo. Artefatos [pedal 0](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45423116521/artifacts/14933904922), [pedal 0.5](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45423116521/artifacts/14936490188), [pedal 1](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45423116521/artifacts/14934227392). Sem pedal global, cordas secundárias desligadas. Feedback forte F9.10b 20,5 s não avalia F9.14. Main preservada.
