# Yamaha C3X — F1: inventário verificável e diagnóstico do protótipo V10

**Data:** 23/11/2026 · **Fase física F1: PENDENTE** · **Decisão:** não avançar para F2/F9/F12/F13 nem substituir o DSP público.

## 1. Conclusão objetiva

A V10 está numericamente consistente, mas a identificação física permanece incompleta. A escala no arquivo `stage_synth_c3x/parameters.py` **não contém comprimentos, tensões, diâmetros, massas de martelo ou inarmonicidade medidos em um C3X**. O oscilador deriva `mu = T/(4*L*L*f_alvo*f_alvo)` para produzir a própria frequência alvo, portanto a auditoria das 88 notas prova afinação **interna**, não afinação física de um C3X. O motor usa IR modal sintética, e não um modelo espacial medido e identificado da radiação do tampo. A ação da V10 é reduzida e possui parâmetros estimados.

A escuta da V10 **não foi homologada**: o titular observou que ainda existe muito a melhorar. Não inferir aprovação a partir do simples pedido de continuidade.

## 2. Fontes externas verificadas sem confundir tipo de evidência

| Fonte | Evidência conferida | Limite e uso permitido na F1 |
|---|---|---|
| [Yamaha Brasil — Série CX](https://br.yamaha.com/pt/musical-instruments/pianos/products/grand-pianos/cx-series/) | Modelo **C3X convencional**: 149 × 101 × 186 cm, 320 kg | **Especificação externa**; não estabelece escala de cordas/tampo |
| [Yamaha EUA — especificações](https://usa.yamaha.com/musical-instruments/pianos/products/grand-pianos/cx-series/specs.html) | 88 teclas, ação Yamaha, martelos CX, pedais damper/sostenuto/shift | Nomes de componentes, sem medições de impacto ou dinâmica |
| [Kemp, PLOS ONE 2023](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0292515) | **Um exemplar C3X real** em St Andrews, nota **Sol2**, dois picos no quarto parcial separados por ~3 cents; microfone Rode NT5/Allen & Heath DT168 | **Medição publicada real de G2**; NÃO é dado do Dó4 ou tabela de física do C3X inteiro; não importar números para C4 |
| [Piano Concerto Dataset, 2023](https://reference-global.com/article/10.5334/tismir.160?tab=article) | 15 trechos de 12 s em Yamaha C3X de estúdio privado (R2), par de Sennheiser MKH 8020 | 180 s **de execução musical processada**; não há resposta física isolada de C4 nem medidas força/ponte; licença específica do áudio a conferir |

**Cuidado:** o artigo Kemp trata primariamente de pontes de **baixo elétrico**; apenas uma figura apresenta o C3X como comparação. A licença CC BY do artigo não concede automaticamente todas as permissões relativas a gravações de terceiros. Não confundimos C3X convencional com C3X espressivo, nem o Yamaha C5 Salamander com C3X.

## 3. Parâmetros específicos do Dó4 presentes na V10 — ESTIMATIVAS, NÃO F1

| Variável | V10 calculada/estimada | Valor físico do C3X |
|---|---:|---|
| Frequência alvo (12-TET, A4=440) | 261.625565 Hz | **Desconhecida**, requer afinação medida |
| Cordas por nota | 3 | A conferir no exemplar |
| Comprimento vibrante | 0.545 m | **Desconhecido** |
| Tensão por corda | 702.63 N | **Desconhecida** |
| Massa linear derivada do alvo | 0.00864001 kg/m | **Desconhecida** |
| Inarmonicidade B | 0.000528449 | **Desconhecida** |
| Massa efetiva do martelo | 0.010125 kg | **Desconhecida** |

**Crítica central:** o caminho de áudio soma componentes de corda, corpo sintético, modos de tampo e filtros. Não é uma simulação identificada de deslocamento do tampo → pressão sonora no microfone. 'Dry' sem reverb de sala não garante fidelidade do caráter acústico.

## 4. Teste objetivo dos três WAVs de apresentação V10

| Arquivo | Clipping detectado | Conclusão |
|---|---:|---|
| `C3X_V10_DEMONSTRACAO_DRY_14s.wav` | **0 frames** | Sem clipping PCM; não prova harmônicos ou pressão física corretos |
| `C3X_V10_DEMONSTRACAO_PEDAL_14s.wav` | **0 frames** | Sem clipping PCM; não prova harmônicos ou pressão física corretos |
| `C3X_V10_DO4_DINAMICA_DRY_3_TOQUES.wav` | **0 frames** | Sem clipping PCM; não prova harmônicos ou pressão física corretos |

Não confundir ausência de clipping com qualidade auditiva. Em especial, a normalização isolada de arquivos dificulta comparação verdadeira de dinâmica e decaimento entre pianos; futuros testes devem preservar ganhos e geometria de captação controlados.

## 5. F1: o que falta antes de desenvolver outro motor

1. **Identificar a origem da referência C3X** (mesmo exemplar quando necessário), condições de afinação, tampa, sala, microfone, posição e calibração.
2. **Dó4 isolado:** gravar pp/mf/ff, sustain/soltura, mesmas posições e ganho; obter batimentos/inharmonicidade/decaimento de cada uma das cordas (quando possível).
3. **Mapear geometria e ação:** escala de cordas C4, massa de martelo efetiva, posição de impacto, curva de contato, histerese e velocidades físicas reais (não velocidade MIDI).
4. **Ponte e corpo:** medições de mobilidade com força conhecida, componentes transversal/longitudinal e parâmetros modais espaciais; gravações de pressão sincronizadas onde possível.
5. **Licenças comerciais:** comprovar uso de cada arquivo original (inclusive se houver calibração, derivação de parâmetros e distribuição), guardar hash e autorizações documentadas.
6. **Relatório de incerteza:** para cada parâmetro guardar unidade, origem, método de medição, intervalo de confiança e limitação; parâmetros desconhecidos permanecem explicitamente desconhecidos.
7. **Aceite explícito F1:** somente com dados minimamente suficientes para montar e validar Dó4 e com fontes legais/comerciais verificadas.

## 6. Estado e próximos passos

- **F0 concluída; F1 pendente**, etapas seguintes sem homologação.
- PR #44 permanece em **rascunho**, V10/11A–11C como pesquisas antecipadas.
- Nenhuma alteração do timbre público, nenhum DSP V11D novo e nenhuma declaração de Yamaha C3X reproduzido fielmente.
- Se não houver acesso a um C3X real, é possível estudar o método com parâmetros de outros instrumentos devidamente rotulados, **mas isso não conclui F1 para C3X**.

**Inventário auditável:** `research/c3x-physical/F1_INVENTARIO_PARAMETROS_C3X.csv`; o JSON fornece o estado e as fontes. Nenhum dataset externo foi importado no projeto nesta auditoria.
