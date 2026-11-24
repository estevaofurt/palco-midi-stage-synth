# STAGE SYNTH — F1.3: auditor de Dó4 e evidência de fontes

**Status: preparação instrumental concluída; aquisição física do Yamaha C3X Dó4 NÃO realizada. Não modificar o sintetizador.**

## Por que esta etapa existe

A V10 mantém a afinação interna porque estima comprimentos, tensões e massas lineares com relações escolhidas pelo motor. Sua excelente consistência numérica *não demonstra* massa, rigidez, resposta do feltro ou radiação reais do C3X. Primeiro precisamos medir o exemplar e aceitar a metodologia de coleta. Este trabalho adiciona apenas ferramentas para registrar e analisar evidências — não desenvolve F2 nem um novo motor.

## Checagem adicional de fontes externas

| Fonte | Novo achado verificável | Classificação/limite |
|---|---|---|
| [Kemp 2023, PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0292515) | Publica Sol2 de um C3X real e separação aproximada de 3 cents nos picos do quarto parcial; deposita dados gerais do artigo em [OSF TBZDC](https://osf.io/tbzdc/) | **Dado espectral publicado para G2 apenas.** A declaração de disponibilidade do artigo não demonstra que o depósito contenha o arquivo bruto C3X, nem sua licença comercial; a listagem OSF não pôde ser acessada nesta consulta |
| [AudioLabs — Piano Concerto Dataset](https://audiolabs-erlangen.de/resources/MIR/PCD) | Disponibiliza arquivo `PCD_2.0.1.zip` rotulado pelos autores como *original WAV files*, com metadados (~1,2 GB); artigo descreve 15 excertos do C3X (R2), 180 s | **Existência do arquivo principal publicada**; não foi adquirido nem auditado. WAVs são apresentações musicais, não isolamento físico de C4. Verificar cadeia de processamento e licença **dos arquivos**, distinta da licença do artigo |
| [Karp, Acustica 1986](https://loopholes.blog/wp-content/publications/Karp-Inharmonicity-1986.pdf) | Medições de C4 em Blüthner e Erard, testando condições da ponte/tampo; demonstra que deslocamento da ponte afeta inarmonicidade além da rigidez da corda | **Referência metodológica de outros instrumentos**, proibido incorporar as medidas como Yamaha C3X |
| [Yamaha CX Series](https://usa.yamaha.com/musical-instruments/pianos/products/grand-pianos/cx-series/) | Construção do tampo, coroa, nervuras, encordoamento e feltro da série CX são descritos | **Fonte oficial qualitativa**, sem número de parâmetros físicos internos C4 |

**Licenciamento:** o artigo PLOS é CC BY, mas não inferir que os arquivos de áudio externos estejam automaticamente autorizados para calibração de produto comercial. Um outro site AudioLabs (`PCD_AudioLabs`) informa CC BY-NC-ND para um projeto *diferente*; não atribuir essa licença à coleção PCD sem evidência própria. Verificar cada origem separadamente.

## Ferramenta de medição, sem afirmar piano real

`research/c3x-physical/c4_measurement_audit.py`:

- Lê WAV PCM, registra SHA-256, taxa, duração, canais, subtipo, pico e clipping.
- Detecta o início e extrai picos espectrais até o 12º parcial, com interpolação local.
- Estima frequência fundamental e coeficiente **B** por ajuste sobre os parciais observáveis; mede erro do ajuste, não erro de calibração do piano.
- Pesquisa **picos duplos** ao redor do 4º parcial, fornecendo separação em Hz/cents. Um par pode resultar de uníssono, duas polarizações, reflexões ou outros efeitos: **a origem não é identificável por esse teste sozinho**.
- Estima o decaimento da fundamental pela projeção temporal; o **T60 reportado é extrapolado**, não uma medição direta de 60 dB.
- Falha de maneira conservadora para trecho curto, clipping ou baixa informação.
- **Nunca** atribui identidade Yamaha, autorização comercial ou aceite F1 automaticamente.

O mínimo para análise exploratória: nota C4 **isolada**, preferencialmente 48 kHz/24-bit mono ou estéreo, pedal solto, ao menos ~3 s sustentados sem nova pancada, nota solta em arquivo ou trecho separado, volume fixo e início de tecla/timestamp documentado. Para separar picos distantes só 3 cents no **4º parcial** do Dó4, uma janela longa é necessária; sem resolução/sinal suficientes, registrar **inconclusivo** e não inventar batimentos.

### Como executar

No diretório `research/c3x-physical`:

```bash
python -m pip install numpy scipy soundfile
python -m unittest -v test_c4_measurement_audit.py
python c4_measurement_audit.py caminho/para/dado_C4_isolado.wav --saida relatorio_C4.json --origem nao_verificada
```

Opcional: `--origem sintetico_teste` ou `--origem v10_sintetizado` para dados que **não** são piano real. Esses modos continuam com `instrument_identity_verified=false`, `commercial_rights_verified=false` e `f1_c3x_measured=false`.

O arquivo `template_meta_c4.json` exige identificar o exemplar, captação, afinação, autorização comercial e anotar o método de medição. Mesmo com todos os campos preenchidos, a aprovação requer revisão da proveniência e análise independente.

## Testes / prova negativa

O conjunto de 9 testes usa sinais matemáticos gerados localmente: afinação e B conhecidos, dois picos a ~3 cents, caso sem pico duplo, estéreo invertido de fase, áudio curto, clipping, hash estável, taxa de decaimento conhecida e entrada a 44,1 kHz. O medidor usa limite absoluto relativo à fundamental para evitar falsos picos causados por vazamento da FFT. **Esses testes verificam o medidor, não o Yamaha C3X.**

Os exemplos `F1_C4_TESTE_*` são sinais de osciladores sintéticos originais, *não gravações do Stage, Yamaha, Steinway ou qualquer fabricante*.

## Critérios bloqueadores da F1

1. Mesmo exemplar C3X identificado com documentação de sessão e direitos comerciais;
2. Tomadas originais isoladas C4 pp/mf/ff e eventos pedal/soltura, controle de gravação e hashes;
3. Medições independentes das propriedades de cordas, ataque e contato e, quando disponível, resposta da ponte/tampo/radiação;
4. Erro/incerteza, separação de treino/validação, revisão do analisador com originais e aceite do titular.

**F1 permanece pendente.** Não avançar F2–F13, não modificar DSP público, não considerar o ZIP de WAVs sintéticos como fonte acústica real.
