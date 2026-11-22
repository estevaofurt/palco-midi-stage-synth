# Plano de fidelidade sonora dos pianos — após v1.9.5

**Data:** 22/11/2026  
**Status:** diagnóstico e planejamento técnico; **nenhuma alteração de áudio foi implementada neste documento**.

## Contexto e objetivo

O usuário confirmou que os estalos melhoraram **100% na v1.9.5**, inclusive no PC. A estabilidade atual é requisito de regressão, não algo que podemos sacrificar para melhorar o timbre.

O usuário também confirma que **Japanese Grand, American Grand, Felt e Upright ainda não se parecem com pianos reais**. Há capturas de referência `Japanese.wav`, `American.wav`, `Felt.wav` e `Upright.wav` (WAV estéreo 24-bit/44 kHz, mesma execução, aproximadamente 6m27s), com **efeitos originais dos instrumentos**. Não publicar/distribuir as capturas.

**Restrições obrigatórias:**
- Polifonia mínima **32 notas**, meta **64**, em PC e, na medida do possível, Moto g04s; medir no dispositivo real antes de declarar atingida.
- Motor próprio, **sem reproduzir diretamente samples das gravações**. O áudio serve para análise e comparação, não para embutir no site.
- Preservar a v1.9.5 funcional; próximas versões de DSP são **experimentais e isoladas**.
- Não reintroduzir o rack pesado de efeitos na inicialização; manter processamento sob demanda.
- Separar **timbre seco da fonte** e **acabamento de efeitos** para que reverberação não mascare falhas de ataque e sustentação.

## Diagnóstico verificado no código v1.9.5

Inspeção em `physical-piano.js`, `acoustic.js`, `fx-rack.js` e `CALIBRACAO_194.md`:

1. **Contato martelo–corda não é simulado dinamicamente.** A função `seedString()` coloca pulsos gaussianos pré-calculados nos buffers; `noteOn()` excita modos adicionais com amplitudes fixas. Falta força de contato variável com a compressão do feltro, velocidade e deslocamento relativo; martelo e corda não interagem durante a colisão.
2. **Calibração espectral é local a uma nota.** `profiles` define fatores extremos (`japanese.partials[1]=8.0`, `upright.partials[1]=4.6`) atenuados pela distância ao Dó4. Isso ajusta H2/H1 em uma janela, mas não garante a evolução do timbre em registros/velocidades distintos e pode resultar em parciais exagerados.
3. **Envelope artificial:** `v.transient` multiplica todos os componentes por uma curva rápida para reproduzir um declínio RMS medido em um trecho de apresentação. Em um piano real, parciais distintas e as cordas decaem de forma diversa; presença de pedal/efeitos nas referências torna o valor anterior inadequado como constante física.
4. **Ressonância limitada:** o tampo usa `BOARD` com 3, 5 ou 7 modos fixos (87–876 Hz), sem acoplamento bidirecional corda–ponte e sem representação adequada de radiação por registro, direção ou posição. A ressonância simpática é aproximada, não um sistema físico de cordas não percutidas.
5. **Vozes:** uma linha completa por nota em ECO, duas em outros perfis; efeitos de batimento são em grande parte aproximados por um ressonador. O conjunto produz som periódico, mas pode soar eletrônico.
6. **Testes de áudio ainda insuficientes:** verificam afinação, clipping, H2/H1 e quedas de nível em C4, não perceptualidade ou envelopes em várias teclas com forças diferentes. Não existe um protocolo de comparação cega com a referência sonora.
7. **Estabilidade melhorou por razões verificáveis** na v1.9.5: FX pesados sob demanda, eliminação de duplicações no caminho físico, processamento por bloco das vozes ativas. Manter esses avanços.

## Arquitetura recomendada — piano físico de baixa CPU

### Etapa 1 — Estabelecer uma medição correta

- Criar ferramenta de comparação offline entre WAVs (com efeitos originais) e áudio gerado (seco e processado), com nivelamento de loudness.
- Extrair características de **ataque (0–20, 20–80, 80–250 ms), espectros de parciais, inarmonicidade, evolução dos parciais, decaimento e release** em pelo menos cinco registros: A1/C2, C3, C4, C5, C6/C7.
- Capturas de performance polifônica não devem ser tratadas como notas isoladas sem confirmar a segmentação; não calcular rigidez/tempo de martelo a partir de um trecho contaminado.
- Reusar as referências atuais como **alvo musical final**. Capturas adicionais de notas isoladas e níveis de velocity conhecidos, com FX desligados, só se forem necessárias para calibração física.

### Etapa 2 — Novo martelo

