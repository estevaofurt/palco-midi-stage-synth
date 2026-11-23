# Stage Synth — E2.5: ajuste passivo da mobilidade da ponte com validação independente

**Data:** 23/11/2026. Pesquisa isolada na PR #37; Stage D público v1.12.8 permanece inalterado.

## Objetivo e implementação
Após a E2.4 separar mobilidade mecânica da ponte `Y(f)=v_ponte/F_ponte` de radiação acústica `H_pa(f)=p_microfone/a_ponte`, a E2.5 acrescenta um **ajustador de rede mecânica passiva**, `research/passive-bridge-mobility-fit.mjs`.

Cada modo candidato é um oscilador amortecido mecanicamente, com mobilidade positiva-real:
`Y_j(ω) = w_j · iω / (ω_j² − ω² + i·2ζ_j ω_jω)`, onde `w_j=1/m_j >= 0`, `ζ_j>0`. A parte real é não negativa em frequências positivas. Não se permite ajuste com pesos negativos, frequências inválidas ou damping negativo. A grade de frequências/amortecimentos precisa ser predefinida: o algoritmo ajusta **somente os pesos positivos**, com descida coordenada projetada. Isso NÃO identifica unicamente massas/rigidezes do tampo, porque as frequências, amortecimentos, posição e topologia ainda são hipóteses.

Para evitar ajuste excessivo, exigimos faixas disjuntas de **treino** e **validação**. O módulo devolve erros complexos separados nas duas faixas, a proveniência do dado e um indicador explícito `provenanceExternallyAudited:false`. Sinais sem bins válidos suficientes são rejeitados. Este estágio opera offline sobre `bridge-mobility-h1.mjs`; não está no caminho de áudio.

## Testes e resultado
`tests/passive_bridge_mobility_fit.test.mjs` introduz cinco testes **com dados matemáticos sintéticos determinísticos**:
1. Mobilidade positiva-real sem resistência negativa para modos com peso positivo.
2. Recuperação dos três pesos conhecidos em um conjunto artificial complexo.
3. Degradação detectada **apenas no conjunto retido**, sem alteração da perda do treino.
4. Configuração modal errada não consegue inventar peso negativo para maquiar o erro.
5. Rejeição de bandas sobrepostas, unidades incorretas e ausência de amostras válidas.

[GitHub Actions E2.5 — run 45200108448](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45200108448): **202/202 testes Node aprovados**, benchmarks anteriores e diff público de DSP/UI/FX/presets sem alterações.

## Limites e decisões
Os testes NÃO demonstram que o algoritmo consegue ajustar uma ponte real; isso dependerá da **mobilidade de ponto calibrada em SI** com força e velocidade medidas na própria ponte, medidas com coerência e permissão comercial verificáveis. O H1 de alta coerência não comprova automaticamente passividade nem explica todo o comportamento de um piano acústico. Dados sintéticos recuperados comprovam consistência do cálculo, não melhoria de piano.

**Próximo gate concreto:** obter mobilidade medida com calibração independente e direitos claros, identificar/resolver `Y(f)` no intervalo crítico dos graves e confrontar a predição com eventos retidos não usados no ajuste, incluindo decaimento. Depois disso calcular radiação medida em Pa, fazer A/B nivelado com o motor D e somente então testar áudio/browser em 32/48/64 vozes.

**Não promover candidato E2.5 a versão sonora.** Main preservada em v1.12.8. A/B/C/Clássico, MIDI/CC64, FX, UI, presets e histórico permanecem sem alterações. R-GATEs 0/7.
