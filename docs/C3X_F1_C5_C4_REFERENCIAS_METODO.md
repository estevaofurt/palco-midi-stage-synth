# STAGE SYNTH — F1 / Yamaha C5 Dó4, referência auditiva licenciada

**Esta pesquisa utiliza o Yamaha C5 (Salamander Grand Piano V3), NÃO um Yamaha C3X.** A F1 específica do C3X continua pendente. O motor V10 não é alterado e não recebe samples como fonte sonora.

## Fonte

Alexander Holm, *Salamander Grand Piano V3*, CC BY 3.0. Três arquivos originais 48 kHz / 24-bit: `C4v1.flac`, `C4v8.flac`, `C4v16.flac`. Download do commit `3382bf9496bba2486f5ab0de55a264d1dfc38404` em [sfzinstruments/SalamanderGrandPiano](https://github.com/sfzinstruments/SalamanderGrandPiano). A prova de proveniência e os hashes estão no inventário existente do STAGE SYNTH (`research/commercial_audio/verified_source_sha256.json`). Condições CC BY 3.0: preservar atribuição de autor, fonte, licença e alterações; revisar obrigações para distribuição comercial.

A biblioteca tem microfones AKG C414 a aproximadamente 12 cm das cordas; a captação inclui a resposta dos microfones/instrumento e possivelmente sala, não corresponde à radiação espacial isolada de um tampo. Camadas v1/v8/v16 são níveis da biblioteca, não martelo medido em m/s. A comparação com velocidades V10 MIDI 25/75/115 é ilustrativa, não pareamento físico de dinâmica.

## Análise

- `c5_c4_analysis.py`: extrai f1 e B por ajuste, até doze parciais, evolução harmônica ataque/corpo/cauda; gera apenas JSON numérico.
- `v10_c4_profiles.json`: perfis numéricos da V10 renderizados sem samples e com normalização desligada; volume absoluto não é comparável ao C5.
- `download_analyze_c5.py`: só realiza download com commit fixado, SHA256 e tamanho exatos, no diretório temporário do GitHub Actions; **nenhum FLAC/PCM é publicado**.
- `test_c5_c4_analysis.py`: controles artificiais, sem alegar medição C3X.
- `.github/workflows/c3x-f1-c5-c4-compare.yml`: roda download/provenance/FFT apenas em CI e publica resultados numéricos; apaga FLAC do runner.

Métrica `mean_absolute_difference_db` é distância descritiva de harmônicos 2–8 em relação à fundamental, **não** uma nota de fidelidade perceptual ou validação física. Não medir decaimento material apenas de janelas de mic/room ou de arquivos retocados.

## Próximas decisões

1. Confirmar os três hashes no CI (não basta existir URL).
2. Comparar evolução de parciais do C5 com V10. Se os resultados forem inadequados, preparar hipóteses de instrumentação **antes** de mudanças de DSP.
3. Manter a F1 Yamaha C3X como pendente; um C5 nunca deve ser rotulado como medição C3X.

## Primeira execução com C5 real — verificada

GitHub Actions [run #45313270498](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313270498) aprovou 6 testes sintéticos, obteve os três FLACs originais, verificou os três hashes e analisou os parciais; somente JSON numérico foi publicado. O relatório `RELATORIO_F1_C5_REAL_V10.md` descreve o resultado. **Antes de fechar a comparação**, o protocolo de referência V10 foi corrigido para manter a nota pressionada até 1,765 s e os harmônicos quase inaudíveis foram excluídos da métrica complementar `mean_absolute_difference_salient_db`.

As observações C5 real mais relevantes incluem B~0,00028–0,00030 e 4º/5º parciais muito diferentes da V10. Essas são características dos sinais captados e **não são dados físicos internos identificados do Yamaha C3X**.
