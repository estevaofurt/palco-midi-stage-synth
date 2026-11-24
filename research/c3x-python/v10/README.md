# STAGE SYNTH C3X — Etapa 10: mecânica contínua

**Protótipo experimental V10 para síntese física offline de piano, sem samples como fonte sonora e sem reverberação de sala.** A referência pretendida é um Yamaha C3X, mas as propriedades internas da ação **não são medidas reais desse modelo**. A V1 aprovada e a V9 foram preservadas em `referencias/`, com SHA-256.

## O que mudou

- `stage_synth_c3x/continuous_action.py`: a cada 0,5 ms acompanha a profundidade comandada e a posição simulada da tecla; detecta passagem pelo escapamento, voo livre do martelo, captura/backcheck simplificado e condições de rearme do mecanismo.
- `stage_synth_c3x/continuous_engine.py`: transforma colisões em excitação física **das mesmas cordas compartilhadas** da V9 e conserva o caminho sonoro da V9/V8. Não contém fonte WAV/sample nem reverberação de sala.
- Eventos opcionais de profundidade permitem testar pressões parciais e retrigger sem soltura total.
- `bypass_continuous=True` delega à V9 para comparar o som antigo exatamente.

**Cuidado:** não é um modelo multibody completo de jack, wippen, mola e alavanca de repetição. O reset e a captura são regras reduzidas; as velocidades e limiares são estimativas de pesquisa. O amortecimento devido ao movimento parcial da tecla também continua aproximado.

## Como executar

Requer Python 3.11 ou mais recente e ambiente com NumPy, SciPy, SoundFile e Numba. No diretório raiz da V10:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s testes -p 'test_*.py' -v
python gerar_etapa_10.py
python auditoria_88_v10.py
```

Para MIDI convencional (início, nota, duração pressionada, velocidade):

```python
import soundfile as sf
from stage_synth_c3x.continuous_engine import render_sequence_v10_action
from stage_synth_c3x.engine import SR

wav = render_sequence_v10_action([
    (0.10, 60, 0.40, 82),
    (0.65, 64, 0.35, 90),
    (1.10, 67, 0.50, 98),
], length=2.0)
sf.write('piano_dry_v10.wav', wav, SR, subtype='PCM_16')
```

Para a ação física opcional, envie *keyframes* `(tempo, MIDI, profundidade 0..1, velocidade de descida MIDI 1..127)`. Use velocidade zero nos movimentos ascendentes:

```python
keys = [
    (0.02, 69, 1.00, 90),
    (0.12, 69, 0.45, 0),
    (0.16, 69, 1.00, 99),
    (0.26, 69, 0.45, 0),
    (0.30, 69, 1.00, 105),
    (0.40, 69, 0.00, 0),
]
wav, info = render_sequence_v10_action(
    (), length=1.05, keyframes=keys, action_mode='double',
    return_diagnostics=True)
print(info['strike_count'])  # 3 golpes neste ensaio de dupla repetição
```

## Áudios novos

- `audios/C3X_V10_DRY_acao_continua_7s.wav`: execução musical com a V10.
- `audios/C3X_AB_V9_vs_V10_DRY_15s.wav`: mesma partitura, V9 antes da V10; RMS global pareado.
- `audios/C3X_V10_meia_liberacao_dupla_repeticao.wav`: ação com três golpes em tecla parcialmente solta.
- `audios/C3X_V10_meia_liberacao_repeticao_simples.wav`: mesma execução, um golpe apenas.
- `audios/C3X_AB_V10_dupla_vs_simples.wav`: comparação direta dos mecanismos.
- `audios/C3X_V10_DRY_pedal_dinamico_7s.wav`: pedal móvel, sem efeitos ambientais.
- `audios/C3X_V10_A4_quatro_intensidades.wav`: velocidades 25, 55, 85 e 115.
- `audios/C3X_AB_V9_vs_V10_A4_isolada.wav`: comparação da nota Lá4.

Todos os WAVs novos são estéreo, 48 kHz, PCM 16-bit. Os WAVs de referência são saídas sintéticas antigas, não inputs da síntese.

## Resultados e ressalvas

- **123 testes automatizados passaram** na execução registrada em `medicoes/resultados_regressao_completa.txt`.
- Auditoria espectral de 88 notas concluída: erro absoluto mediano de **0,617 cent** e máximo de **1,651 cent** usando janelas de sustentação adequadas por registro.
- Uma avaliação com janela precoce da nota E6 apresentou pico transitório cerca de 36 cents abaixo da fundamental. A análise posterior mostra a fundamental perto de 1318 Hz. Não confundir o pico transitório do corpo/ponte com afinação da corda.
- Na V10, as 18 entradas da partitura de teste produziram 18 golpes e reutilizaram as cordas de 10 notas distintas.
- Os parciais 2–7 do Lá4 diferiram no máximo 0,067 dB da V9 no protocolo de janela alinhada ao impacto. Em agudos altos alguns parciais fracos apresentaram diferenças maiores; a análise não comprova fidelidade sonora ao C3X físico.
- Não é plugin VST, não foi testado com MIDI real em Windows e ainda não há latência/CPU de tempo real validadas.

Mais detalhes em `RELATORIO_ETAPA_10.md` e `PLANO_ETAPA_11.md`.
