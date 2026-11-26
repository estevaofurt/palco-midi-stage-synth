# G3.12o — polifonia do app e motores existentes

G3.12n run 45771662496 aprovado: Chromium 44100 Hz, preferência 128 persistida, pool 128, IDs 1..128 ativos, Stage 128/128, roubo 129 substitui 1, camada reduz Stage a 64, pico analisador 0.0074638016521930695. Artefato 15094761162 G3-app-polyphony-preview. Não certifica deadlines de hardware. Teste Node dos pools 32..192 e política aprovados.

Ampliar prova navegador para solicitações 128/192, manter 40 amostras do analisador ao longo de ~2s, verificar sinal finito, vozes ainda ativas e progresso do relógio de áudio >=0.8 do tempo de parede; diagnóstico funcional, não medição de underrun/latência. Limites de camadas iguais. Não alterar regra de capacidade.

Benchmark dos motores existentes B/C/D, objetos de teste com pools ampliados, sem modificar presets de qualidade, 72 cenários: 3 motores × 2 taxas × 2 qualidades × 6 capacidades 32/64/96/128/192/256. 100 blocos aquecimento, 200 cronometrados de 128, sustain quando suportado, verificar vozes ativas, áudio finito e não silencioso, substituição e liberação. Margem p99 <=70%, zero overruns e todas vozes ativas. Picos brutos antes do grafo de proteção, não confundir com saída de áudio final. Não certifica Windows/Android, browser completo, FX, ou G3 físico. Mantém fontes estáveis e main intactos.
