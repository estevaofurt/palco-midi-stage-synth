# G3 — d7 e seleção orientada pelos receptores
Continuação de G3_Enriquecimento_Otimizado. 103 entradas verificadas por execução. 369 portas, 127.825 estados, tampo d3 fixo, 48/384 kHz. Seleção fixa de 144 direções: contribuição quadrática individual aos receptores, normalizada por receptor, do sétimo coeficiente da diferença de fluxo d8-d6 em ruído arquivado de 64 blocos. Fração 99,6282% dos escores. Não é sensibilidade adjunta exata; ignora interferências e mudanças no acoplamento. 1734/1878/2023 incógnitas inferiores d6/mista/d7, todos executam em grade d7. Sem ganho de custo comprovado.

| Caso/modelo | Pressão fina % | Projetada % | Pior receptor fino % | Pior receptor projetado % |
|---|---:|---:|---:|---:|
| Arquivado d6 |0,957980|0,087733|1,127271|0,108227|
| Arquivado mista |0,580009|0,033456|0,699279|0,038419|
| Arquivado d7 |0,578150|0,032754|0,697157|0,037504|
| Novo d6 |0,980349|0,084346|1,019527|0,088962|
| Novo mista |0,583705|0,032492|0,601061|0,035393|
| Novo d7 |0,582627|0,030557|0,602375|0,033474|

Transientes seed 271132 (128 blocos, referência arquivada) e 271133 (160 blocos, d8 recalculado). Nenhum usado na seleção. Primeira metade de ruído envelopado, segunda metade fluxo superior zero com abertura evoluindo implicitamente. 6 soluções projetadas, 864 blocos, 6912 subpassos, uma nova referência d8 (1280 subpassos). Energia <=1,826e-16, trabalho <=1,045e-15, continuidade ativa <=1,277e-15; nenhum trabalho acumulado negativo observado. Referência nova: resíduo fino 1,235e-14, trabalho fino por prefixo 1,567e-15.

Replay fino independente da solução projetada usando passo modal único e FFT espacial-temporal em lote: resíduo relativo de continuidade inferior d6 27,733134%, mista 19,774386%, d7 18,009696%, d8 1,418978e-14 (relativo). Carga reproduzida com erro <=1,083e-15. Mista e d7 passam critério exploratório de pressão fina individual 1% nestes dois casos, d6 falha. Não implica aprovação da continuidade interna nem inaudibilidade. Normas L2. Janelas 2,667/3,333 ms; pressão calculada com fluxos zero após a janela, não cauda completa.

Decisão: d7 referência projetada de precisão, mista d6/d7 candidata intermediária, d6 baseline, d8 referência fina. Próximo: robustez em transientes e janelas mais longas, custo real e integração mecânica. Nenhuma alteração física, benchmark controlado, render ou promoção. Geometria piloto, 12 dependências de regeneração pendentes. Parâmetros definidos nesta etapa.

Reprodução no pacote local G3_D7_369.zip (29 entradas SHA256SUMS verificadas). Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Numba 0.65.1, uma thread. Consulte CHECKPOINT.md local para comandos e insumos. Publicação parcial: fine_replay.py e relatório; d7.py, demais dependências e binários permanecem no pacote.
