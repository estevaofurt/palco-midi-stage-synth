# Stage Synth — referências acústicas comercialmente seguras: preparação piloto

**Data:** 22/11/2026 (execuções de CI registradas em 23/11 UTC).
**Base anterior:** main 92654d35e55bc20ba7723621bc28f9bd4b0457a7, v1.12.4.
**Objetivo:** obter e verificar ORIGINALMENTE arquivos licenciados para potencial uso comercial, sem acrescentá-los ao software, nem extrair parâmetros físicos não identificáveis.

## 1. VCSL CC0: 8 WAVs originais verificados

Origem: https://github.com/sgossner/VCSL , commit **c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e**, fonte de licença CC0 https://versilian-studios.com/vcsl/ .

**Oito arquivos originais** foram baixados do repositório principal, conferidos contra tamanho e SHA1 Git blob do commit, receberam SHA256 e foram abertos como PCM WAV **44,1 kHz, 24-bit**. Bytes totais: **37.495.964**.

- Steinway Model B, NoSus (close): C2, C4 e C6, camada de fonte vl3.
- Steinway Model B, Sus (close): C4, camada vl3.
- Knight Upright: C#2 (vl1), C#4 (vl1 e vl2), C#6 (vl2).
- O arquivo autoral NORMALIZED.txt na pasta do Steinway informa expressamente que **as articulações Sus/NoSus foram normalizadas**. NÃO usar esses ganhos como curva de velocidade física/martelo; vl3 não equivale a mezzo-forte calibrado.
- O Knight foi gravado em tons inteiros a partir de A0; C# foram efetivamente gravadas, C natural não deve ser alegado como sample original.
- Teste por URL imutável: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45101388156 . O fluxo testou SHA, WAV e apagou arquivos; artifact apenas JSON de checksums/metadados.

## 2. Salamander Yamaha C5: 15 FLAC comerciais em cinco registros

Origem: https://github.com/sfzinstruments/SalamanderGrandPiano , commit **3382bf9496bba2486f5ab0de55a264d1dfc38404**, autor **Alexander Holm**, licença **CC BY 3.0** no README.

- Piano físico identificado: Yamaha C5, NÃO Yamaha CFX.
- Captação: dois AKG C414 em AB, aprox. 12 cm acima das cordas; arquivos FLAC originais de gravação 48kHz/24-bit, 16 layers no banco.
- Seleção piloto em cinco regiões: **C2, C3, C4, C5, C6**; três layers em cada, **v1, v8, v16**; total 15 arquivos.
- Os labels v1/v8/v16 NÃO medem diretamente a velocidade do martelo. O SFZ suporta seleção natural/retuned; amostras retuned não constituem outro piano físico.
- Para qualquer uso comercial ou adaptação publicada, conservar autor, licença, link e aviso de modificações aplicável.
- Os FLAC originais são escolhidos para substituir AAC reempacotados usados nas investigações E0.

## 3. FreePats Upright KW: 5 FLAC CC0 originais

Origem: https://github.com/freepats/upright-piano-KW , commit **570f6c60ed2eff67accad3b85d5b452e57a3ad28**, licença **CC0 1.0** registrada em LICENSE.

- Instrumento real: piano vertical Kawai, gravação com Zoom H1 diante do instrumento, numa sala residencial, com edição de amostras.
- Cinco arquivos individuais: C2 (vL/vH), C4 (apenas vL), C6 (vL/vH).
- O arquivo **samples/C4vH.flac NÃO existe** no commit auditado. Não presumir três velocidades em todos os registros.
- O mapeamento SFZ contém **loops nos graves**. Esses trechos não são adequados para medir decaimento físico natural de cordas.
- Fonte de comparação entre caráter de grand e upright, NÃO modelo completo de martelo e ponte.

## 4. Auditoria reproduzível no GitHub — dados SEM áudio

- Manifesto 1: research/commercial_audio/vcsl_cc0_pilot_manifest.json (8 WAV, Git blob SHA e origem).
- Manifesto 2: research/commercial_audio/cc_flac_pilot_manifest.json (20 FLAC Yamaha/Kawai, SHA e licença por arquivo).
- Validador WAV: research/commercial_audio/verify_vcsl.py: verifica origem fixa CC0, SHA1 Git blob, SHA256 e propriedades RIFF/WAV.
- Validador FLAC: research/commercial_audio/verify_flac.py: verifica origens fixas CC BY 3.0 / CC0, SHA1 Git blob, SHA256, STREAMINFO e **decodificação integral sem gerar outro áudio**.
- Dez testes unitários offline, incluindo proteção de licença NC, commit imutável, caminho malicioso, PCM e STREAMINFO.
- Automação: .github/workflows/commercial-reference-prep.yml: arquivos apenas em /tmp do runner e excluídos após conferência; artifact temporário somente com metadata e hashes. NÃO há arquivos de gravação publicados no repositório.

