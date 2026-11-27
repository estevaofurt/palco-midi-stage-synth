# G3 — Particionamento espectral e atualização modal compilada

Continuação de G3_Referencia_Fina_369. 18 entradas do manifesto anterior verificadas; cada execução confere 20 arquivos de G3_Acoplamento_369 e cinco insumos físicos. 369 portas, 127.825 estados, d3 a 48 kHz, oito subpassos a 384 kHz; fluxo superior prescrito e 867 incógnitas inferiores. Sem alteração física.

9/9 ensaios em circuito fechado: 320/128/128 intervalos de ruído/pulso/alta por configuração; 1.728 intervalos, 13.824 subpassos. Erros máximos frente a sinais arquivados 1,22e-15; energia 1,62e-16; trabalho 1,22e-15; continuidade projetada 4,76e-15; trabalho acumulado mínimo normalizado zero. Sete testes sintéticos pequenos do particionamento (1,2,3,7,8,9,17 lags) verificam volta completa dos dois anéis, reset e preview; erro máximo 3,35601e-16. Teste físico de 320 blocos não cobre volta dos anéis de 512/1024 do particionado.

| Caso | Compacta ms | Particionada ms | Modal compilada + compacta ms |
|---|---:|---:|---:|
|Ruído|23,7328|19,6029|14,2160|
|Pulso|19,2359|20,7658|9,5641|
|Alta|18,9123|21,2899|9,3401|

Ruído após preencher 301 lags: 31,7466/21,5685/19,5115 ms (19 blocos). P99 36,4638/85,7304/22,6727 ms. Exterior: memória persistente contabilizada compacta 134.366.400 bytes, particionada 822.000.960 bytes; sem campos, temporários ou estados; fused adiciona coeficientes modais não incluídos. Execuções únicas, mesma entrada e uma thread, sequenciais, sem controle de carga do SO. Tempos instrumentados excluem verificações, preparação e compilação; aquecimento modal explícito apenas em fused nos logs originais, sem compilação modal nas demais. Não é benchmark de dispositivo, ainda muito acima de 20,833 us.

Decisão: FusedGrouped + CompactStream candidato de pesquisa; preservar todos os polos/resíduos; particionamento exato como alternativa não prioritária devido a memória e picos. Próxima etapa redução passiva modal, validação reservada e recuperação de observadores. Sem render, sem alteração da main, geometria piloto e 12 dependências de regeneração pendentes.

Reprodução no pacote local G3_Espectro_Particionado_369.zip, com todos os módulos irmãos, verify.py, test_partition.py, JSON, logs e manifestos. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Numba 0.65.1. Conferir SHA256SUMS e insumos, executar em uma thread:
```
python verify.py /raiz/restaurada /pasta/G3_Acoplamento_369 --mode compact
python verify.py /raiz/restaurada /pasta/G3_Acoplamento_369 --mode partitioned
python verify.py /raiz/restaurada /pasta/G3_Acoplamento_369 --mode fused
python test_partition.py
```
Este commit publica módulos novos e resumo, não o runner completo nem os binários.
