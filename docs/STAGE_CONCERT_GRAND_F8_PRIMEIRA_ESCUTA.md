# Stage Concert Grand — F8 primeira escuta física experimental

Base F7.3: 7a5a068457f89d9840f71515745cdf8f8786196b. Renderizador: bbc7861c197145c37b21845deeb811db0db6f7ec. Geração em JavaScript V8 com fontes recuperados do GitHub. Não executado CI Node nem hardware. Nenhuma alteração em main/V10/UI/DSP público.

## Arquivos
Quatro WAV PCM 16 bits, estéreo 48 kHz, 0,5 s de trajetória mecânica mais atraso de propagação (~0,505 s de arquivo), 97000 bytes cada. São saídas de pesquisa, não samples incorporados ao motor. Ganho único 0,36767023440034063 FS/Pa, zero clipping. Fade editorial de 40 ms no fim do arquivo para evitar corte abrupto; não representa abafador físico. Sem EQ de timbre, sem IR externa, sem normalização individual. O filtro de exportação espectral comum é unitário até 8 kHz e cosseno até 12 kHz; pode gerar pequeno pré-ringing. Não constitui filtro anti-alias ideal antes da média temporal. Não confundir banda de exportação com banda validada do tampo.

Configuração: taxa mecânica 96 kHz, base Mindlin original 4 kHz, 337 modos ativos abaixo de 3 kHz, 282 modos de cordas, ligação e martelo F6.4/F7.3; observadores x=0,90 e 1,20 m, y=0,38 m, z=1 m; malha 64x50. Acelerações médias em pares de passos, convolução geométrica por FFT, sem sala. Após separação confirmada por folga >2 mm, velocidade negativa e ausência de força por 2 ms, seguir movimento livre do martelo e relaxação da memória por passo, verificar ausência de recontato. Cache da resposta afim do tampo, preservando resolução simultânea. Não é validação da ação completa, pedal ou abafador. O registro longo de 1,2 s em quatro casos numa única chamada excedeu o limite de execução do ambiente; quatro registros de 0,5 s foram gerados individualmente.

| Arquivo | velocidade m/s | R | pico Pa | RMS inicial Pa | RMS final Pa | pico PCM | clipping |
|---|---:|---:|---:|---:|---:|---:|---:|
| C4_suave_R.wav | 0.5 | 1 | 0.379301 | 0.129548 | 0.062023 | 0.139458 | 0 |
| C4_medio_R.wav | 1 | 1 | 0.812975 | 0.280472 | 0.135508 | 0.298907 | 0 |
| C4_forte_R.wav | 2.5 | 1 | 2.175863 | 0.751937 | 0.357457 | 0.800000 | 0 |
| C4_medio_sem_R.wav | 1 | 0 | 0.837612 | 0.292855 | 0.154637 | 0.307965 | 0 |
RMS inicial primeiros 100 ms, final últimos 100 ms de trajetória, antes de fade de exportação. Resíduo máximo energético global 1,055e-14 J, aumento observado zero, todos impactos com separação e sem recontato. A resistência reduz RMS final do toque médio de 0,154637 para 0,135508 Pa (12,37%). Não é calibração do SPL real.

## Reprodução
`node research/stage-concert-grand/f8-demo.mjs 0.5 f8-output` (script disponibilizado, não executado em Node nesta sessão). Geração V8 com os mesmos parâmetros, individualmente. Arquivos e hashes de blobs no audio/manifest.json. A execução de 1,2 s permanece possível no ambiente local com memória e tempo suficientes, não testada. F8 entregue como primeira escuta de ataque e sustentação curta; não é Dó4 completo homologado. Abafador físico, sustentação longa, reatância, convergência de banda superior e precisão de fase pendentes. F9: avaliação auditiva pelo usuário, comparação com V10 e C5 com ganho compatível, antes de qualquer expansão. 32–64 vozes não homologadas.