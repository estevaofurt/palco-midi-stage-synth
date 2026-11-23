# P1 — dispersão de duas seções allpass (experimento isolado)

**Base:** Stage Synth main v1.12.4, commit 8683246dcdb8557dc129bee15249dc78aca80411.

## Objetivo
Testar se duas seções allpass com compensação da fase na fundamental aumentam a inarmonicidade do guia de onda e melhoram a relação entre parciais, sem reintroduzir estalos ou comprometer 32–64 notas.

## Implementação
- Cópia do núcleo físico-mecânico em physical-piano.js nesta pasta, sem alterar o arquivo equivalente na raiz, a interface, presets ou MIDI.
- Nova seção allpass de primeira ordem por corda, coeficiente derivado da rigidez da nota (provisório), com estados alocados na construção de cada voz e reinicializados no note-on.
- A duração do loop é corrigida pela fase de **ambas** as seções na fundamental.
- Todas as operações em tempo real usam variáveis/estados prealocados; nenhum Array ou objeto novo na amostra.
- Processador de teste recebe identificador distinto para impedir colisão com o motor normal.

## Verificações
Arquivo: tests/dual_dispersion_p1.test.mjs
1. Medir notas C2/C4/C6 contra o motor C atual usando o analisador acústico P0; checar deslocamento de inarmonicidade, cents e picos.
2. Validar que 32 e 64 notas permanecem alocadas, sem roubo prematuro de voz e sem clipping/NaN no render offline curto.
3. Rodar npm run check e verificar relatório do GitHub Actions. Se falhar, corrigir no experimento; não alterar a raiz.

## Bloqueios para integração
- As magnitudes de inarmonicidade são *estimativas espectrais*, não alvos físicos medidos em piano seco. Não concluir superioridade de timbre por aumento de B.
- Ganho, dinâmica por velocity, amortecimento de parciais e consumo de CPU ainda exigem análise e escuta.
- Este arquivo **não está no seletor do Piano Acústico** e não é uma versão publicada.
- A v1.9.5 e a raiz v1.12.4 continuam intactas. Antes de qualquer integração, ensaiar PC/Moto g04s, acordes e pedal no AudioWorklet real e comparar A/B nivelado.
