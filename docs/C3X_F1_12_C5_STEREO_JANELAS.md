# STAGE SYNTH C3X — F1.12: robustez por canal e janela, referência Yamaha C5

**Status físico:** F1 Yamaha C3X **PENDENTE**. Estudo descritivo **exclusivamente de gravações originais de um Yamaha C5**, captadas por Alexander Holm (Salamander Grand Piano, CC BY 3.0), nas camadas C4v1, C4v8 e C4v16. Não altera V10, IR, presets nem o aplicativo Stage Synth. **Não é identificação de martelo, corda, ponte ou radiação do C3X.**

## Motivo

A F1.4 observou cancelamento artificial do H5 por resposta modal sintética na V10; a F1.5 demonstrou matematicamente a sensibilidade espacial da radiação. A comparação anterior usou áudio mono (média L/R). Precisamos verificar se o H5/H4 estimado no C5 é estável **em cada canal** e **sob mudanças moderadas de janela**, antes de sugerir qualquer mudança de física.

## Método reproduzível

1. GitHub Actions baixa **somente** `Samples/C4v1.flac`, `C4v8.flac` e `C4v16.flac`, commit pinado `3382bf9496bba2486f5ab0de55a264d1dfc38404`, e valida byte-count e SHA-256 contra inventário do projeto. Sem distribuir áudio original no GitHub ou no produto.
2. Recupera f1/B apenas como **âncora descritiva** do relatório numérico C5 já conferido em F1 anterior; não transforma esses valores em propriedades do C3X.
3. Analisa L, R e sua média, em três janelas de tempo (ataque/corpo/cauda), cada qual com 3 inícios × 3 durações: **9 escolhas por estágio × 3 canais × 3 camadas**. FFT com Hann e interpolação; compara H5/H4 em bandas **±8 Hz centradas nos parciais previstos por f1/B**, impedindo selecionar erroneamente o pico lateral ~1291 Hz da V10 como H5 esperado em ~1317 Hz.
4. Rejeita medição quando o contraste de H4 ou H5 com a vizinhança espectral está abaixo de 6 dB. Descreve medianas, percentis 10–90, mínimos, máximos e contagem de janelas rejeitadas. **Percentis são sensibilidade à janela, NÃO intervalos de confiança estatísticos.**
5. O estudo registra diferença entre os microfones esquerdo e direito e o desvio da média estéreo, sem atribuir diferenças a parâmetros internos do instrumento.

## Execução

```bash
python -m unittest discover -s research/c3x-physical -p 'test_c5_stereo_robustness.py' -v
# Aquisição original somente em runner temporário com GitHub Actions:
# .github/workflows/c3x-f1-12-stereo-robustness.yml
```

## Condições de aceitação

- 11 testes de controle devem passar; aquisição de 3 FLACs deve validar SHA-256; todas as escolhas de janela têm resultado, inclusive rejeição documentada.
- **Sem ajuste de DSP** baseado apenas na amplitude de H5/H4; sensibilidades espaciais e observação de C5 não são evidência de radiação do C3X.
- Exigir medições de vibração da ponte/tampo sincronizadas com pressão (ou referência C3X licitamente medida) antes de afirmar F7 ou F1 concluída.

Fontes: [Salamander Grand Piano, Yamaha C5 / Alexander Holm](https://sfzinstruments.github.io/pianos/salamander/); [referência técnica anterior F1.5](C3X_F1_5_RADIACAO_IDENTIFICABILIDADE_E_ABLACAO.md). Banco de samples original **não faz parte da síntese**.
