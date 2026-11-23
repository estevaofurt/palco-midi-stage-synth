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


## Resultado da primeira medição (não homologado)
A execução inicial do GitHub Actions em 23/11/2026 (run 45094402305) obteve **92 testes aprovados e 1 falha**. A exigência experimental de aumento mínimo de 5% do coeficiente B de C4 falhou: C4 / Japanese / velocity 80 passou de **0,0001102457** (motor C) para **0,0001129035** (P1), incremento de somente ~2,4%.

- C2: 0,0000547790 → 0,0000552145; C6: 0,0002769985 → 0,0002784529.
- Em C4, o pico caiu de 0,06232 para 0,05370 no sinal médio estéreo; não confundir redução de volume com fidelidade.
- Nenhuma conclusão auditiva é permitida a partir desses números. Os modos ressonantes independentes preservam sua própria rigidez: melhorar só a fase da linha de atraso tem efeito limitado no espectro final.
- O teste foi reestruturado para **isolar o guia de onda** e medir seu efeito real, mantendo o aumento de B global como objetivo ainda não atingido. Isso **não** autoriza integrar o experimento no app.
- Próximos passos: verificar métricas isoladas, estudar coerência entre modos e linha dispersiva, corrigir perdas por frequência, repetir benchmark de CPU e só depois comparar a audição.

## Diagnóstico isolado aprovado (CI 45094508441)
- **93 testes Node aprovados, zero falhas** para o código experimental revisado, incluindo 32/64 vozes e estimativa de afinação nas três regiões. Não há teste em hardware real.
- C4 waveguide somente, sem modos auxiliares: B estimado **0,0000159021 → 0,0000180928** (~13,8%). O filtro novo efetivamente muda o guia de onda.
- C4 saída completa, com os modos originais: **0,0001102457 → 0,0001129035** (~2,4%). Os modos aditivos limitam o efeito global, e a mistura altera o pico.
- **Conclusão:** mecanismo matematicamente operacional, mas **critério de fidelidade não atingido**. Manter o experimento sem merge e sem opção no Piano Acústico até redesenhar coerentemente a dispersão da guia e dos modos, sem parâmetros arbitrários e com comparação de áudio seca real.
