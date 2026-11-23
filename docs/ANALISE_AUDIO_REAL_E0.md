# Stage Synth E0 — análise experimental de áudio real (Steinway Model B)

**Base:** Stage Synth main v1.12.4, commit 73ce2f0507365adec93d1b5d5d83c549a344817e.  
**Natureza:** pipeline de pesquisa separado. **Não modifica DSP, interface, módulos, presets, MIDI, FX ou samples do app**.

## Fontes e direitos
- Universidade de Iowa, Steinway Model B, gravado em 2001, 16 bit / 44,1 kHz estéreo, *não anecoico*; pp, mf, ff musicais: https://theremin.music.uiowa.edu/MISpiano.html .
- Declaração de permissão para uso de projetos pela própria universidade: https://theremin.music.uiowa.edu/MIS.html .
- Cópia espelho de origem declarada, usada somente se o servidor Iowa falhar: https://huggingface.co/datasets/sondalex/university-iowa-piano-samples (conferir hash e proveniência).
- Áudio original **não** é versionado no GitHub, não vai para o app, não é incorporado ao artifact. Apenas metadados e resultados derivados do sinal (não reversíveis em samples).

## Execução e desenho
1. Workflow .github/workflows/piano-real-reference-e0.yml executa sob branch experimental por push.
2. script scripts/fetch_iowa_reference.py transfere nota por nota para **/tmp** do próprio runner; mede SHA-256 e tamanho, valida cabeçalho AIFF e usa ffprobe/ffmpeg para decodificar a 48 kHz mono float32.
3. script scripts/analyze_reference_audio.mjs detecta início da nota, recorta 1,7 s do ataque, mede FFT/inharmonicidade estimada/parciais/envelopes com testes/piano_acoustic_metrics.mjs e renderiza os motores A/B/C em configuração de referência.
4. E0 compara **forma espectral relativa por parcial**, não nível absoluto e não é classificação de realismo. O Stage usa velocidade interna 80/127 somente como experimento; as inscrições pp/mf/ff do piano real não são velocímetros MIDI calibrados.
5. Only e0-report.json é disponibilizado para auditoria (por 14 dias), inclusive URLs e SHA-256 da origem. Remoção obrigatória de todos os arquivos de áudio no fim do workflow.
6. Seleção controlada por env STAGE_PIANO_SELECTION. Piloto C4:mf, depois C2/C4/C6 × pp/mf/ff, verificando a integridade do primeiro resultado.

## Critérios para relatório
- Fonte aceita somente se download íntegro, cabeçalho AIFF válido, arquivo no limite estipulado e decodificação válida.
- O relatório registra posição aproximada do ataque, afinação espectral, intensidade RMS local, razões harmônicas, B aproximado, envelopes e contrastes.
- Filtros espectrais do piano gravado/posição dos microfones são diferenças reais de observação, não necessariamente falhas do Stage.
- **Não** comparar volume absoluto entre instrumentos; o arquivo Iowa preserva níveis de gravação, e a curva das velocities do Stage ainda não foi calibrada.
- O decaimento tardio do Steinway contém também a resposta da sala.
- Se o número de parciais confiáveis for insuficiente, registrar B como ausente em vez de inventar uma constante.
- Dados sintetizados A/B/C devem continuar passando 32/64 vozes e sem estalos (último requisito somente testável em hardware).

## Gatilhos para expansão
Após piloto de Iowa validado por log e SHA, executar 9 arquivos C2/C4/C6 × pp/mf/ff. Na sequência, usar Yamaha C5 Salamander (16 layers), Kawai Upright KW (2 layers com loops graves) e Fuchs & Möhr Felt (3 layers, disponibilidade de download condicionada ao site). Para Yamaha CFX, manter demos apenas como referência de audição até encontrar dados brutos isolados licenciados.

**Status inicial:** script/testes adicionados à branch; diagnóstico com áudio externo precisa de execução verificada no Actions. Não confundir sucesso do teste com validação perceptiva.

## Resultados E0 verificados no GitHub Actions (23/11/2026 UTC)

### 9 arquivos originais AIFF — Steinway B / University of Iowa
**Workflow:** https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45096510022 (94/94 testes Node passaram; 9 downloads íntegros e 9 medições concluídas).
Todos os 9 originais foram baixados do domínio da universidade; SHA-256 por arquivo disponível no log e no artifact de medições; áudio **não** foi publicado.

