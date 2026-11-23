# Stage Synth — Felt Fuchs & Möhr: gravações ORIGINAIS verificadas para referência comercial

**Data de verificação:** 23/11/2026. **Base inicial do projeto:** main `dfa59b22e0528bd6642b7262cfe5c8b3ef0f5bcd` (antes da integração da pesquisa).
**Escopo autorizado:** proveniência, acesso, direitos, seleção de originais e protocolo de medições. **NÃO alterar síntese, timbre, MIDI, FX, UI, presets ou integração P1/P2.**

## 1. Fonte, autoria, licença e identidade

- Autor das gravações e do instrumento virtual: **Tom Guder**.
- Instrumento: piano vertical acústico **Fuchs & Möhr**, preparado com feltro; o autor relata afinação não uniforme.
- Fonte original de autoria e direitos: https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr .
- O criador declara textualmente suas **amostras como Public Domain**, disponibilizando o arquivo **FuchsUndMoehrSamplesWAV16bit.zip** com áudio WAV estéreo de 16 bits, três camadas.
- Link autoral de origem: https://drive.google.com/file/d/1XbIZgTdKoR2KxIyKM-CkEweS3HI4ieHu/view?usp=drive_link .
- O registro público não é uma licença Creative Commons padronizada (SPDX/CC0) com contrato de cessão assinado. A declaração explícita do próprio autor é forte evidência de intenção de liberar, mas **uma revisão jurídica de direitos patrimoniais, conexos e moral no Brasil permanece antes da comercialização**.

**Não confundir com espelhos:** a E0 anterior usou nove WAV reempacotados/recortados do CueHarbor/Hugging Face. Nesta etapa os dados foram obtidos **diretamente do ZIP do criador**, não do espelho.

## 2. Origem original acessível, sem baixar o ZIP completo

O ZIP do próprio autor responde a pedidos HTTP **206 Partial Content** com intervalos de bytes via `drive.usercontent.google.com`. Não foi necessário solicitar autenticação de conta, nem baixar todo o arquivo.

O script `research/commercial_audio/inspect_original_felt_zip_index.py` lê apenas a estrutura central do ZIP por intervalos limitados. Essa consulta confirmou:
- **Tamanho do ZIP original por Content-Range: 648.995.046 bytes**.
- **264 WAVs**: 88 `piano/p21.wav ... p108.wav`; 88 `mezzo/m21.wav ... m108.wav`; 88 `forte/f21.wav ... f108.wav`.
- Os números são **identificadores nominais** de nota MIDI nos nomes do arquivo, não validação espectral da afinação real. Níveis `piano/mezzo/forte` não são medidas de velocidade do martelo em m/s ou SPL calibrado.
- A indexação exigiu apenas **188.646 bytes** de dados de rede numa requisição de intervalo; não leu o conteúdo completo dos WAVs.

**Evidência de CI:** https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105179654 .

## 3. 15 WAVs realmente adquiridos, extraídos e verificados

**Seleção:** cinco identificadores MIDI — 36, 48, 60, 72 e 84 (C2, C3, C4, C5, C6 nominais) × três camadas **piano, mezzo e forte**. São **15 arquivos ORIGINAIS**, sem transposição no banco nem interpretação de MIDI como velocidade física.

**Verificação real:**
1. Entrada selecionada no diretório central do ZIP **original**, obtido pelo link autoral;
2. Transferência somente das partes comprimidas necessárias, com limite global de tráfego e de requisições HTTP;
3. Descompressão da entrada, confirmação de tamanho e **CRC32 do ZIP**;
4. Leitura PCM/WAV completa (2 canais, **48 kHz, 16 bits**, sem codec comprimido interno);
5. **SHA-256 dos bytes WAV originais**, armazenado como texto;
6. Eliminação dos dados de áudio ao fim da verificação; ZIP e WAVs **não** foram enviados ao GitHub nem embutidos no app.

**Evidência de CI:** https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105332553 — **36/36 testes** dos scripts de preparação e **15/15 WAVs aprovados**.

