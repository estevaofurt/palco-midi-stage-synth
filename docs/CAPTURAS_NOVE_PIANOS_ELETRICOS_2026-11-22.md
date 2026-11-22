# Stage Synth — análise das 9 capturas de pianos elétricos

Data: 22/11/2026. Fonte: nove arquivos WAV fornecidos pelo usuário, preservados localmente e **não incluídos** neste relatório ou no GitHub.

## Condições de captura verificadas
- Todos os nove arquivos têm **6 min 26,911 s**, são **WAV PCM 24 bits estéreo, 44.000 Hz**.
- O primeiro áudio ultrapassa amplitude 0,001 por volta de **1,23 s** em todos os arquivos: forte indicação de apresentação sincronizada, útil para comparação A/B.
- **Não há clipping digital** no critério de amostras acima de 0,999999 de amplitude.
- Os canais L e R são **idênticos** em Wurly 140B, Wurly 200A e Clavinet nos trechos verificados (dupla-mono); outros têm estéreo variável.
- A configuração de efeitos internos e as velocidades MIDI **não estão documentadas**; as capturas podem conter o som final processado, não apenas a fonte física.

## Métricas gerais

| Captura | Pico | RMS global (dBFS) | Correlação L/R | 2º harmônico (dB) em trecho de Dó4 |
|---|---:|---:|---:|---:|
| Rhodes MK I | 0.722 | -25.5 | +0.70 | +9.9 |
| Rhodes MK II | 0.920 | -26.7 | +0.77 | -0.1 |
| Wurly 200a | 0.567 | -29.6 | +1.00 | -4.9 |
| Wurly 140b | 0.664 | -25.4 | +1.00 | +2.7 |
| CP70 | 0.727 | -27.5 | +0.82 | -0.7 |
| Clavinet | 0.397 | -37.9 | +1.00 | +4.7 |
| E. Piano 1 | 0.738 | -26.2 | +0.58 | +6.3 |
| E. Piano 2 | 0.667 | -26.0 | +0.92 | +0.9 |
| E. Piano 3 | 0.622 | -24.4 | +0.58 | -3.0 |

**Atenção aos harmônicos:** o valor é uma leitura local de espectro ao redor de **82,67 s**, em uma passagem que contém frequência próxima ao Dó4 (261,6 Hz). O valor mede o segundo múltiplo em relação ao fundamental, e não a identidade timbral do instrumento em todo o teclado. A presença de outras notas, release e efeitos pode alterar a estimativa.

## Diferenças relevantes para novos modelos
- **Rhodes MK I vs MK II:** o MK I mostra 2º harmônico muito mais destacado nesse trecho (+9,9 dB vs −0,1 dB), apesar de ambos pertencerem à família de pianos eletromecânicos de lâminas (tines). Não reduzir essa diferença a um controle de brilho global; a resposta da captação e a evolução dos modos precisam ser próprias por modelo.
- **Wurly 140B vs 200A:** 140B +2,7 dB e 200A −4,9 dB no mesmo trecho. Modelar a palheta/reed e a captação, com saturação dependente da intensidade da tecla; considerar amplificador como camada distinta.
- **Clavinet:** no trecho, segundo e terceiro harmônicos maiores que o fundamental (+4,7 e +4,6 dB). Exige um modelo de corda percutida, captação e abafamento que não seja o Rhodes com outro filtro.
- **CP70:** registrado como CP70. O app atual oferece CP80; são modelos diferentes. Manter CP80 e adicionar CP70 como identidade separada antes de atribuir este arquivo a um preset.
- **E. Piano 1, 2 e 3:** espectros distintos; **não atribuir automaticamente** às opções FM Full Tines/Dino EP/Ballad Key, pois os nomes dos arquivos não identificam esses presets com segurança.

## Riscos de calibração
1. **Níveis diferentes:** Clavinet apresenta RMS global muito mais baixo que vários outros. Sempre igualar volumes para testes A/B de caráter sonoro; não aumentar o ganho do motor apenas para “parecer mais realista”.
2. **Dupla-mono vs estéreo:** evitar cancelar canais, somar sinal mono duas vezes ou embutir estéreo artificial no modelo físico; espacialização e efeitos devem atuar na etapa de acabamento quando necessários.
3. **Gravações musicais:** harmonias simultâneas e efeitos podem mascarar harmônicos isolados. Antes de ajustar a rigidez de uma palheta/corda, comparar vários ataques e regiões do teclado e, quando possível, usar notas isoladas.
4. **Performance móvel:** modelos econômicos devem garantir pelo menos 32 notas de polifonia, com 64 como meta; medir a carga em Moto g04s real e evitar dezenas de AudioNodes independentes por nota.

## Plano de implementação no Stage Synth
1. Preservar a v1.9.4 e o motor elétrico existente como referência/fallback.
2. Desenvolver **núcleo DSP compartilhado (um AudioWorklet)** e famílias físicas/eletromecânicas separadas: tines Rhodes, reeds Wurly, cordas Clavinet e piano eletroacústico CP70.
3. Introduzir modos moduladores específicos para as três capturas E. Piano após identificar as fontes/presets correspondentes.
4. Parametrizar ataque, inarmonicidade, evolução de parciais, decaimento, pickup e saturação dependente da dinâmica e do modelo.
5. Separar “motor seco” dos efeitos de amplificação, microfonação, tremolo e auto-pan já existentes, com mudanças audíveis em tempo real.
6. Gerar comparação A/B com sequências MIDI idênticas e mesmo nível, usando capturas fornecidas apenas localmente para análise.
7. Revalidar 32/64 notas, CPU, memória, pico de áudio, mono e desempenho Android físico antes de definir timbre padrão.

### Situação
Capturas recebidas, integridade verificada e perfis iniciais medidos. **A calibração/reescrita do motor de pianos elétricos ainda não foi implementada nesta etapa.**
Os arquivos de áudio não serão publicados no repositório público sem autorização explícita e confirmação dos direitos de redistribuição.