- Implementar colisão com lei de força de contato do tipo `F = K·max(0,δ)^p`, com amortecimento e rebote, idealmente resolvidos por método numérico estável. `δ` é compressão relativa do feltro; ajustar `K` e `p` por registro, não inventar constantes exatas.
- Para celular, pré-calcular/cachear uma família curta de **excitações físicas sintéticas** por tecla e faixas de velocidade, interpolando no momento do note-on. *Não são samples gravados*; são respostas geradas matematicamente.
- Priorizar diferença real entre pianíssimo e fortíssimo, consistência do ataque e variação de espectro por velocity.

### Etapa 3 — Cordas, perdas e inarmonicidade

- Manter a linha de atraso eficiente com interpolação allpass, mas evoluir para perdas dependentes de frequência e dispersão calibradas por registro (especialmente graves e agudos).
- Modelo de 1/2/3 cordas acopladas por nota somente onde fizer sentido; **vozes de cauda podem reduzir complexidade** sem serem cortadas.
- Reduzir gradualmente os ganhos espectrais arbitrários conforme o modelo físico acertar o ataque e a evolução dos modos.

### Etapa 4 — Ponte, tampo e saída

- Implementar um modelo estéreo compartilhado de ponte/tampo com filtros modais e resposta variável por região/registro, preferencialmente com bancos de coeficientes pré-calculados.
- Separar radiação do tampo do reverb externo, e só depois recuperar o acabamento dos presets originais.
- Desenvolver ressonância simpática condicionada aos amortecedores e sustain, sem abrir 88 osciladores extras continuamente.
- Validar a compatibilidade mono da saída do celular.

### Etapa 5 — Identidade de cada piano e acabamento

- Japanese: grand mais brilhante e articulado no registro médio-agudo, sem segundo harmônico exagerado em todo o teclado.
- American: resposta do ataque, inarmonicidade e evolução harmônica próprias; não reduzir a diferença a um filtro passa-baixas.
- Felt: amortecimento do martelo por feltro e transiente suave, não apenas corte de agudos.
- Upright: conjunto de cordas, amortecimento e corpo característicos, não apenas menos reverb.
- Cada modelo terá parâmetros físicos próprios e processamento final separado, calibrados em mais de uma nota e intensidade.
- **Respeitar efeitos presentes nas capturas**, evitando interpretá-los como constantes de corda ou martelo.

## Desempenho: porta de aceitação obrigatória

- DSP num **AudioWorklet compartilhado**, com buffers prealocados e nenhuma alocação variável no callback.
- Em 48 kHz, cada bloco de 128 amostras dura **2,67 ms**: o trabalho de áudio de todos os módulos precisa terminar com margem adequada, também com 32/64 notas e sustain.
- Qualidade adaptativa **por voz**: notas recém-atacadas podem ter maior detalhe; caudas longas usam representação simplificada sem perder polifonia audível.
- Não reduzir polifonia abaixo de 32 para mascarar sobrecarga; se 64 não couberem no Moto g04s, expor o limite real e manter opção 32 sem estalos.
- Benchmark Node, navegador desktop e **Moto g04s físico**: renderização de notas únicas, acordes densos, pedais, troca de timbre e FX; inspecionar xrun/estalos percebidos, uso de CPU e memória.
- Regressionar v1.9.5 antes de promover qualquer novo DSP a padrão.

## Critérios para considerar uma nova versão melhor

1. Comparação A/B **nivelada** com a referência real em pelo menos graves, médios e agudos, com 3 faixas de dinâmica (baixo, médio, forte).
2. O ataque deixa de soar dedilhado, como sino ou órgão; o som possui evolução de harmônicos, ruído de martelo e decay plausíveis.
3. Os quatro modelos soam distintamente reconhecíveis sem depender de FX pesados.
4. Não há novos estalos, notas presas, clipping ou aumento de latência na sessão de testes.
5. O usuário confirma melhora auditiva **antes** de substituir a versão estável.

## Referências técnicas públicas

- Julius O. Smith, *Physical Audio Signal Processing*, capítulo de piano: https://www.dsprelated.com/freebooks/pasp/Piano_Synthesis.html
- Bank & Sujbert, *On the Nonlinear Commuted Synthesis of the Piano*: https://www.dafx.de/paper-archive/details/yL8RbflysbijGmR3zFXxGg
- *Physically informed signal processing methods for piano sound synthesis: a research overview*: https://research.unipd.it/handle/11577/2471599
- *Parameter fitting for piano sound synthesis by physical modeling*: https://pubmed.ncbi.nlm.nih.gov/16119368/

### Versão recomendada para próxima implementação

**v1.9.6 experimental: novo martelo com excitação física multivelocidade, sem alterar o rack FX estável, mais teste A/B em vários registros.** Fazer checkpoint de qualidade e CPU antes de avançar para a ponte/tampo.
