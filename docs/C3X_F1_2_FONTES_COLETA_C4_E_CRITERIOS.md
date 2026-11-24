# STAGE SYNTH C3X — F1.2: evidências e procedimento de coleta do Dó4

**Estado em 23/11/2026: F1 PENDENTE — nenhuma medição física inédita do C4 foi obtida.** Este documento organiza a execução da F1; não aprova F2, F8, F9, V11D, otimização ou integração no aplicativo. Preserve V1/V10 como **protótipos**. O repositório é destinado a produto comercial; não importar WAV sem permissão aplicável.

## 1. Auditoria complementar de fontes primárias

| Prioridade | Fonte | Constatação | Decisão |
|---|---|---|---|
| 1 | [Yamaha CX Brasil](https://br.yamaha.com/pt/musical-instruments/pianos/products/grand-pianos/cx-series/) e [Europa](https://europe.yamaha.com/en/musical-instruments/pianos/products/grand-pianos/cx-series/) | C3X convencional 149×101×186 cm, 320 kg; tampo com crown conforme técnica CFX; encordoamento redesenhado, feltro da mesma base do CFX adaptado ao modelo, vigamento C3X+ reforçado (fabricante diz aproximadamente 20% mais espesso que anterior). | **Descrição qualitativa do fabricante**, não fornece as propriedades constitutivas, modos, tensão ou comprimentos de corda. Não ajustar DSP por slogans comerciais. |
| 1 | [Yamaha EUA — ficha da família CX](https://usa.yamaha.com/musical-instruments/pianos/products/grand-pianos/cx-series/specs.html) | Tabela mostra **185 cm** de profundidade para C3X, enquanto Brasil/Europa informam **186 cm**; indica **4 travessas traseiras**. | Registrar divergência documental sem presumir motivo; identificar ano, região e exemplar antes de qualquer cota externa. |
| 2 | [Kemp, *PLOS ONE*, 2023](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0292515) | C3X real da Universidade de St Andrews, G2/43, pico duplo do quarto parcial em cerca de 3 cents. O artigo indica [OSF TBZDC](https://osf.io/tbzdc/) com dados subjacentes. | O **link está confirmado**, mas não conseguimos listar nem conferir arquivos OSF. Não afirmar que contém WAV G2, muito menos C4. Perguntar ao responsável sobre sinais brutos e possibilidade de uma sessão no mesmo instrumento. |
| 3 | [Piano Concerto Dataset, 2023](https://reference-global.com/article/10.5334/tismir.160?tab=article) | Sala R2 contém Yamaha C3X com 15 trechos musicais de 12 s. Os pesquisadores dizem que dados **raw podem ser solicitados**, mas as faixas distribuídas `P` (sem reverb artificial) **ainda receberam EQ, edição e redução de ruído**. | Útil para referência perceptiva de frase, não para identificar massa, tensão ou mobilidade de C4. Verificar licenças do áudio e termos de uso comercial separadamente da licença do artigo. |

**Observação jurídica:** artigo publicado em CC BY não significa automaticamente que todo arquivo de áudio citado ou hospedado em outro repositório seja liberado para uso comercial. Os arquivos C3X de St Andrews e PCD **não foram baixados, testados nem usados para calibração** nesta etapa.

## 2. Estratégia F1 — duas vias, uma única classificação de evidência

**Via A — maior valor para F1:** localizar **um C3X convencional real** (registro interno do exemplar, revisão, manutenção e afinação). Com autorização do proprietário e técnico de piano, documentar as características do Dó4 e coletar sinais não processados. Nome/código do instrumento e ambiente devem permanecer consistentes nas sessões; possível informação privada fica fora do GitHub.

**Via B — dados existentes:** verificar se os arquivos OSF incluem G2 cru; solicitar **C4 cru com documentação e licença** aos autores / operador do C3X quando disponível. O PCD pode ajudar na escuta, mas sua fonte R2 é outro exemplar e não supre medição física. Ambas as vias podem coexistir, **sem misturar parâmetros de exemplares como se fossem o mesmo**.

## 3. F1.3 — especificação de gravação de C4, sem criar sinais fictícios

1. **Instrumento e ambiente:** data, código do exemplar, A4 afinado, temperatura e umidade, estado de regulação e abafadores, posição de tampa e pedais; microfone identificado, distância, altura, orientação, pré, ganho, latência, relógio e ruído de fundo. Testar a sala com sinal de referência e registrar acústica residual.
2. **Sinal bruto:** WAV PCM **sem equalização, compressão, normalização, denoise, reverb ou time-stretch**, preferencialmente 48 ou 96 kHz / 24 bits. Capturar o mesmo ganho em todas as execuções e incluir um trecho de silêncio. A ausência de reverb artificial não elimina o som da sala.
3. **Três dinâmicas repetidas:** Dó4 isolado **pp/mf/ff, cinco execuções de cada** (15). Registrar velocidade **real do martelo** se houver sensor; caso contrário informar que pp/mf/ff são apenas classes de toque, **não m/s**. Evitar variar ganho ou microfone entre repetições.
4. **Articulação:** três testes de soltura, três de pedal total e três de meio-pedal (9); anotar timestamps do toque, note-off e deslocamento do pedal. O meio-pedal real varia por instrumento/afinação do mecanismo; não converter posição a partir de CC64 sem calibração.
5. **Cordas individuais:** fotografar/contar as cordas do Dó4 e medir comprimento com auxílio de técnico. Se autorizado, usar abafamento temporário das demais cordas para medir cada parcial/corda; **não manipular nem forçar cordas, feltro ou ponte sem profissional habilitado**.
6. **Verificação:** SHA-256 por WAV original, identificação da tomada, cabeçalho PCM, sem clipping, silêncio/ruído, dispositivo e direitos de uso comercial. Calibrar amplitude somente se existir cadeia de referência adequada; senão valores são **relativos**, não Pa.
7. **Fase física avançada (plano, não coleta atual):** força/velocidade do martelo, mobilidade complexa da ponte e radiação exigem sensores sincronizados e método não destrutivo por especialista. Não derivar força, massa modal, impedância ou ortotropia apenas a partir do sinal de microfone.

Os **24 registros previstos**, vazios e explicitamente `PENDENTE`, estão em [F1_SESSOES_C4_PLANEJADAS.csv](../research/c3x-physical/F1_SESSOES_C4_PLANEJADAS.csv). Os **16 parâmetros C4** sem medidas estão em [F1_PARAMETROS_C4_PENDENTES.csv](../research/c3x-physical/F1_PARAMETROS_C4_PENDENTES.csv). Não criar WAVs sintéticos para preencher essa evidência.

## 4. Dó4: por que o WAV da V10 e a afinação interna não bastam

A V10 ajusta massa linear da corda para obter frequência esperada a partir de `T/(4L²f₀²)`. Essa identidade reproduz a afinação configurada, mas **não identifica** de forma independente tensão, comprimento, massa linear e rigidez de um C3X. Sem medição separada, combinações distintas desses parâmetros geram a mesma f0. O mesmo vale para radiatividade: FFT de microfone isolado não isola contribuição de ponte, tampo e sala. Não acrescentar EQ/agudos artificiais como substituto de medição.

## 5. Critérios auditáveis de progresso

| Submarco | Entrega | Situação |
|---|---|---|
| F1.1 | Exemplar C3X identificado para C4 e autorização de coleta | **Não obtido** |
| F1.2 | Inventário e fontes classificadas, CSV/JSON, divergências documentais | **Documentado; origem experimental ainda pendente** |
| F1.3 | C4 bruto e medições com incerteza, arquivos e hashes verificados | **Não obtido** |
| F1.4 | Protocolo, lacunas e instrumentos de auditoria | **Documentado; execução pendente** |
| F1.5 | Revisão legal, licença comercial e aceite explícito | **Não obtido** |

**Decisão:** F1 permanece **PENDENTE**. Não retomar portabilidade V11D, F12 ou som novo no app; PR #44 draft, branch principal e DSP público inalterados.
