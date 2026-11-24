# STAGE SYNTH C3X — F1.5: limites da identificação radiativa e ablação auditiva da V10

**Estado: F1 específica do Yamaha C3X ainda PENDENTE.** Experimentos matemáticos e uma comparação de caminhos **do próprio motor V10**. Nenhuma gravação ou medição espacial C3X foi obtida, nenhum sample foi usado como fonte sonora, **nenhuma alteração do DSP V10 ou do Stage publicado** foi feita. **F7 NÃO foi iniciada/concluída** por estes testes.

## 1. O problema demonstrado na etapa F1.4

Na V10, a rota de áudio é, esquematicamente, `sinal_direto_das_cordas + (sinal_direto * IR_modal_sintética) + saída_dos_modos_estimulados_da_ponte`, seguida de filtragem. A decomposição F1.4 provou numericamente que a IR sintética reforça H4 e provoca interferência destrutiva em H5. O fato de o filtro causar esse cancelamento **não determina como deveria ser a resposta de um tampo acústico real**.

O que mede a gravação C5 do Salamander é **pressão após fonte e caminho acústico desconhecidos**, com posição de microfones específica. Não possuímos simultaneamente velocidade espacial do tampo, força aplicada à ponte e pressão de microfone, indispensáveis para identificar os blocos físicos separadamente. C5 também não é C3X. As três referências C5 permanecem licenciadas CC BY 3.0, Alexander Holm, com hashes originais arquivados no Stage; nenhum FLAC é importado para esta pesquisa.

## 2. Experimento independente: radiação espacial de duas regiões hipotéticas

Implementamos `radiation_identifiability.py`, uma *quadratura discreta ilustrativa* da integral de Rayleigh para **patches fictícios** de uma superfície plana com baffle infinito:

\[
 p(\mathbf x,\omega)\approx \frac{j\rho\omega}{2\pi}\sum_i A_i v_i(\omega)\frac{e^{-j\omega r_i/c}}{r_i},\quad r_i=\lVert\mathbf x-\mathbf x_i\rVert.
\]

- `A_i` em m², `v_i` em m/s, densidade `ρ` em kg/m³, `c` em m/s, `r_i` em m, pressão `p` em Pa.
- Duas regiões iguais de 0,04 m² a ±0,24 m, normal 1 mm/s, microfones a 1 m do plano, deslocados em x.
- O 4º parcial foi **assumido** como velocidade em fase nas duas regiões; o 5º como velocidade em oposição. Essas formas modais são inventadas **propositadamente** para testar informação acessível, não estimadas de piano físico.

| Microfone de pesquisa | \|p4\| simulado (Pa) | \|p5\| simulado (Pa) | 5º versus 4º (dB) |
|---|---:|---:|---:|
| Central (x=0 m) | 0,09808 | 0,00000 | cancelamento exato por simetria |
| Deslocado (x=0,50 m) | 0,04016 | 0,06381 | +4,02 |
| Deslocado (x=1,00 m) | 0,07145 | 0,07193 | +0,06 |

**Resultado demonstrado:** o mesmo movimento hipotético de placa pode fazer H5 desaparecer de um ponto de escuta e reaparecer em outro por diferença de fase e propagação. Isto NÃO afirma que o H5 real do C5/C3X se comporte assim. O modelo ignora back-reaction do ar na placa, borda finita, nervuras, material ortotrópico, superfície contínua, aro, tampa e sala. **Não é simulador acústico aprovado**.

### Não-identificabilidade rigorosa com um único microfone

Uma única gravação de pressão observa `P(f)=S(f)·H(f)` (na simplificação SISO). Para qualquer `G(f)` complexo não nulo, `S'(f)=S(f)·G(f)` e `H'(f)=H(f)/G(f)` reproduzem **o mesmo P(f)**. Sem dados independentes, não se pode atribuir exclusivamente ao martelo, corda, tampo ou radiação o desequilíbrio H4/H5. Em sistemas com múltiplas regiões irradiantes a ambiguidade é ainda maior. O exemplo é testado em `test_radiation_identifiability.py`.

## 3. Comparação audível feita apenas com a V10 original

`diagnostic_v10_output_paths.py` reutiliza `c4_v10_stem_ablation.py` da F1.4; **não altera nenhuma equação, estado de corda, evento do martelo ou ponte**. Compara o WAV V10 original contra uma ablação **só de saída**, em que a IR modal sintética não é adicionada. Não é uma nova proposta de timbre nem o cálculo de radiação de F7.

| Dó4, 35–255 ms | H4 na V10 | H4 sem IR modal | H5 na V10 | H5 sem IR modal |
|---|---:|---:|---:|---:|
| MIDI 75 | +0,85 dB | −12,71 dB | −38,22 dB | −17,82 dB |
| MIDI 115 | +2,35 dB | −11,33 dB | −41,60 dB | −21,15 dB |

