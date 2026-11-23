# Stage Synth E3.4 — ataque percussivo físico do martelo, testes A/B e limitação acústica

**23/11/2026 — pesquisa isolada (PR #37, draft).** O titular percebeu a falta de **dureza, definição e pequena percussão do impacto do martelo**. Essa avaliação complementa a rejeição anterior do timbre E3.0. A síntese continua **100% por modelagem física**: nenhum WAV de piano, camada de ruído de tecla, impacto gravado, SoundFont, EQ de correção ou IR de convolução entra no motor.

## Problema e hipótese

O E3.3 já tinha martelo móvel e contato reativo, mas seu feltro usava apenas `U(δ)=k·δ₊^(p+1)/(p+1)`, com dureza global fixa. O tampo possuía apenas **oito modos de vibração**, com frequências ilustrativas até **610 Hz**. Por isso não bastava aumentar volume ou reverberação: o impacto físico e a transmissão do seu conteúdo transitório não estavam suficientemente representados.

## E3.4 — duas mudanças físicas opcionais

1. **Núcleo de feltro que endurece ao comprimir:** `ReactiveFeltDistributedPianoE33` ganha `feltHardeningRatio` (default `0`, preserva a E3.3) e `feltHardeningThresholdM` (default `0.00016`). O potencial adicional é
   `U_core(δ)=k·ratio·max(δ−δ_core,0)^(p+1)/(p+1)`.
   A força física é sua derivada; o **gradiente discreto do potencial** na solução implícita mantém a conservação de energia com reação do martelo e cordas. Não há mistura de sinal de clique.
2. **16 modos espaciais opcionais do tampo:** `PassiveDistributedSoundboardE33` aceita `panelModes=16`, mantendo `8` por padrão. Aumenta a ordem da mecânica distribuída (modos 9–16 com índices espaciais de uma placa idealizada). As novas frequências vêm de uma relação `f ∝ m²/L²+n²/W²` ancorada em 95 Hz, válida apenas para uma placa ideal de contorno simplificado. `AnalyticSpatialPlateRadiatorE33` agora admite essas **16 velocidades físicas de placa** na integral de Rayleigh. Não são 16 equalizadores nem 16 amostras.

A hipótese é plausível fisicamente, mas as massas, rigidez, densidade, geometria, condições de contorno e força de feltro **não estão calibradas com medidas de um piano específico**. A opção `feltHardeningRatio=12` é um valor forte para diagnóstico, **não uma configuração comercial recomendada**.

## Resultado mensurável: melhora do contato ≠ timbre convincente

[CI experimental 45240292197](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45240292197): **279/279 testes Node aprovados**, 0 falhas, baseline Stage v1.12.8 também verde. Comparação controlada **C3, velocidade inicial de martelo 2,8 m/s**, 48 kHz:

| Medida | Feltro antigo, 8 modos | Feltro com núcleo, 8 modos |
|---|---:|---:|
| Pico de força generalizada de contato | 216,69 | 430,37 |
| Tempo acumulado de contato | 0,479 ms | 0,354 ms |
| Relação RMS ataque (8–65 ms) / corpo (140–380 ms) | +4,471 dB | +4,498 dB |
| Alteração ataque/corpo | — | **+0,027 dB** |

O impacto **ficou mecanicamente mais curto e aproximadamente duas vezes mais forte**, como esperado. Entretanto, a diferença acústica relativa `+0,027 dB` foi **minúscula**. Repetindo com **16 modos**, a relação ficou aproximadamente `4,468→4,496 dB`: também insignificante. Isso confirma que **endurecer o feltro não resolve sozinho a falta de percussão na saída do painel**. O acoplamento físico da linha da ponte aos modos superiores do tampo permanece um gargalo.

As verificações de energia da E3.4 apresentaram erros da ordem de `10^-14` no balanço `E_final + dissipação − E_inicial`, e os modos 9–16 foram efetivamente excitados. Isso valida propriedades do solver, **não timbre de piano**. A renderização usou o mesmo ganho para os quatro arquivos, preservando diferenças reais de amplitude. Também foram aplicados fades de edição iguais para evitar que cortes artificiais criassem falsos estalos de martelo.

## WAVs experimentais disponíveis

`scripts/render_percussive_felt_e34.mjs` produz notas **Dó3 suave/forte e Dó4 suave/forte**, sequenciais e reinicializadas em cada tomada, em WAV estéreo PCM16 de 48 kHz:
- `e34_8mode_felt_normal.wav`
- `e34_8mode_felt_core.wav`
- `e34_16mode_felt_normal.wav`
- `e34_16mode_felt_core.wav`
- `e34_AB_8panel_normal_then_compressed_felt.wav`
- `e34_AB_16panel_normal_then_compressed_felt.wav`

No A/B, primeiro toca a configuração original; depois a de feltro comprimido. A amplitude é mantida por ganho comum **não equiparado em loudness**. Os arquivos e o diagnóstico `e34_percussive_hammer_report.json` são gerados pelo GitHub Actions, sem utilizar gravações do usuário e sem adicionar WAVs ao repositório.

## Decisão e próximos critérios

- **Não integrar ao motor D público** como se o realismo estivesse aprovado; a PR #37 continua draft e a v1.12.8 (A/B/C/D/Clássico, MIDI, presets e FX) permanece intocada.
- **Próximo passo E3.5:** rever massas e impedâncias de ponte/tampo, *linha espacial de excitação* da ponte, rigidez e dispersão das cordas e **densidade de modos acima de 1 kHz**. O gargalo principal é transferir e irradiar o ataque existente — não gerar clique com ruído artificial.
- Comparar C2/C3/C4/C5 nos primeiros 10–80 ms, espectro até pelo menos 5 kHz e decaimento em 0,1–2 s. Gravações externas poderão auxiliar **somente como referências de diagnóstico**, nunca ser reproduzidas na síntese.
- Confirmar as diferenças por **escuta do titular**. 32–64 martelos simultâneos com tampo distribuído e radiação real ainda não foram validados em navegador/AudioWorklet.
- R-GATEs comerciais **0/7**.

**Conclusão:** a observação do titular é tecnicamente consistente. A E3.4 criou um contato fisicamente mais percussivo, mas o tampo/ponte ainda não o transforma em uma batida de piano convincente. O resultado não deve ser promovido por pressão de testes numéricos.
