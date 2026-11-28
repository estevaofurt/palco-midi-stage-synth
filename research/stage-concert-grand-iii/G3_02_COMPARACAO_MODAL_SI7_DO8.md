# Concert Grand III — transferência da análise modal entre notas e intensidades

Quatro replays de 100 ms recuperam os estados aos 60 ms para Si7 MIDI 24 e Dó8 MIDI 76 com os feltros original e graduado. A comparação usa a pressão arquivada, 64 parciais por corda, integração a 384 kHz e dois observadores. Em Si7 a montagem regional inclui MIDI 107 também nas propagações modais.

Três grupos de frequências nominais do tampo, 300–400, 400–500 e 500–650 Hz, evoluem separadamente sem força externa a partir dos deslocamentos e velocidades dos replays. Os limites inferiores são inclusivos e os superiores exclusivos. Em Dó8 leve, a referência incorpora aos respectivos grupos as respostas dos três modos antes reportados individualmente, para usar a mesma partição nos três casos. A análise usa Hann e retangular em 60–100, 60–90 e 70–100 ms, na grade de 25 Hz. A diferença assinada em energia de pressão divide igualmente cada termo de interferência. A retirada simulada do grupo mede a mudança no contraste entre os feltros.

A G3.02 permanece aberta para validação experimental. Consulte RETOMADA.md para reproduzir.

No segundo observador, 400–500 Hz liderou em 17 das 18 análises. A exceção foi Dó8 médio em Hann de 70–100 ms, com 30,6% em 300–400 Hz e 30,4% em 400–500 Hz. No primeiro observador, a liderança alternou entre 400–500 e 500–650 Hz conforme a janela. Na janela de Hann de 60–100 ms, 500–650 Hz liderou no primeiro observador em todos os três casos.

| Caso | Parcela de 400–500 Hz no segundo observador, seis análises | Parcela em 60–100 ms com Hann | Contraste total em Hann, observadores 1 e 2 |
|---|---:|---:|---:|
| Si7 leve | 37,6–68,0% | 53,9% | +2,56 / +2,29 dB |
| Dó8 leve | 37,5–83,2% | 59,0% | +2,69 / +2,27 dB |
| Dó8 médio | 30,4–71,5% | 48,9% | +0,69 / +0,58 dB |

No segundo observador, retirar o grupo de 400–500 Hz na janela de Hann de 60–100 ms mudou o contraste de +2,29 para +2,37 dB em Si7 leve e de +0,58 para +0,62 dB em Dó8 médio. A parcela assinada é uma diferença de energia que inclui a interferência repartida. A retirada altera simultaneamente os denominadores e os termos de interferência da razão em dB.

Os quatro replays reproduziram a pressão de referência amostra por amostra. O erro relativo máximo de balanço das 12 propagações foi 1,45 × 10⁻¹². O próximo ensaio deve completar a matriz com Si7 médio e avaliar a estabilidade do contraste antes de ajustes no feltro.

[Checkpoint com dados e executores](https://chatgpt.com/library?file_id=libfile_6acbc1ce6b108191ad503b8b217e0a25&account_id=personal)
