# Stage Synth — Verificação independente do diagnóstico da v1.9.6

**Data:** 22/11/2026  
**Escopo:** motor experimental `physical-v1.9.6` do Stage Synth. Nenhum motor de áudio foi substituído por esta revisão.

## Origem do diagnóstico

O usuário forneceu os seguintes quatro arquivos produzidos numa revisão externa: `DIAGNOSTICO_TIMBRE_v196.md`, `timbre_scorecard.py`, `piano_partials.py` e `render_notes.mjs`. Os três scripts foram reproduzidos na mesma estrutura de código local da v1.9.6. Seus resultados são úteis para encontrar erros específicos, mas **não são uma certificação acústica independente**: a implementação e os critérios foram elaborados na revisão externa e reaplicados aqui.

## Reprodução exata dos testes

Em Python com `numpy` e Node.js, sem qualquer alteração de DSP:

| Critério do scorecard recebido | `physical` | `modal` |
|---|---|---|
| Afinação fundamental (≤ 5 cents) | OK | OK |
| Inarmonicidade B (7 registros, comparada com faixa hipotética) | **FALHA: 0/7** | 7/7 |
| Centroide não diminui ao aumentar velocidade, teclas 28–72 | **FALHA: 3/5** | 5/5 |
| Harmônicos 3 e 4 não perdem nível relativo com velocidade, teclas 36–72 | **FALHA** | OK |
| Decaimento do fundamental com duas taxas | OK | OK |
| **Total** | **2/5** | **5/5** |

No Dó4, o motor físico passou de 521 Hz de centroide ao toque fraco para 493 Hz médio e 481 Hz forte; H3 mudou **−6,9 dB** e H4 **−9,9 dB** (forte contra fraco), de acordo com o código de medição recebido. Os resultados reproduzem o relatório externo.

Em um benchmark adicional **não comparável à execução real em tempo real** (Node, 48 kHz, 2 s renderizados, execução local única), o motor físico levou cerca de **201 ms** para 32 notas e **367 ms** para 64 notas; o modal levou **197 ms** para 32 notas. Esses números dependem muito da máquina e da otimização do JIT.

**Limitação importante:** `piano-worklet.js` declara `MAX_VOICES=32`. O modal *não* suporta 64 notas sem roubo de vozes na versão atual. Os 5/5 critérios não tornam o modal automaticamente melhor para o usuário, especialmente após relato de estalos em versões anteriores.

## Diagnóstico de código

- `physical-piano.js` usa uma seção allpass dispersiva de primeira ordem na realimentação; as parciais geradas pela linha de atraso são quase harmônicas. Os poucos modos adicionais em `modalY1/modalY2` possuem B configurado, mas são insuficientes para dominar todo o espectro. A necessidade de filtros de dispersão mais ricos está documentada na literatura.
- A excitação do martelo superpõe o estado de `seedString` com o kernel periódico de `seedHammer`, que é adicionado à linha em `noteOn`. A correlação com perda de brilho é forte no teste de ablação, mas **interferência de fase destrutiva ainda é hipótese**, não medição causal definitiva.
- O multiplicador `transient` é comum a todos os componentes da voz e impõe amortecimento global semelhante. Decaimento por parcial é mais realista; o motor já tem alguns modos separados, mas a linha principal não possui perdas espectrais adequadas.
- Os ganhos espectrais de `profiles.japanese.partials`, inclusive o peso **8,0** em H2 em torno do Dó4, foram ajustados sobre uma gravação de apresentação com efeitos originais. Isso tende a sobreajustar um ponto sem prever outras regiões/velocidades.

## Riscos metodológicos do scorecard

1. Os valores típicos de `BREF(k)` do script são funções de aproximação, **não medições do Japanese Grand do usuário**. A faixa ×/÷4 é deliberadamente ampla. Uma nota seca isolada pode ajudar a identificar o B verdadeiro; uma peça tocada com pedal/reverb não permite a mesma inferência.
2. O estimador de picos por FFT identifica máximos ao redor dos harmônicos esperados. Batimentos, sobreposição modal, ruído e parciais fracas podem enviesar a regressão de B. Validar em sinais sintéticos com B conhecido e em gravações isoladas.
3. A regra de que centroide e H3/H4 precisam crescer monotonicamente em todas as notas/velocidades é uma **heurística útil**, não uma lei universal de cada piano e nota (interferência e pontos de impacto podem alterar parciais específicas).
4. As notas renderizadas pelo scorecard ficam sustentadas por 8 s, **sem note-off**. Os T60 medidos são da sustentação, não do comportamento do abafador após soltar a tecla.
5. O benchmark de Node por si só não prova ausência de estalos em um AudioWorklet real, especialmente no Moto g04s.

## Decisão de engenharia

- **Não substituir automaticamente o motor físico pelo modal**, nem promover uma v1.9.7 só porque um motor passou no scorecard.
- Manter a **v1.9.5 estável** e a v1.9.6 isolada; incluir o scorecard como ferramenta reprodutível.
- Preparar duas linhas experimentais: (A) síntese modal calibrada a partir de parciais reais com otimização de 32→64 vozes; (B) guia de onda com dispersão por cascata de allpass e perdas frequenciais, sem superposição destrutiva de excitações.
- Comparar as duas com a mesma sequência MIDI, graves/médios/agudos, diferentes velocidades e custos de CPU. **Um scorecard de física, audição A/B com volume igualado e desempenho real precisam concordar** para promover uma versão.

## Próxima referência necessária (somente o Japanese inicialmente)

Se for possível, exportar **nove notas isoladas e secas**, sem reverb, delay, chorus, EQ/compressor ou pedal: C2 (MIDI 36), C4 (60) e C6 (84), com velocidades MIDI aproximadamente 32, 80 e 120. Manter cada tecla por cerca de 3–5 s e capturar pelo menos mais 2 s de cauda após note-off. Arquivo mono ou estéreo WAV sem normalização/clipping, nomeando tecla e velocidade. Se os efeitos não puderem ser desligados, documentar quais permanecem ativos — não tratar as medidas como constantes físicas.

Os WAV originais do usuário não são redistribuídos nem incluídos no repositório.

## Fontes públicas para a direção técnica

- Rauhala & Välimäki, *Dispersion Modeling in Waveguide Piano Synthesis Using Tunable Allpass Filters*: https://www.dafx.de/paper-archive/2006/papers/p_071.pdf
- Julius O. Smith, *Digital Waveguide Theory / Physical Audio Signal Processing*: https://www.dsprelated.com/freebooks/pasp/Digital_Waveguide_Theory.html
- Young, *Inharmonicity of Plain Wire Piano Strings* (JASA 1952): https://pubs.aip.org/asa/jasa/article-abstract/24/3/267/660100/Inharmonicity-of-Plain-Wire-Piano-Strings