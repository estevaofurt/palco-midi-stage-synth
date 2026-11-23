# Stage Synth — baseline acústica reproduzível v1.12.4

**Linha:** research/piano-acoustic-metrics-v124 (somente diagnóstico; sem modificação de timbre).
**Base verificada:** main @ bcfb40a8dea86d65d012cbc7d0695127fbddf58a (22/11/2026).

## Finalidade
Estabelecer medidas repetíveis para A modal adaptado, B waveguide v1.9.5 preservado e C físico/mecânico v1.12.3 antes de corrigir inarmonicidade e decaimento.
Não altera DSP, AudioWorklet, rotas, seis módulos, presets, FX, MIDI nem migração. Não publica WAVs privados. A v1.9.5 permanece disponível. A v1.11 externa continua não localizada.

## Reproduzir
Requer Node 22+ sem dependências extras.
- npm run check — checagem de sintaxe e testes Node.
- node tests/measure_piano_engines.mjs — tabela curta.
- node tests/measure_piano_engines.mjs --json > piano-acoustic-baseline.json — relatório completo.
- Workflow .github/workflows/piano-acoustic-baseline.yml executa os testes e guarda o JSON como artifact por 14 dias.

Matriz: **3 motores × 4 pianos (Japanese/American/Felt/Upright) × 3 notas (C2/C4/C6) × 3 velocities MIDI (32/80/120) = 108 casos**. Cada nota seca tem 1,7 s, 48 kHz e blocos de 128; saída é média dos canais estéreo; não inclui efeitos. Os motores físicos usam qualidade eco. C usa acoplamento ativo.

## Métricas
- Pico, RMS, clipping e amostras não finitas.
- RMS de ataque (0–20/20–80/80–250 ms) e sustentação (250–450/800–1000/1400–1600 ms).
- Desvios em cents e magnitudes relativas de até 8 parciais; amplitude por parcial nas fases 160–300, 520–700 e 1120–1300 ms.
- Inarmonicidade B aproximada a partir dos picos da FFT Hann (32768 pontos, interpolação de frequência). Ausência de parciais confiáveis produz resultado null; alvos não são impostos.
- Tempo offline máximo por bloco não prova cumprimento de prazo no navegador.

## Limitações
A janela finita (~1,46 Hz de espaçamento entre bins), vazamento espectral, batimento e parciais fracos tornam B uma **estimativa**, não medição física exata. RMS por intervalos não é T60 absoluto nem decaimento isolado de corda. Não substitui comparação auditiva nivelada. O baseline monofônico não atesta 32–64 vozes: conservar testes de polifonia existentes e exigir avaliação no PC e Moto g04s reais.

## Validação
- **5/5 testes locais Node do analisador aprovados** (FFT, amplitude, B sintético, decaimento e detecção de anomalias); não é a suíte integrada.
- Regressões do repositório, matriz 108 casos e relatório do CI só podem ser marcados aprovados após execução verificada do workflow.
- DSP principal e v1.9.5 não modificados; nenhum motor novo foi promovido.

## Próxima etapa
Ler o relatório completo para priorizar problemas por registro/velocity/modelo. Depois prototipar dispersão de ordem superior e perdas dependentes de frequência **isoladamente**, reexecutar a matriz e validar 32/64 vozes, efeitos, MIDI, estalos e escuta antes de qualquer integração.
