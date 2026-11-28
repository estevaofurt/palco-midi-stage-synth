# Concert Grand III — modos de 300 a 650 Hz no decaimento de Dó8 leve

O ensaio usa o estado físico de Dó8 MIDI 24 aos 60 ms, com 64 parciais por corda e taxa de 384 kHz. Propaga dois grupos de estados sem força externa. O primeiro reúne os demais modos do tampo na faixa nominal de 300 Hz inclusive a 650 Hz exclusive. O segundo reúne os demais estados da cavidade na mesma faixa nominal. A resposta conjunta soma esses dois sinais à resposta já auditada de 443,42 e 528,53 Hz. O sinal restante preserva os demais estados e a resposta decorrente do histórico anterior aos 60 ms.

A análise compara 60–100, 60–90 e 70–100 ms com janelas retangular e de Hann. Todos os cortes usam uma grade espectral de 25 Hz, com preenchimento por zeros nos intervalos menores. As frequências nominais pertencem ao tampo e à cavidade antes do acoplamento. Os bins de pressão decorrem da resposta acoplada nos observadores. A decomposição da diferença de energia entre feltros inclui a energia dos estados nominais, a energia do restante e a interferência entre ambos. As frações são assinadas.

Os resultados descrevem a simulação. A G3.02 permanece aberta para validação experimental. Consulte RETOMADA.md para reproduzir o ensaio.

A análise abrange 41 modos do tampo e 25 estados da cavidade, contando os dois estados do checkpoint anterior. A parcela modal isolada fornece 79,7–104,6% da diferença líquida de energia de pressão entre os feltros, considerando seis análises e dois observadores. Valores acima de 100% ocorrem quando a interferência e o restante compensam parte da diferença modal. Remover a cavidade em toda a faixa altera o contraste entre os feltros em até 0,021 dB. O contraste do restante após retirar todos os estados nominais varia de −0,58 a +2,58 dB conforme a janela. Em 60–100 ms com Hann, o contraste passa de +2,69/+2,27 dB para +2,08/+1,71 dB.

A próxima etapa investiga os modos do tampo com maior diferença de energia, começando pela região de 527–532 Hz e pelo modo de 446,40 Hz. A análise deve manter as duas janelas para verificar interferências. O erro máximo de balanço nas quatro novas propagações foi 5,45 × 10⁻¹³.

[Checkpoint com executores e instruções](https://chatgpt.com/library?file_id=libfile_16eedaf4ca4481918f8501894320e288&account_id=personal)
