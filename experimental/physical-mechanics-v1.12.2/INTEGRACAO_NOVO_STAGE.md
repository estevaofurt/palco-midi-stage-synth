# Ponte para o Novo Stage v1.11

Este diretório é uma versão **executável experimental baseada na v1.9.5**, não o código-fonte do Novo Stage v1.11.0.

### API e local de acoplamento

O motor `PhysicalPianoEngine` instancia `PianoResonanceBody` no mesmo callback de processamento. Toda amostra:

1. Cada waveguide calcula a vibração da corda e recebe **a reação mecânica limitada do passo anterior**.
2. As saídas secas são agregadas como velocidade na ponte, sem somar áudio de reverb externo.
3. `PianoResonanceBody.step(bridgeVelocity)` avança ressonadores de tampo e cordas simpáticas, influenciados por teclas/pedal.
4. A componente estéreo da ressonância substitui gradualmente os modos antigos do corpo, com crossfade para o modo anterior.
5. A reação da ponte é limitada a ±0.055 antes de ser distribuída às vozes, ponderada pela quantidade de notas.

### Interfaces MIDI

`noteOn({id,key,speed})`, `noteOff(id)`, `setSustain(CC64)` e `stopAll()` coordenam o estado dos abafadores. Duplicatas da mesma nota são contadas; soltar uma delas não silencia a ressonância da outra.

### Para portar à v1.11

1. Recuperar/identificar a fonte atual daquela linha, incluindo seu processor e teste A/B com Claude.
2. Localizar o callback que calcula o sinal de ponte **antes** do tampo e do reverb.
3. Incorporar a reação em seu modelo de propagação, sem encadear dois AudioWorklets e sem adicionar um segundo tampo.
4. Migrar a máquina de estados de CC64, teclas repetidas e nota-off.
5. Reexecutar benchmark, regressão MIDI e comparação auditiva contra as quatro capturas; não promover se houver estalos.

**Pontos ainda em aberto:** inarmonicidade, perdas espectrais realistas, modelagem detalhada do martelo, parâmetros medidos de notas secas e validação no hardware físico.
