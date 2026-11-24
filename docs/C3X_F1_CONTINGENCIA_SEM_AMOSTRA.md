# F1 — Plano de contingência: ausência de gravação ou acesso físico a C3X

**Registro:** titular informou que não consegue obter/fornecer gravação própria de Yamaha C3X. **Não exigir que o usuário adquira equipamento, visite estúdio ou grave amostras** como condição para continuar a pesquisa metodológica. **F1 específica do Yamaha C3X segue PENDENTE.**

## Fontes existentes que podemos usar sem falsificar a origem

1. **Yamaha C5 (piano de cauda), Salamander Grand Piano v3**, Alexander Holm, licença CC BY 3.0; localizados e previamente auditados no Stage Synth em `research/commercial_audio/verified_source_sha256.json` e `cc_flac_pilot_manifest.json`:
   - [C4v1.flac](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/3382bf9496bba2486f5ab0de55a264d1dfc38404/Samples/C4v1.flac): SHA-256 `ca44d2e906110ebc2f67ae4c233e84cbbf0e657fe53e1c6724e4f31409478f11`.
   - [C4v8.flac](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/3382bf9496bba2486f5ab0de55a264d1dfc38404/Samples/C4v8.flac): SHA-256 `36fb0535a1f21fe1dfc367c361dedda73710144e8c4940b40e97e6e5f8a3c694`.
   - [C4v16.flac](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/3382bf9496bba2486f5ab0de55a264d1dfc38404/Samples/C4v16.flac): SHA-256 `e2944a0d1b31ea0ff8eb82b20ae2108027f111d96fb680c6e36d01f40582c252`.
   - [Origem/licença](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/3382bf9496bba2486f5ab0de55a264d1dfc38404/README.md).
   - Posições de microfone ~12 cm sobre as cordas, 48 kHz/24-bit, camadas v1/v8/v16 **não equivalem a velocidades físicas do martelo**. Sem informação física suficiente para identificar cordas/ponte de um C3X. O uso exige atribuição e revisão das condições comerciais antes da incorporação do material a um produto.

2. **Meta Open Sound — Meta Piano**, licença CC0 declarada pelo editor, contém `INSPiano_Vel03_C4_01.wav` e quatro camadas C4, mas é **piano vertical**, não C3X nem C5. Útil somente para testar pipeline e método, com atenção a processamento/ruído, sem forçar parâmetros Yamaha.
   - https://github.com/facebookincubator/Meta-open-sound
   - https://github.com/facebookincubator/Meta-open-sound/blob/main/systems/instruments/meta-piano/README.md

3. **C3X real no Steinberg Etude**: nota C4 está contida em biblioteca comercial de samples; **não extrair, incorporar ou calibrar** a partir de arquivos proprietários sem licença explícita para tal. Demonstrações autorizadas podem ajudar escuta subjetiva.

## Duas frentes de trabalho distintas

**Frente A — ciência/método (executável sem C3X medido):**
- Verificar os hashes já documentados ao adquirir fontes originais de maneira legal;
- ensaiar analisador `c4_measurement_audit.py` em áudios de **Yamaha C5** e em casos sintéticos;
- medir precisão de f0/B, batimentos, coeficientes de decaimento e separação dos parciais em janelas e níveis de ruído distintos;
- caracterizar explicitamente a transferência de microfone/sala como limitação de observação;
- deixar os resultados no domínio **C5/metodologia**, não rotular de C3X;
- manter código V10 preservado, sem nova modificação de timbre público.

**Frente B — identificação específica C3X (ainda bloqueada):**
- localizar gravações C3X C4 verdadeiramente isoladas e com autorização de calibração comercial;
- obter física do mesmo instrumento com unidade/erro/proveniência (ao menos encordoamento e dinâmica observável do Dó4);
- se tais dados forem inacessíveis, comunicar a limitação: produto pode ser **piano de cauda físico genérico inspirado no C3X**, mas não deve alegar emulação verificada de um exemplar real.

## Regra de status
- F1: **PENDENTE** para Yamaha C3X real.
- Nenhum parâmetro identificado no C5, Meta Piano ou no protótipo V10 deve migrar para a coluna `medicao_c3x`.
- F2–F13 não recebem aprovação automática nem por falta de acesso ao instrumento.
- CI/retorno auditivo/checagem de segurança de software continuam úteis como métodos de pesquisa e não como prova física.
