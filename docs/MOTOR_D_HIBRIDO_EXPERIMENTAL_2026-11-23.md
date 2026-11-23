# Stage Synth v1.12.5 — D · Híbrido experimental

**Escopo autorizado em 23/11/2026:** gerar um motor com a pesquisa atual, preservando A/B/C e o módulo Piano Acústico. **Protótipo de engenharia, não piano acústico calibrado nem versão estável homologada.**

## Localização e composição

Em `Piano Acústico → Identidade e dinâmica → Motor do piano`, selecionar **D · Stage híbrido · experimental**. Clássico, A Claude modal, B histórico v1.9.5 e C Novo Stage mecânico continuam disponíveis; sem novos menus, botões ou categorias. Na página `index.html` e versão fixa `v1.12.5.html`, um único `acoustic.js` prepara o worklet `physical-piano-hybrid.js` sob demanda. Presets antigos continuam `soundEngine:'physical'` (C), e o usuário pode salvar `hybrid`.

## Componentes reais de implementação

| Subsistema | Código do D | Tipo de evidência / limite |
| --- | --- | --- |
| Martelo com feltro | `hybridContactTime(key,speed,hardness,character)`, duração limitada e redução de harmônicos pela transformada simplificada do contato; ruído de impacto curto por nota | **Hipótese físicamente informada**. Não é força medida de martelo nem modelo viscoelástico histerético validado |
| Cordas | Recorrências amortecidas por parcial, `n f0 sqrt((1+B n²)/(1+B))`, `hybridInharmonicity` crescente nos extremos, posição de batida como pente senoidal | **Parâmetros aproximados**, sem extração de B/parciais dos 15 AIFF Iowa |
| Uníssonos | Primeiros 3/4/5 parciais duplicados em rápidas e lentas caudas, pequena diferença de frequência por nota | **Aproximação de duas populações de modos**, não simulação completa de três cordas ou mobilidade cruzada H/V medida |
| Corpo, tampo e simpática | Instância única de `PianoResonanceBody`, já existente e original Stage; alimentada do sinal seco sintetizado de cada nota | **Ressonância modal/ponte aproximada**, não FRF Y_bridge 2×2 aferida; não há realimentação completa da resposta de ponte no modo de corda. Saídas de FX independentes |
| Ação/pedal | Ruído de impacto, CC64 global, `noteOff` sob pedal, abafamento após pedal solto, nota sem pedal termina, mensagens `param`, `send`, `stop` | **Aproximação discreta de pedal e ruído**; sem dinâmica física aferida do meio-pedal, una corda ou sostenuto |
| Perfis de custo | eco: **32 notas / 12 parciais**, balanced: **48 / 17**, studio: **64 / 23**; 3/4/5 pares, `MAX_MODES=32` por nota, matrizes prealocadas | **Limites de alocação, não prova de 32–64 vozes sem xruns em Android/Windows**. Uma parcial duplicada equivale a dois ressonadores e tem custo computacional extra |
| Proteção de saída | Compensação de ganho por quantidade de vozes e curva macia `0.96 tanh(x/0.96)` | Não substitui limitador final do Stage; escuta precisa confirmar que não existe bombeamento perceptível |

**Nota de origem:** nenhuma amostra externa, algoritmo de código AGPL/LGPL, tabelas numéricas ou parâmetros do Dussek/MF-1 foram incorporados ao produto. Os artigos científicos e os 65 arquivos de áudio originais de sete fontes são *fundamentação e potenciais futuras referências*. O D não foi ajustado, treinado nem comparado a esses arquivos nesta etapa.

## Testes planejados/executáveis

- `npm run check`: sintaxe e regressão Node pré-existente e testes novos `tests/hybrid_piano_v125.test.mjs`.
- Testes novos de seletor A/B/C/D, manutenção do default C e da seleção salva, cálculos de B e contato, sinal finito e diferente dos anteriores, dinâmica piano/forte, energia do martelo, 32/48/64 vozes sem roubo prematuro, pico abaixo do teto, CC64/panic e ciclo do AudioWorklet.
- `tests/measure_piano_engines.mjs` continua medindo **somente A/B/C**; não usar **108 cenários antigos** como se medissem o D. O D recebe testes próprios; métricas perceptivas secas comparáveis E1.0 permanecem para próxima etapa.
- `tests/browser_three_piano_engines_v124.py` foi atualizado para conferir seletor A/B/C/D (execução local de navegador depende de Playwright/Chromium, não incluída automaticamente no CI).
- GitHub Actions `piano-acoustic-baseline.yml` permanece o gate de regressão. A confirmação de CI e o hash de merge serão reportados separadamente após sua execução.

## Critérios mínimos antes de promover D

1. Ouvir D nas notas C2/C3/C4/C5/C6, a três dinâmicas e com FX desligado, confrontando Yamaha C5, Steinway B e Felt reais **sem confundir instrumento**.
2. Verificar ataque, sensação de corda dedilhada, construção de som de martelo, decaimento duplo, batimentos, pedestal de ruído e simpatia sob pedal. Ajustar somente mediante evidência perceptual/documentada.
3. Aferir **32 vozes em Moto g04s**, **64 em PC**, callback/CPU/xruns/latência e consumo de memória. O teste Node não é homologação.
4. Conferir calibração e direitos comerciais por R-GATE antes de atribuir fidelidade física a Steinway/Yamaha ou tornar D padrão. **R-GATEs atuais 0/7 plenamente aprovados**.

**Regra para próximos passos:** não alterar automaticamente A/B/C/MIDI/FX ou subir o D ao perfil padrão. A autorização expressa do titular em 23/11/2026 permitiu gerar **este** protótipo, não dispensou testes auditivos ou físicos.
