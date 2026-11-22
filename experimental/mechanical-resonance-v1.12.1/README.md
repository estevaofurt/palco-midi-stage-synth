# Stage Synth — Acoplamento mecânico v1.12.1 (PROTÓTIPO)

**Estado:** protótipo original e independente, NÃO integrado ao Novo Stage v1.11.0. A v1.9.5 continua preservada. O código não é, por si só, um piano realista.

## Avanço sobre o protótipo anterior

O subsistema recebe a vibração *seca* da ponte (antes de reverb, EQ ou compressão), excita os modos compartilhados do tampo e das cordas abertas, **e agora calcula a reação mecânica da ponte**. Esse retorno pode entrar de volta na linha de atraso da corda, alterando sua evolução sonora. A classe `CoupledPianoBus` conecta ambos **dentro do mesmo callback de amostra**, evitando atrasos de 128 quadros entre AudioWorklets separados.

- 88 estados de teclas, com liberação dos abafadores, pedal CC64 e notas agudas sem abafadores.
- 176 ressonadores de cordas simpáticas, discretizados e processados a 1/4 da frequência (quando possível).
- 12 modos compartilhados de tampo harmônico estéreo; **não** um processador por nota.
- Modelo simplificado de impedância da ponte: retorno proporcional à velocidade calculada do tampo e à resposta simpática, limitado para manter estabilidade.
- Sem novas alocações por amostra no processamento do subsistema.
- Ruído mecânico opcional e discreto: o conjunto completo tecla/escapamento/martelo ainda não está modelado.

## Arquivos

- `piano-resonance.js` — estados, ressonadores e `step()` que expõe `wetL`, `wetR` e `reaction`.
- `coupled-piano-bus.js` — adaptador para ligar o processamento de cordas ao retorno mecânico **na mesma thread**. Espera de um motor de cordas com `sample()` e `pushBridge()`; não contém um piano completo.
- `piano-resonance-worklet.js` — legado: saída wet, **sem realimentação física**, para preservar os testes de integração anteriores.
- `tests/coupling.test.mjs` — testes novos de retorno mecânico, bypass, pedais e estabilidade.
- `tests/resonance.test.mjs`, `tests/performance.mjs` — regressão anterior e benchmark isolado.
- `tests/polyphony.test.mjs` — simulação de 32/64 loops de cordas simplificados, **não** vozes completas do Stage.
- `tests/performance-coupled.mjs` — mede o custo do acoplamento com 32/64 cordas de **teste**, excluindo a síntese do app.

## Fluxo correto para integrar no Novo Stage

```text
tecla / velocity / sustain
           │
           ▼
  martelo ─► cordas por waveguide
                  │ amostra por amostra
                  ▼
          ponte (velocidade)
                  │
                  ▼
    tampo + cordas simpáticas
           │            │
           ▼            └─► radiação wet estéreo
  reação de impedância
           │
           └─► devolve à corda no próximo sample
```

O loop só é bidirecional **se o motor principal realmente consumir `reaction`**. Não conectar o sinal wet ao áudio seco como se isso fosse feedback físico: seria apenas mistura/reverberação. O arquivo `piano-resonance-worklet.js` continua UNIDIRECIONAL. Para ativar o feedback dentro do aplicativo, a classe de cordas deverá fornecer `sample()` e `pushBridge()` ou expor mecanismo equivalente; o código-fonte do Novo Stage v1.11.0 não está disponível aqui, então essa integração ainda não foi aplicada.

## Testes

```bash
npm test
node tests/performance.mjs
node tests/performance-coupled.mjs
```

Requisitos para promover ao aplicativo: testes acústicos com notas isoladas e sem FX, comparação A/B com suas quatro capturas (que incluem efeitos originais), 32 vozes reais mínimas e 64 como meta, regressão de estalos e medida **no PC e Moto g04s**. Não confundir 64 teclas abertas na ressonância com renderizar 64 vozes completas do motor principal.

## Limitações e parâmetros

`bridgeLoad` determina o ganho do acoplamento simplificado e é limitado a 0–0,4. O valor atual NÃO corresponde à impedância medida de um piano. A dinâmica de martelos não lineares, a interação de uníssonos, a vibração do aro/estrutura, a geometria da ponte e o decaimento real do tampo ainda precisam ser identificados. Este módulo não contém reverb nem amostras gravadas de terceiros.
