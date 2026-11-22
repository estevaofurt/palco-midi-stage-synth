# Japanese Grand — referência acústica Yamaha CFX

## Arquivo analisado

Referência fornecida pelo usuário: `Piano CFX - YAMAHA _ André Mehmari.mp3`, 48 kHz, estéreo, aproximadamente 3min58,64s.

**O arquivo original é apenas material de referência e NÃO está incluído no aplicativo, no GitHub ou no pacote de distribuição.** Não copiar amostras da execução para o motor.

## Observações extraídas do áudio (medidas, não transcrição)

Uma passagem predominantemente grave no início (3,6–5,4 s) apresenta forte energia abaixo de 180 Hz; na passagem de maior atividade entre 9–12 s, cresce substancialmente a energia relativa de 800–4.000 Hz. A imagem estéreo varia muito com a execução e com o ambiente. Há notas sobrepostas e longos decaimentos.

| Trecho | Banda 20–180 Hz / RMS | Banda 800–4.000 Hz / RMS | Correlação L/R |
|---|---:|---:|---:|
| 3,6–5,4 s (ataque grave) | 0,81 | 0,26 | 0,59 |
| 9–12 s (frase aguda/dinâmica) | 0,39 | 0,66 | 0,38 |

Essas proporções são energias RMS de sinais filtrados divididas pelo RMS da mistura mono do mesmo trecho. **Não são respostas isoladas de notas, nem medições dos parâmetros físicos das cordas:** incluem muitas notas, reverberação, microfones e possível processamento da gravação. Não utilizar esses valores como metas diretas de equalização.

## Correções em v1.9.3 experimental

- **Somente o Japanese Grand** foi recalibrado: o perfil American Grand, Felt e Upright permanece distinto.
- Contato efetivo do martelo dependente do registro e da intensidade: mais longo nos graves, mais curto nos agudos. O modelo anterior usava um contato aproximadamente uniforme, suprimindo excessivamente harmônicos acima de C6.
- Duas escalas de compressão do feltro no espectro da excitação: corpo do impacto e componente elástica rápida que recupera transientes agudos, sem samples.
- Fundamental mais robusto nos graves, distribuição de parciais revista nas oitavas superiores e ressonância do corpo com peso por registro.
- Mantidos DSP alocado antecipadamente, 32 vozes Econômico e 64 Estúdio. O corpo e o ataque seguem aproximações, não a reprodução exata do Yamaha CFX.

## Limites de comprovação

A referência é uma execução musical estéreo com sobreposição de notas. Para estimar curvas de inarmonicidade, contato do martelo e tempos de decaimento **por nota** com precisão, ainda são necessárias gravações de notas isoladas em diversas velocidades, preferencialmente sem reverb. Uma execução musical pode orientar caráter, ataque, articulação e registro, mas não determina sozinha coeficientes físicos.

Os testes Node e navegador simulado não substituem medição em um Moto g04s real: latência, temperatura, x-runs, estabilidade de 32 vozes e avaliação auditiva continuam pendentes.
