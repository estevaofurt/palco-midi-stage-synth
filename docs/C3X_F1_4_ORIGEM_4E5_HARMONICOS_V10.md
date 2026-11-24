# STAGE SYNTH C3X — F1.4: diagnóstico da origem dos 4º e 5º harmônicos da V10

**Estado:** resultado de pesquisa reproduzível; **não** validação do Yamaha C3X. **V10 intacta**, sem nova versão sonora ou alteração no Stage publicado. **F1 específica de C3X pendente**.

## Síntese do resultado

Conseguimos separar **três caminhos do áudio original da V10** sem modificar a física calculada: (1) sinal direto de cordas, (2) sinal direto das cordas convoluído com a resposta impulsiva **modal sintética** do corpo e (3) saída radiativa de 11 modos estimados da ponte/tampo. Em todas as análises, os três caminhos foram filtrados como no motor original, somados em fase e **sem normalização**. A comparação amostra por amostra com `render_sequence_v10_action` comprovou diferença máxima de **1.2e-07** (arredondamento para float32). Portanto o fenômeno é da V10 original, não de uma nova versão.

### 1. Origem da ênfase do 4º harmônico

A resposta modal **sintética** do corpo possui ganho acentuado perto do 4º parcial estimado do Dó4 (~1050.64 Hz), em relação à saída apenas direta:

- Canal esquerdo: **+21.29 dB**.
- Canal direito: **+17.93 dB**.

No Dó4 da V10 com velocidade MIDI 75, janela inicial de 35–255 ms, o 4º harmônico do áudio somado aparece **+0,85 dB** relativamente à fundamental, mas na rota direta isolada ficaria perto de **−12,9 dB**. A rota modal de corpo domina esse harmônico: o módulo da sua componente está a **−0,63 dB** do total. A saída adicional dos modos de tampo, com os ganhos atuais, fica a aproximadamente **−62,8 dB** da amplitude total desse parcial. Isso é específico deste arranjo de saída, **não demonstra que um tampo físico real tenha pouca radiação**.

### 2. Origem da falta do 5º harmônico

Perto do quinto parcial esperado (~1316.39 Hz), o filtro **corpo sintético + sinal direto** apresenta um vale de interferência:

- Canal esquerdo: **-5.61 dB** relativo à rota direta.
- Canal direito: **-10.94 dB** relativo à rota direta.

A diferença do ganho espectral entre o 4º e o 5º harmônicos é **26.90 dB (esquerda)** e **28.87 dB (direita)**. Este segundo método usa apenas a transformada complexa da IR sintética da V10, sem selecionar picos de um arquivo de áudio, e portanto confirma a origem algorítmica do vale.

Ao analisar o áudio real sintetizado (três componentes com a mesma fase e janela), as componentes direta e modal têm uma defasagem próxima de **169° no ataque** e **158° na sustentação**. A perda de magnitude pela soma de vetores complexos, comparada à soma das magnitudes isoladas, se mantém em todas as três intensidades:

| Velocidade V10 | 5º parcial, ataque (rel. fundamental) | Cancelamento de fase, ataque | Cancelamento de fase, corpo (260–700 ms) |
|---|---:|---:|---:|
| MIDI 25 | -37.10 dB | -16.38 dB | -9.75 dB |
| MIDI 75 | -38.22 dB | -16.26 dB | -9.73 dB |
| MIDI 115 | -41.60 dB | -16.33 dB | -9.75 dB |

Na velocidade MIDI 75, o 5º parcial fica em cerca de **−38,22 dB** relativamente à fundamental no mix. Na rota direta isolada, a estimativa na mesma frequência e janela é **−17,84 dB**. Isto não autoriza simplesmente retirar a resposta de corpo: seria trocar um filtro arbitrário por outro caminho acústico sem validação física, além de perder outros parciais e a ressonância de corpo.

### 3. Correção necessária da auditoria anterior: pico lateral não é 5º harmônico

O detector anterior procurava um pico muito amplamente para o 5º parcial no ataque. Escolheu uma componente lateral próxima de **1.291 Hz**, fora da faixa predita para o **5º harmônico físico da V10**, próximo de **1.317 Hz** (posição prevista pela frequência e pelo B configurados). O resultado publicado anteriormente para a V10 na intensidade média era **−30,37 dB**, mas o 5º parcial identificado agora pelo método fisicamente restrito é **−38,22 dB**.

