# G3 — Compactação por paridade temporal e simetria espacial

Continuação de G3_Enriquecimento_369. 62 entradas verificadas por execução: 5 insumos, 20 acoplamento, 25 enriquecimento, 12 observadores. 369 portas, 127.825 estados, tampo d3, abertura d3/mista/d6, 48 kHz/384 kHz. Nenhuma alteração de polos, amortecimento ou seleção de direções.

A base Legendre discreta tem paridade sob inversão dos oito subpassos. Assim K_l[b,a]=(-1)^(a+b) K_l[a,b]. Mantêm-se 21 pares de 36, a metade não redundante do eixo espacial x (31 de 60 índices), espectros reais e somente 3 coeficientes superiores ativos. O operador retorna apenas saídas superiores ativas, todas as inferiores; não deve ser usado para recuperar as saídas superiores d4-d6 descartadas. Simetria máxima relativa 2,81e-14. A compressão é algébrica, não truncamento de lags. A seleção mista ainda usa seis coeficientes na grade inferior.

8/8 circuitos fechados de regressão, 64 intervalos cada, quatro excitações por configuração mista/d6. Máximos: fluxo 5,76e-16, carga 1,17e-15, pressão 8,63e-16, energia 1,53e-16, trabalho 6,47e-16, continuidade ativa 2,72e-15. Nenhum trabalho acumulado negativo observado.

320 intervalos de exterior isolado (fluxo d6 independente de 64 intervalos repetido cinco vezes), 301 lags completos, volta do anel, preview sem avanço e reset. Erro 1,3124e-15, pós-preenchimento 1,3213e-15. Baseline CompactStream e ParityStream, uma thread, ordem fixa, execução única, aquecimento dois passos; não benchmark controlado.

| Métrica | Baseline | Paridade |
|---|---:|---:|
| Kernel bytes |322479360|97191696|
| Histórico bytes |107493120|80619840|
| Média ms |30,2510|16,6881|
| Histórico completo ms (19 intervalos) |54,0208|30,1637|
| P99 ms |55,8007|31,3026|

Total persistente 429972480 -> 177811536 bytes, redução 58,65%; kernel -69,86%, ganho médio 1,81x. Exclui projeções, campos, temporários e estados da cavidade. Ainda muito acima de 20,833 us/intervalo. Não demonstra ganho específico misto sobre d6.

Novo transiente independente: seed 271132, 64 blocos de ruído nos coeficientes superiores (amplitude 0,1, envelope senoidal), seguidos por 64 blocos de fluxo superior zero; abertura inferior evolui implicitamente. 128 blocos = 2,667 ms. Referência d8 recalculada causalmente, 1024 subpassos. 4/4 controles de conservação aprovados, referência fina 1,4012e-14, trabalho fino 3,4335e-15. Pressão convoluída com fluxo zero somente após o fim da janela; não é cauda completa do piano.

| Modelo | Pressão fina % | Projetada % | Pior receptor fino % | Pior receptor projetado % | Fluxo inferior durante silêncio % |
|---|---:|---:|---:|---:|---:|
|d3|4,345266|1,512909|5,001852|2,282676|12,172381|
|mista|1,080810|0,277299|1,260249|0,392564|5,218189|
|d6|0,957980|0,087733|1,127271|0,108227|4,919143|

Nenhuma configuração projetada passa o critério exploratório de 1% de pressão fina individual no novo caso. D6 candidata de precisão, não aprovada universalmente. Normas L2, não erro audível. Continuidade fina dos modelos projetados não avaliada neste ensaio. Próximo: testar d7 e enriquecimento direcionado por sensibilidade dos receptores em pontos independentes, ampliar janelas. Sem render, integração mecânica ou promoção; geometria piloto e 12 dependências de regeneração pendentes. Parâmetros definidos nesta etapa.

Reprodução no pacote local G3_Enriquecimento_Otimizado.zip (23 entradas verificadas), Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Numba 0.65.1. Conferir SHA256SUMS; definir OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1. Argumentos dos scripts: raiz restaurada, pasta G3_Acoplamento_369, pasta G3_Enriquecimento_369, pasta G3_Observadores_369. Executar verify.py --mode closed e --mode ring, depois transient.py. Os binários e runners integrais permanecem no ZIP local.

Git blob IDs locais: parity_stream.py 65923687324316b7be1dab0a7f6dce760e9a58ef; verify.py 5b654c1b1532e4711cffba5ef818873292a50531; transient.py 9cdd66d9af28bd68a60cb9030d3ccdbed0af39e2; SHA256SUMS 828760fc25c3d6f5562ec08f4d005a33d03a6e3e.