## 5. Referências que continuam PENDENTES

| Fonte | Licença e problema | Próximo passo permitido |
|---|---|---|
| Princeton bitKlavier Grand Steinway D | CC BY 4.0, 16 camadas, 9 posições mic, mas áudio denoised/normalizado; ZIP PianoBar 44k16b ~931 MB | Selecionar coleção original e validar hash/download e mapeamento; não usar níveis como força do martelo |
| Iowa Steinway Model B | autorização institucional explícita para qualquer projeto, 9 AIFF já usados em E0 | Preservar checksums, direitos e ambiente não anecoico; possível ampliar intensidades/notas |
| Felt Fuchs & Möhr / Tom Guder | domínio público declarado pelo autor, 9 WAV do espelho usados em E0 | Conferir distribuição original do autor, cadeia de direitos e cortes do espelho; falta comparação pareada com/sem feltro |
| BiVib, RWC, MAPS e MAESTRO | restrição NonCommercial nas licenças conhecidas | Literatura pode ser estudada, mas NÃO usar arquivos em pipeline comercial sem licença adicional expressa |
| Yamaha CFX verdadeiro | demos comerciais e EULA, sem corpus aberto medido | Comparação de escuta só nos termos legais; não confundir C5/CFX nem copiar amostras |
| Martelo, ponte e tampo | sem séries de força e mobilidade física para o piano alvo | Obter dados próprios ou contrato comercial com laboratório; método passivo aproximado só se formalmente delimitado |

## 6. Protocolo para obtenção de medições PRÓPRIAS com direitos comerciais

**Não foram agendadas gravações ou feitos contatos com titulares nesta etapa.** Protocolo disponível para contratar um técnico/laboratório especializado e documentar direitos sobre áudio e parâmetros derivados:

1. Contrato com fabricante/proprietário/intérprete/engenheiro para captação e uso comercial dos dados e resultados, com detalhes sobre exclusividade, eventual redistribuição, autoria e confidencialidade.
2. Instrumentos identificados: ao menos um cauda japonês, um Steinway B ou D, um vertical e, para o Felt, o MESMO instrumento com/sem feltro, com microfonação e afinação equivalentes.
3. Notas piloto 36, 48, 60, 72, 84 (ou notas originalmente amostradas mais próximas), ao menos três intensidades controladas, press/release, CC64 parcial/total, rearticulação e condições de tampa/sala.
4. Áudio em PCM original sem EQ, reverb, compressão ou normalização independente por layer. Microfones próximos e na posição do ouvinte, calibrados com ganho/fase, coordenadas, sample rate/bit depth e canais anotados.
5. Martelo: obter força(t), compressão(t) e velocidade real por instrumento/registro com instrumentação não destrutiva de especialista. Não extrair força física apenas de WAV gravado à distância.
6. Ponte/tampo: medir força de impacto instrumentado DIRETAMENTE na ponte e aceleração na mesma região para estimar mobilidade complexa, além da pressão L/R. **Força de tecla contra base não é força direta na ponte.**
7. Guardar cada sinal com URI/fonte, license/contrato, SHA256, pitch real, velocity real ou comandada (distinguir), pedal/lid/damper, mic, ganhos, sala, data, edições e restrições de uso.
8. Arquivos privados continuam fora do GitHub e do app. Só publicar estatísticas e metadados não reversíveis.

## 7. Decisão de prontidão

A verificação de origem/licença/bytes de um **subconjunto** é avanço concreto em R-GATE-1, R-GATE-3 e R-GATE-4, porém esses critérios são amplos e **NÃO estão concluídos**. Falta caracterização física do martelo/cordas/ponte, controle de dinâmica, corpus Felt pareado, seleção Steinway D e CFX, medidor confiável, validação da saída final A/B/C, avaliação perceptual e hardware PC/Moto g04s. A prontidão global continua **0 de 7 R-GATEs integralmente aprovados**.

**Congelamento permanece:** não implementar P1/P2, não alterar motores, MIDI, FX, UI ou presets. A aquisição e documentação legalmente segura podem continuar.
