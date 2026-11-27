# G3 — Recuperação dos observadores de 369 portas

Continuação do checkpoint de redução passiva. 23 entradas do manifesto anterior conferidas; branch de pesquisa retomada em e1c09bd64ed30ae446ab78612b0a91aa3ae0b788. Modelo piloto, d3/48 kHz, referência fina 384 kHz. Nenhum áudio gerado.

Recuperação algébrica/numérica das coordenadas relativas dos dois receptores a partir de aperture.py e dos kernels arquivados. Ajuste do primeiro receptor em 329,6276, 1000 e 2000 Hz sobre 12 portas b16, inicialização b4. Alturas 0,5 e 1,5 m e deslocamento 0,25 m definidos no código original. Coordenadas relativas à origem da malha: (0,852; 0,8022857142857145; 0,5) e (1,102; 0,8022857142857145; 1,5) m. Resíduo do ajuste 4,713e-15. Replay de kernels completos b16/12 portas 2,931e-13 e b64/48 portas 1,760e-13, segundo receptor e b64 não usados no ajuste. Observador b64 completo 2439 x 2 x 369. Primeiras chegadas 559 e 1679 subpassos.

Replay dos fluxos d3/d8 arquivados, 64 blocos por caso, 512 subpassos, entrada superior idêntica. Convolução linear de 2950 amostras, fluxo zero após a janela. Conferência direta em quatro índices por caso: erro máximo 1,533e-15; causalidade antes das chegadas dentro de 1e-10.

| Caso | Pressão fina L2 relativa % | Pressão projetada L2 relativa % |
|---|---:|---:|
|Ruído|3,349517|1,027642|
|Pulso|0,001924|0,001012|
|Alta|0,148421|0,048411|

Ruído: pior receptor 3,471052% fino e 1,163174% projetado. d3 não aprovado universalmente pelo critério experimental de 1%. Referência d8 discreta, sem validação audível, não representa cauda real ou geometria absoluta do gabinete. Manter modelo integral FusedGrouped + CompactStream, d3 prioritária; investigar d6/mista em 369 portas, especialmente banda larga. Doze dependências de regeneração ainda pendentes.

Reprodução no pacote local G3_Observadores_369.zip, conferir SHA256SUMS e os insumos. Uma thread BLAS/OMP:
```
python observer.py /raiz/restaurada /pasta/G3_Acoplamento_369
python pressure.py /pasta/G3_Acoplamento_369 /pasta/G3_Referencia_Fina_369
```
O commit publica o relatório e manifesto dos artefatos locais, não os binários nem os scripts integrais. Parâmetros definidos nesta etapa. Sem promoção ou mudança na main.
