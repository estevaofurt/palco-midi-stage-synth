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
