# Referência sonora aprovada pelo usuário — Japanese Grand

## Fonte principal

Vídeo indicado pelo usuário como o som desejado para o **Japanese Grand** do Stage Synth:

https://www.youtube.com/watch?v=spBUgbBIoA0

**Status:** referência registrada em 22/11/2026. O áudio do vídeo ainda não pôde ser acessado ou analisado diretamente no ambiente de desenvolvimento; não afirmar que o timbre já foi reproduzido ou que o piano da gravação foi identificado.

## Objetivo

Desenvolver o timbre Japanese Grand com o motor **próprio de modelagem física**, sem copiar nem distribuir áudio do vídeo, bancos de amostras ou materiais protegidos.

Os parâmetros do motor devem ser calibrados com base em *áudio de referência acessível e autorizado*, não apenas em descrições subjetivas.

## Protocolo de calibração

1. Examinar a gravação de referência, identificando piano, captação, processamento e eventuais ruídos de fundo quando isso for verificável.
2. Escolher trechos com notas isoladas nos graves, médios e agudos e ataques de intensidades diferentes.
3. Comparar com o motor v1.9.2 em níveis igualados: forma espectral durante o ataque (0–100 ms), sustentação, decaimento de parciais, inarmonicidade, batimentos de cordas, release e ressonância simpática.
4. Separar o timbre do instrumento dos efeitos de gravação (reverb, equalização, compressão, microfonação).
5. Ajustar submodelos de contato martelo–corda, propagação e amortecimento de cordas, ponte/tampo harmônico e radiação sem reproduzir o sinal da gravação.
6. Realizar comparações A/B com um conjunto de notas e acordes, conferindo *qualidade auditiva*, estabilidade, afinação, envelope e custo computacional.
7. Homologar em um Moto g04s físico antes de tornar padrão.

## Critérios de desempenho

- **32 notas** de polifonia mínima em aparelhos de baixo desempenho, sem estalos de CPU ou áudio.
- **64 notas** como meta no perfil completo.
- Implementação eficiente num AudioWorklet compartilhado, priorizando memória alocada antecipadamente, sem alocações constantes no callback de áudio e sem regenerar efeitos por nota.
- Preservar as versões experimentais anteriores para comparação e reversão.

## Direitos de uso

Vídeo usado unicamente como referência de percepção e calibração; **não embutir, extrair ou redistribuir sua trilha sonora** sem os direitos pertinentes. Quando necessário, solicitar gravações separadas de notas isoladas fornecidas com autorização.

## Status de implementação

- [x] Referência registrada.
- [ ] Áudio de referência disponível para análise técnica.
- [ ] Características verificadas, medidas e documentadas.
- [ ] Motor retimbrado com comparação A/B.
- [ ] Testes reais no Moto g04s, 32 vozes e latência.
- [ ] Validação musical pelo usuário.
