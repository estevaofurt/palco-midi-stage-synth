# Stage Synth — E3.2 | Martelo reativo e auditoria de massa modal (modelagem física pura)

**23/11/2026** · pesquisa na PR #37, **DRAFT**, `main` v1.12.8 preservada. O titular rejeitou o timbre E3.0 como não sendo piano e exige **geração sonora 100% física**. Nenhuma gravação, SoundFont, resposta ao impulso gravada ou camada PCM entra na nova cadeia.

## Implementação estrutural — primeira interação realmente bidirecional

`research/reactive-felt-modal-piano-e32.mjs` conecta **um martelo de feltro não linear móvel** à rede das **88 teclas de corda** e aos **dois modos passivos compartilhados de ponte/tampo** da E2.3, mantendo a opção `externalForceMode:true` que impede o antigo pulso seno². O contato faz a corda receber a força modal positiva `f_j=w_j F` enquanto o martelo recebe a reação `−F`; portanto a energia do martelo de fato atravessa a interface mecânica, sem simular a aparência de impacto com envelope arbitrário.

A força vem de uma lei de compressão de feltro unilateral `U(δ)=k max(δ,0)^(p+1)/(p+1)`. Para cada passo, usando a **mesma ponte compartilhada**, calcula-se a posição livre da corda `q_free` e sua complacência `dq/dF`; a força escalar é encontrada por bisseção não negativa de um **gradiente discreto do potencial**. Assim `F (δ_novo − δ_antigo)=U_novo − U_antigo`: a perda de energia cinética do martelo é igual ao ganho de trabalho nas cordas e armazenamento do feltro, com dissipação mecânica positiva.

**Limitações assumidas:** este é um **único martelo** acoplado às 88 teclas permanentes, não 64 martelos em contato simultâneo. A solução é offline e usa uma predição O(n) com alocação de pequeno objeto por amostra, não uma implementação AudioWorklet validada. Os modos, suas forças projetadas, rigidezes, feltro e massas não estão identificados a partir de um piano real. A saída da placa E2.3 continua não calibrada em m/s/Pa. **Não é um novo timbre comercial.**

## Novo parâmetro de massa — hipótese física explícita, não preset de áudio

A E2.3 utilizava massas de coordenada da ordem de 1 kg (`m_j ~ 1 / n^1.1`) em graus modais de corda, o que era arbitrário e muito maior do que uma corda de aço individual.

O novo parâmetro **opcional e de pesquisa** `uniformModalMassKg`, com valor-padrão `null`, **preserva exatamente o comportamento histórico**; somente candidatos de laboratório substituem a massa arbitrária pela idealização de uma corda uniforme com modos senoidais `m_eff=ρ π r² L/2` (independente do número da parcial). Em `ReactiveFeltModalPiano`, a função `idealStringModalMassKg` aceita comprimento, raio e densidade; os números de teste para C3 são **L=0,85m, r=0,60mm, ρ=7850kg/m³**, produzindo `m_eff=0,00377321 kg`.

Esses parâmetros **não foram medidos** em C3 do piano de interesse; usar **a mesma massa para as 88 teclas é fisicamente inadequado** e serve apenas para controlar a hipótese e auditar estabilidade. Não confundir essa opção com 88 geometrias verificadas nem com calibragem comercial.

## Evidência numérica reproduzida (Dó3 MIDI48, 48 kHz, 0,38s)

[GitHub Actions E3.2 — run 45232683659](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45232683659) e `scripts/audit_reactive_felt_e32.mjs` (`e32-reactive-hammer-diagnostic.json` no artefato de CI). **252/252 testes Node aprovados**. Valores abaixo são do modelo ilustrativo; forças e transferências **não estão validadas contra instrumentos reais**.

| Configuração da corda/modal | 5ª parcial do painel relativa a H1 | Fração da energia inicial entregue a cordas/perdas | Contato acumulado |
|---|---:|---:|---:|
| Legacy, 5/2 parciais, martelo 2 m/s | −61,04 dB | 3,72% | 0,542 ms |
| Legacy, 8/8 parciais, 2 m/s | −59,68 dB | 4,11% | 0,542 ms |
| Geometria ilustrativa C3, 5/2, 2 m/s | **−94,04 dB** | **90,62%** | 1,188 ms |
| Geometria ilustrativa C3, 8/8, 2 m/s | −93,14 dB | 92,48% | 4,688 ms |

O martelo reativo responde à intensidade: com as massas legacy 1/2/3m/s, forças máximas generalizadas **52 / 136 / 238** e contato acumulado **0,708 / 0,542 / 0,458 ms**. O balanço `(E_total + perdas - E_inicial)/E_inicial` ficou em módulo da ordem de **10⁻¹⁴–10⁻¹³** nos seis cenários, preservando energia até o arredondamento de ponto flutuante.

**Interpretação essencial:** trocar massas aumentou drasticamente a transferência de energia, mas a radiação do único painel/superfície disponível **ficou muito mais pobre em harmônicos superiores**. Portanto, **não promoveu fidelidade acústica**. Adicionar 8/8 parciais tampouco recupera o quinto harmônico radiado em magnitude plausível. O perfil 8/8 com massa de geometria tem múltiplos contatos/recontatos totalizando ~4,69 ms; isso requer investigação, não propaganda de realismo.

`tests/reactive_felt_modal_piano_e32.test.mjs` testa força/reação recíproca, predição da complacência da ponte, gradiente discreto de energia, velocidade, contato nulo, CC64/damper, 44,1/48/96 kHz, 8/8 parciais e massa derivada de geometria. `scripts/audit_reactive_felt_e32.mjs` gera somente métricas/sinal da simulação. **Nenhum WAV de piano externo é carregado.**

## Gate do produto e próximos passos

1. **Não repetir E3.0 como 'piano melhorado'**. O novo contato demonstra melhor conservação física, mas os graves/médios ainda não têm espectro acústico convincente.
2. **E3.3:** identificar rigidez do feltro, ponto de impacto e massa efetiva de cada corda real/funcional; corda rígida dispersiva, perdas dependentes da frequência e uníssono real com acoplamentos físicos (não escolha de harmônicos baseada só em equalização).
3. **E3.4:** substituir ponte/tampo de apenas dois graus por **modos espaciais acoplados fisicamente**, aplicando força ao longo da linha da ponte e radiando **somente a área do tampo**, sem disfarçar `bridgeVelocity` de superfície. Investigar cargas acústicas de retorno e convergência.
4. **E3.5:** resolver múltiplos martelos simultaneamente conservando a reação de cada tecla; somente depois avaliar 32–64 notas de polifonia no Worklet/PC/Android com CPU, memória, aliasing e CC64 reais.
5. Validar por **escuta** e comparação harmônica/decaimento com WAVs externos usados exclusivamente como **referência diagnóstica**, não como entrada de áudio do motor.

A PR #37 continua **DRAFT**, R-GATEs comerciais **0/7**. Todo o DSP público, UI, preset, FX e MIDI da `main` v1.12.8 permanece intocado. **Nenhum WAV novo é promovido como piano** nesta etapa, pois a falha tonal foi objetiva e permanece sem solução.
