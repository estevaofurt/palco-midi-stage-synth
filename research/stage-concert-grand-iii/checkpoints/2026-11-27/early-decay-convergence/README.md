# G3 — Convergência da cauda de 32 ms do Mi4
Continuação de 7fa6737. 35 entradas SHA256SUMS e 21 INPUTS do checkpoint anterior conferidas, seis referências adicionais (sobreposição). Dois novos impactos fortes Mi4 3 m/s, 32 ms, 64/192 (720 coordenadas) e 96/384 (1040 coordenadas), 24576 subpassos acústicos novos, abertura integral 369 portas, 127825 estados acústicos, histórico escalonado cabeça32. Referência arquivada 64/384. Parâmetros físicos inalterados. Captura 357/713, força nula depois. Máximos balanço 5,969749e-13, continuidade 1,795165e-15, compressão 1,301043e-18 m, trabalho relativo 5,292079e-16; mínimo trabalho exterior zero. Prefixos 12 ms: 64/192 idêntico; 96/384 vs regional fluxo3,223665e-14, velocidade1,920253e-14, força/compressão zero. Energia mecânica reconstruída idêntica nos três casos. Convolução direta5,255558e-17, pré-chegada1,035343e-15, prefixo FIR zero.
| Caso vs referência | Janela ms | Erro fino causal mic1/mic2 % | Filtrado causal mic1/mic2 % |
|---|---|---|---|
|64/192 vs 64/384|0–12|0,800393/1,220262|0,233946/0,161040|
|64/192 vs 64/384|12–32|1,167448/1,658537|0,691471/0,543363|
|64/192 vs 64/384|0–32|1,076678/1,590733|0,604177/0,503597|
|64/384 vs 96/384|0–12|0,085089/0,084290|0,077948/0,088184|
|64/384 vs 96/384|12–32|0,078639/0,079126|0,080310/0,078183|
|64/384 vs 96/384|0–32|0,080510/0,080052|0,079686/0,079811|
|64/192 vs 96/384|0–12|0,794151/1,219448|0,207356/0,150336|
|64/192 vs 96/384|12–32|1,154892/1,651856|0,670554/0,524515|
|64/192 vs 96/384|0–32|1,065607/1,584884|0,583975/0,485884|
30 comparações por receptor em cinco janelas (0–12,12–32,0–32,12–20,20–32 ms); 30/30 espectral 1 dB global/3 dB banda, 14/30 fino 1%. Pior banda0,226336 dB. 64/384 passa em todas as janelas perante96/384 (pior0,085590%); 192 reprova movimento livre (pior1,884966%). Parseval: fração quadrática acima96kHz temporal 88,6996/97,7131% ataque vs64,8580/88,2945% movimento livre. Não energia radiada. Kaiser617 taps, atraso0,802ms; DFT retangular, bandas significativas >=1e-4 norma quadrática 0–20 kHz. Convolução após 32 ms assume fluxo zero, não cauda física.
Energia mecânica final 64/192,64/384,96/384: 0,0158280524/0,0158284257/0,0158213848 J. Loop55,072463/79,182506 (arquivado)/102,238731 s, execução única, não benchmark. Primeira chamada da ferramenta teve argumento não suportado, corrigido antes de executar; auditoria preliminar substituída pela completa, script final exige três casos. Parâmetros de ensaio definidos nesta etapa. Sem aprovação 192 kHz, T60 de segundos ou convergência global. Próximo: janelas maiores e redução passiva da memória/impedância com controle integral. Sem render, EQ, normalização, alteração física ou promoção.
Pacote local G3_Convergencia_Cauda_32ms.zip, 42 entradas SHA256SUMS verificadas, ZIP íntegro e hashes internos conferidos. Reprodução no CHECKPOINT.md. Este commit publica relatório e hashes; scripts e binários no pacote local. Main preservada.