**Volume:** **70.189.788 bytes WAV originais descompactados**; **46.588.134 bytes transferidos da origem via intervalos**. Não foi gerado SHA256 do ZIP *completo*, pois **não foi totalmente baixado** — os hashes são por cada WAV selecionado, com CRC e tamanho conferidos.

Manifestos e scripts:
- `research/commercial_audio/felt_original_selective_manifest.json`: 15 membros do ZIP e seus identificadores/direitos;
- `research/commercial_audio/felt_original_verified_sha256.json`: **15 SHA-256 reais** registrados permanentemente;
- `research/commercial_audio/probe_original_felt_drive.py`: prova inicial de acesso limitado;
- `research/commercial_audio/inspect_original_felt_zip_index.py`: auditoria do diretório central via HTTP ranges;
- `research/commercial_audio/verify_original_felt_wavs.py`: SHA256 + CRC32 + cabeçalho/duração WAV, áudio descartado;
- `.github/workflows/commercial-felt-original-source.yml`: workflow que só gera artifacts JSON de metadados.

## 4. Abrangência acumulada de fontes comercialmente elegíveis

| Instrumento | Origem | Licença/declaração | WAV/FLAC individuais conferidos |
|---|---|---|---:|
| Steinway Model B | VCSL | CC0 | 4 |
| Knight Upright | VCSL | CC0 | 4 |
| Yamaha C5 Grand | Salamander / Alexander Holm | CC BY 3.0 | 15 |
| Kawai KW Upright | FreePats | CC0 | 5 |
| Steinway Model D | bitKlavier Grand / Princeton | CC BY 4.0 | 7 |
| **Fuchs & Möhr Felt Upright** | **Tom Guder, ZIP original** | **Public Domain declarado pelo autor** | **15** |
| **TOTAL** | **Seis instrumentos acústicos distintos** | | **50 originais** |

Total de WAV/FLAC originais **70.189.788 bytes Felt + 103.753.348 bytes anteriores = 173.943.136 bytes** validados nas operações de proveniência. Isso é evidência de integridade/origem/condições de uso, **não** de calibração física final, sem parâmetros de força de martelo/ponte.

## 5. O que o corpus Felt NÃO resolve

- **Não há uma gravação emparelhada do MESMO piano sem feltro**, com mesma posição dos microfones, intensidade física, afinação/ambiente. Portanto, não isola alterações causadas especificamente pelo feltro;
- Não existem **força martelo–corda F(t)**, compressão de feltro, velocidade real de martelo ou sua curva não linear por nota/velocity;
- Não existe mobilidade complexa \(Y_\mathrm{ponte}=v/F\) obtida ao aplicar uma **força conhecida diretamente na ponte**, com fase e região documentadas;
- Não sabemos se as camadas p/m/f têm resposta dinâmica física calibrada; os rótulos descrevem apenas grupos de gravação;
- O instrumento original estava ligeiramente desafinado e pode apresentar assimetrias; não inferir parâmetros gerais de um piano vertical comercial a partir de suas frequências isoladas;
- As licenças e obrigações de distribuição de **código** e os direitos de qualquer outro asset do Stage ainda não estão homologados; isso é independente das gravações.

## 6. Referências físicas e operação seguinte

**Protocolo técnico preparado:** [PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md](PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md), com ensaios independentes de martelo, H/V, 1–3 cordas, mobilidade da ponte, radiação, pedal e antes/depois felt. A literatura de Birkett/Weinreich/Miranda Valiente fornece as equações e os métodos, **mas não transforma gravações de microfone em força de impacto medida**.

**Status:** os **sete R-GATEs globais permanecem NÃO APROVADOS INTEGRALMENTE (0/7)**, apesar dos avanços em aquisição/proveniência. Não implementar novos motores, não alterar A/B/C/P1, MIDI, FX, UI ou presets. A pesquisa de parâmetros físicos e o exame de direitos devem continuar antes de qualquer liberação.