| Camada C5 de referência | 5º parcial C5 no ataque | V10 anterior: pico lateral | V10 corrigido: 5º parcial | Diferença C5−V10 corrigida |
|---|---:|---:|---:|---:|
| Suave (v1/MIDI25) | −29,20 dB | −28,35 dB | −37,10 dB | +7,90 dB |
| Média (v8/MIDI75) | −14,52 dB | −30,37 dB | −38,22 dB | **+23,70 dB** |
| Forte (v16/MIDI115) | −12,10 dB | −31,50 dB | −41,60 dB | +29,50 dB |

**C5 e V10 são instrumentos distintos**; MIDI25/75/115 é mapeamento ilustrativo, *não* pareamento de velocidades físicas de martelo. A licença dos arquivos C5 é CC BY 3.0, Alexander Holm/Salamander Grand Piano; os três FLAC originais já foram conferidos por SHA-256 na execução do [GitHub Actions #45313904712](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313904712). **Nesta F1.4 foram usados somente os números publicados da análise C5, sem baixar novamente nem distribuir os FLACs**.

O método corrigido evita interpretar componentes laterais ou ruído como a frequência do 5º parcial. Os ajustes de B, o espaço sonoro/microfone, o temperamento/afinador, a tolerância do algoritmo e a evolução temporal continuam fontes de incerteza. A correção dos picos não equivale a validar parâmetros físicos internos.

## Protocolo reproduzível e validações

- Gerar evento V10 idêntico ao original: comando de nota MIDI 60 em t=0,025 s, 1,74 s de tecla pressionada, sem pedal; action scheduler V10 com impacto estimado e física V9 compartilhada **sem alteração de parâmetros**.
- Integrar as cordas reais aproximadas em duas polarizações, suas simpáticas e os 11 modos de tampo; decompor `direct`, `body`, `board` e aplicar o mesmo filtro Butterworth.
- Verificar identidade do áudio completo com `render_sequence_v10_action` original em float32, erro absoluto abaixo de 2×10⁻⁶; verificar soma temporal e complexa dos três caminhos.
- Medir ataque (35–255 ms), sustentação (260–700 ms), cauda (900–1400 ms) em relação ao **mesmo onset** encontrado no mix; usar um único pico na faixa estreita predeterminada de cada harmônico, aplicado a **todos os caminhos**.
- Calcular perda de fase como `20 log10(|direct+body+board|/(|direct|+|body|+|board|))`, sempre ≤0 por desigualdade triangular.
- Calcular separadamente a resposta em frequência analítica do filtro `direct_gain + body_gain·H_modal(f)`, sem usar áudio; confirmar que realça parcial 4 e atenua parcial 5.
- Testes automatizados do algoritmo, com comparação adicional em 44,1 e 48 kHz; nenhum arquivo sonoro externo como entrada.

Executar no checkout do PR:

```bash
python -m pip install -r research/c3x-python/v10/requirements.txt
python -m unittest discover -s research/c3x-physical -p 'test_c4_v10_stem_ablation.py' -v
python research/c3x-physical/c4_v10_stem_ablation.py \
  --v10-root research/c3x-python/v10 \
  --c5-metrics research/c3x-physical/C5_C4_verified_numeric_report.json \
  --prior-v10-profiles research/c3x-physical/v10_c4_profiles.json \
  --output F1_4_V10_STEM_RESULTS.json
```

## Conclusão e decisão F0–F13

Foi identificada uma **causa algorítmica demonstrável dentro da V10** para o desequilíbrio entre os 4º e 5º parciais: a resposta modal sintética somada ao sinal direto possui reforço do quarto e cancelamento do quinto, de forma consistente por intensidade e por medição analítica do filtro. **Não é evidência de propriedades reais do Yamaha C3X** nem prova de que remover o filtro melhoraria o piano realista.

A prioridade é **F1: obter/validar resposta radiativa legítima e condições de captação**, mesmo que em pesquisa exploratória com C5, **antes** de especificar ou recalibrar a radiação física F7. A V10 permanece intacta como referência histórica, a F1 específica C3X continua pendente, e F2–F13 **não são promovidas**.