Valores relativos à fundamental de cada versão, não dB de pressão absoluta. A nota MIDI 60 foi mantida; a mesma física produz ambas as saídas, e a reconstrução da V10 coincide amostra por amostra com o renderizador original dentro de `1,2×10⁻⁷` antes da quantização WAV.

**Dois protocolos auditivos diferentes:**
- `C4_AB_V10_original_vs_sem_IR_modal_DIAGNOSTICO.wav`: **um ganho comum** a todas as versões, preserva diferença real de intensidade no protótipo. O caminho sem IR modal fica muito mais baixo.
- `C4_AB_V10_vs_sem_IR_modal_RMS_IGUALADO_DIAGNOSTICO.wav`: equaliza RMS de sustentação na janela 120–620 ms **para comparação subjetiva da cor**, portanto **não serve para analisar energia, dinâmica ou pressão acústica**. O fator de reforço da versão sem IR é ~9,54 (MIDI75) e ~9,98 (MIDI115), antes de ganho mestre. Não confundir equalização de volume com autorização para ajustar o produto.

Ambos WAVs são 48 kHz, estéreo, PCM 24 bits, sem clipping, sem sample de terceiros e sem reverb de sala.

## 4. Evidências necessárias antes de desenhar a radiação F7

| Transferência ou parâmetro | Entrada/sensores requeridos | Saída/unidade | Disponível? |
|---|---|---|---|
| Mobilidade mecânica da ponte Y(f) | força calibrada F_ponte [N], velocidade calibrada v_ponte [m/s] com fase sincronizada | (m/s)/N | **Não** |
| Radiação observada de um ponto H_pa(f) | aceleração de ponte [m/s²], pressão de microfone [Pa], cadeia calibrada, mesmo relógio | Pa/(m/s²) | **Não** |
| Radiação distribuída | campo v_n(x,y,f) do tampo, geometrias e posições dos microfones; opcionalmente pressão real para validação | Pa/(m/s) por área | **Não** |
| Pressão de piano real isolado | áudio C5 v1/v8/v16 gravado, posição parcial dos microfones; sem F/velocidade física simultâneas | espectro PCM relativo | **Sim, apenas C5 e apenas pressão** |

O repositório do Stage **já contém** um estimador H1 para futura medição `research/bridge-radiation-h1.mjs`. **Não vamos criar outro equivalente**, nem usar esse estimador com os FLACs C5: faltaria o acelerômetro simultâneo. Mobilidade ponte ≠ aceleração→pressão ≠ campo distribuído de radiação. Em um instrumento real, resposta de caixa, tampa e sala tornam a observação ainda mais complexa.

**Próxima decisão técnica:** manter a V10 intacta e registrar quais parâmetros são *não identificáveis* a partir de C5/pressão isolada. Se forem identificados dados legais e medidos de vibração/ponte sincronizados com pressão, testar o método de inversão em dados originais, validando posições, fase, holdouts, energia e incertezas. Sem isso, não substituir a IR sintética por outra curva arbitrária nem declarar C3X calibrado.

## 5. Testes e reprodutibilidade

- 10 testes sem dados de piano: propagação 1/r, fase de viagem, cancelamento por modo antissimétrico, deslocamento de microfone, linearidade, calibração, fatoração não identificável e entradas inválidas.
- 5 testes da ablação V10: original intacto, divergência ao silenciar IR, restaurar H5, reduzir H4 e arquivos WAV com headroom.
- Total: **15 testes locais aprovados**, com fontes V10 originais preservadas.

```
python -m unittest discover -s research/c3x-physical -p 'test_radiation_identifiability.py' -v
python -m unittest discover -s research/c3x-physical -p 'test_v10_output_paths.py' -v
python research/c3x-physical/diagnostic_v10_output_paths.py \
  --v10-root research/c3x-python/v10 --output /tmp/c3x_f1_5_diagnostic
```

A saída WAV é **artefato diagnóstico local** e não deve ser publicada no aplicativo nem tornar-se sample em um motor.

### Fontes científicas para distinguir energia mecânica e radiação

- Chaigne, Cotte e Viggiano, *Dynamical properties of piano soundboards* (JASA, 2013): https://pubmed.ncbi.nlm.nih.gov/23556610/
- Ege e Boutillon, *Vibroacoustics of the piano soundboard: Reduced models, mobility synthesis, and acoustical radiation regime*: https://arxiv.org/abs/1305.3057
- Modelo com Rayleigh integral e transferência velocidade→pressão: https://pub.dega-akustik.de/DAGA_2016/data/articles/000537.pdf
- Stage Synth, estimador prévio de ponte→pressão: `research/bridge-radiation-h1.mjs`, com documentação `docs/VERIFICACAO_TRANSFERENCIA_RADIATIVA_H1_E11_2026-11-23.md`.

**Governança:** F0 concluída, F1 C3X PENDENTE, F2–F13 sem avanço de estado. Este material é só pesquisa. Revisão acústica e direitos comerciais continuam necessárias para qualquer modelo de piano anunciado como Yamaha C3X verificado.
