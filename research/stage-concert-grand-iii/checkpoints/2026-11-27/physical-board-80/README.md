# G3 — Tampo físico reconstruído de 80 coordenadas

Recuperados G3_Reconstrucao_Estrutural, G3_Reacao_Acustica e G3_Terminacoes_das_Cordas. 73/74 entradas dos manifestos internas verificadas; structure.npz (112 MiB) é separado do ZIP original. Cinco de 12 dependências recuperadas, sete restantes. Nenhuma divergência. Base reduzida nominal de 80 coordenadas: massa unitária conforme fonte, K/D/portas idênticas entre basis_80.npz e integrated_80.npz, ambos vinculados ao manifesto de entrada da radiação. Agregação 4x4 das células 120x120 reproduz A*scale (4,0658063e-16) e T DCT exatamente. Não revalidada a ortogonalidade na estrutura integral ausente. Frequências estruturais 18,255–1607,553 Hz. Sem cordas ou martelos.

Cavidade 127.825 estados e 369 portas; comunicação 48 kHz, integração acústica 384 kHz. Tampo constante por intervalo. Pulso de força nominal 1 N, meia senoide por 32 intervalos nas portas MIDI 48/60/64. Nove ensaios principais: d3/d7 128 blocos cada, d8 64; todos passaram tolerância 1e-10. Máximos: energia mecânica 1,56050e-14, conjugação 6,33244e-18, cavidade 1,23680e-18, balanço integrado 1,55822e-14, continuidade projetada 1,78184e-15, solução simultânea 1,50698e-15; mínimo trabalho acumulado exterior normalizado zero. Execução conjunta de 128 blocos interrompida na preparação d8; d8 repetido isoladamente em 64. Comparação restrita ao prefixo comum. Não há segunda resolução fina independente nesta base.

| Erro máximo relativo % | d3 | d7 |
|---|---:|---:|
| Velocidade | 0,0000005443 | 0,00000002279 |
| Carga mecânica | 0,000200660 | 0,0000101835 |
| Fluxo inferior | 0,329718 | 0,0536244 |
| Pressão fina individual | 0,145015 | 0,0182103 |
| Pressão filtrada individual | 0,000329729 | 0,0000485158 |

Pressão por convolução dos 512 subpassos comuns e fluxo zero depois; janela precede chegadas dos dois receptores. Não representa ataque/cauda reais. Filtro Kaiser 617 taps diagnóstico. Critério exploratório de 1% satisfeito apenas nesses pulsos; falhas anteriores preservadas. Parâmetros experimentais definidos nesta etapa, sem alterar K/D. Sem benchmark, render, promoção ou alteração de main.

Reprodução: pacote G3_Tampo_Fisico_80.zip (34 entradas verificadas SHA-256) contém scripts, resultados e logs. Verificar manifestos e executar com uma thread BLAS/OMP/Numba. Primeiro board.py /raiz/restaurada /pasta/G3_Acoplamento_369 --blocks 128 --orders 3 7; salvar results.json como results-128.json. Depois board.py com --blocks 64 --orders 8, salvar results-d8-64.json; audit_board.py /raiz/restaurada /pasta/G3_Observadores_369 PRIOR_MISSING.sha256. Este commit registra resultados e hashes, não os scripts completos nem binários. Próximo: recuperar escala histórica original scale_geometry.json (85a57d1552dc44cf2d8595cc91b2e0321b3c5f5835970187bb1bb38b8b048ab5), validar procedência, integrar cordas e martelos. Não adotar novas terminações reprovadas no checkpoint enviado.