| Nota, intensidade musical | B estimado da referência | parciais B estimado | diferença relativa espectral A/B/C (dB) | parciais comparados |
|---|---:|---:|---|---:|
| C2 pp | 0.000203 | 7 | 18.34 / 39.79 / 39.78 | 7 |
| C2 mf | 0.000484 | 7 | 16.95 / 38.28 / 38.28 | 7 |
| C2 ff | 0.000478 | 7 | 17.23 / 38.60 / 38.60 | 7 |
| C4 pp | inconclusivo | 1 | não comparável | 1 |
| C4 mf | 0.000396 | 6 | 9.06 / 15.01 / 15.01 | 6 |
| C4 ff | 0.000367 | 6 | 9.77 / 14.04 / 14.04 | 6 |
| C6 pp | inconclusivo | 1 | não comparável | 1 |
| C6 mf | inconclusivo | 1 | não comparável | 0 |
| C6 ff | inconclusivo | 1 | não comparável | 1 |

A referência C2/C4 indica dispersão mais elevada que a medida anteriormente no motor B/C em algumas regiões. **Não usar isso como alvo único de B para outros pianos**; valores de B variam por nota e instrumento, e a FFT com parciais sobrepostos envolve incerteza. A diferença de ~38 dB nos graves B/C é apenas entre amplitudes relativas dos modos selecionados; não substitui comparação perceptiva.

### 15 compactados AAC — Yamaha C5 e Upright Knight / StaPiano

**Workflow com arquivos compactos:** https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45096722930 (9 + 15 arquivos, áudio na pasta temporária e resumos JSON somente).
Origem técnica da codificação: https://github.com/StanislavMakhnytskyi/stapiano-samples
Yamaha C5 é Salamander real gravado por Alexander Holm, **4 das 16 camadas** originais em subset mono AAC 96kbps, CC BY 3.0 (obrigatória atribuição). Upright é **Knight**, da VCSL/Simon Dalzell, CC0 1.0; **não confundir** com o Kawai KW listado em docs anteriores.

| Referência | Camada do subset | delta A/B/C (dB) | parciais comparáveis |
|---|---|---|---|
| Yamaha C5 C2 (MIDI36) | v4 (forte) | 7.78 / 24.58 / 24.58 | 7 |
| Yamaha C5 C4 (MIDI60) | v1 (suave) | 8.99 / 13.59 / 13.58 | 6 |
| Yamaha C5 C4 (MIDI60) | v3 | 11.58 / 20.58 / 20.59 | 7 |
| Yamaha C5 C4 (MIDI60) | v4 (forte) | 11.94 / 20.92 / 20.93 | 7 |
| Knight Upright C#2 (MIDI37) | v2 | 27.81 / 49.30 / 49.28 | 7 |
| Knight Upright C#4 (MIDI61) | v1 | 10.59 / 6.46 / 6.47 | 3 (limítrofe) |
| Knight Upright C#4 (MIDI61) | v2 | 7.10 / 21.66 / 21.71 | 6 |

**C6 Yamaha e C#6 Upright:** grande parte dos resultados tem somente 1 ou 2 parciais úteis. O analisador foi corrigido para registrar estimativa de B e comparação espectral como **inconclusivas** nesses casos. Não fornecer ranking de timbre com essas observações. AAC, cortes, fade e posicionamento do microfone introduzem limitações adicionais.

### Interpretação e próximo método

1. São **duas coleções distintas**: a mais adequada para estimar aspectos da vibração é a original AIFF da Iowa; os AAC compactados servem sobretudo para triagem perceptual/forma espectral. Para Yamaha e Upright, obter WAVs/FLACs sem perda e inspecionar SFZ antes de inferir física de rigidez, contato e T60.
2. A maior diferença consistente de timbre calculado no Stage B/C está nos graves. **Hipótese prioritária:** verificar se excitação, amplitude, amortecimento e coerência dos primeiros oito parciais diferem por registro; não corrigir indiscriminadamente com ganho elevado de H2.
3. O A modal (adaptado do Claude) aproximou melhor a distribuição de alguns harmônicos graves, mas não está comprovado como o instrumento sonoro mais realista; a energia do tampo, acoplamento e ruídos ainda precisam de escuta nivelada.
4. Relacionar velocity física real às camadas. Na versão inicial, A/B/C são renderizados todos em speed 80/127 contra qualquer pp/mf/ff/layer; isso **impede conclusão sobre curvas dinâmicas** até calibração.
5. Usar análise temporal por múltiplas janelas para separar parciais vizinhos e batimentos. F0 afinado com stretch é natural; comparar somente contra frequências do próprio instrumento, não ET puro.
6. Felt (Fuchs & Möhr): pesquisar conjunto WAV domínio público original no Hugging Face CueHarbor; acesso e mapa de notas devem ser verificados antes de declarar qualquer medição.

### Proteção da estabilidade
**Nenhuma alteração no DSP A/B/C**, interface, presets, MIDI ou FX; nenhum banco externo ou gravação pessoal foi adicionado ao repo; nenhum motor experimental foi promovido. O PR #2 de dispersão continua isolado. A meta de 32–64 notas permanece sujeita a áudio real em PC/Moto g04s.
