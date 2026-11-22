# Integração do acoplamento ao Novo Stage

## Ponto de partida confirmado

A última informação sobre o Novo Stage v1.11.0 descreve um tampo estéreo com duas zonas de excitação/escuta e um ataque dependente da tecla e da intensidade. **O código dessa versão não foi disponibilizado nesta sessão**; por isso esta integração é uma especificação executável de interface, não uma alteração no aplicativo.

## Onde o acoplamento deve ocorrer

No callback de áudio que já calcula as cordas e a ponte, para cada amostra:

1. A classe de cordas calcula os deslocamentos das linhas de atraso e sua velocidade na ponte.
2. Agrega-se a velocidade em duas regiões (grave/agudo), antes da equalização e dos efeitos.
3. Chama-se `body.step(bridgeL,bridgeR)` **uma vez por amostra de áudio**, nunca uma vez por nota.
4. A reação `body.reaction` é distribuída com ganho pequeno e limitado às linhas de atraso ativas, no próximo passo. Usar pesos e sinais consistentes com a orientação da ponte.
5. `body.wetL` e `body.wetR` são somados à saída seca em nível moderado, sem duplicar o reverb.

Esse projeto oferece um contrato mínimo em `CoupledPianoBus` para demonstrar o circuito. Ele não é um substituto direto da arquitetura da v1.11.0 porque **o gerador de cordas precisa aceitar reação externa**.

```js
// Exemplo conceitual dentro de um único processador AudioWorklet:
const bus = new CoupledPianoBus(waveguide,{sampleRate:48000,wetMix:.12,feedbackGain:.8});
// ...no process() do próprio AudioWorklet...
bus.render(outL,outR,outL.length);
```

## O que NÃO fazer

- Não criar um segundo `AudioWorkletNode` que alimenta seu sinal de volta na primeira entrada. Isso forma uma malha com atrasos de bloco e pode gerar estalos, realimentação instável e afinação inesperada.
- Não fechar o circuito com reverb, limiter ou master. A ponte deve receber a **reação do corpo**, não o áudio final processado.
- Não processar os 88 resonadores individualmente por cada voz. A ressonância é **compartilhada**.
- Não habilitar a nova malha por padrão antes de verificar o som seco, a afinação, o decaimento e a CPU no PC do usuário.

## Critérios de aceitação antes do merge

- 32 notas mínimas e meta 64, medidas no motor real com pedal, FX desligados e também com o rack completo.
- Teste de duas teclas: uma mantida pressionada silenciosamente e outra percutida deve excitar a primeira, se houver coincidência harmônica plausível.
- Tecla solta fecha o amortecedor e atenua a resposta; pedal mantém ressonância após note-off.
- Medir os desvios dos parciais (inharmonicidade B) e as taxas de decaimento por registro antes e depois: retorno da ponte não deve corrigir artificialmente falta de rigidez da corda.
- Checar saída mono; pedal/key noise baixo e opcional.
- Verificar consumo no Android Moto g04s e PC real. Sem novos estalos ou notas presas.
- Comparação com as quatro capturas reais deve distinguir fonte física seca dos efeitos originais preservados nas capturas.

## Próxima etapa específica

Assim que estiver disponível o módulo de síntese da v1.11.0, integrar `PianoResonanceBody.step()` no **mesmo AudioWorklet** do motor de cordas. O próximo bloco de desenvolvimento é a dispersão por rigidez (vários allpass ou modelo equivalente, calibrado por nota) e acoplamento entre cordas de uníssono; por enquanto este protótipo não mede nem corrige esses aspectos do realismo.
