# Stage E2.2 — radiação acústica com dados medidos: contrato, bloqueios e testes (23/11/2026)

## Por que esta etapa é necessária
A E2.1 simula contato do martelo, cordas e ponte compartilhada com conservação de energia. Sua saída `boardVelocity` é velocidade **mecânica generalizada em unidades normalizadas**, não pressão sonora no ouvido. O motor D v1.12.8, por sua vez, soma modos de corda e ressonância úmida sem fechar uma carga recíproca ponte↔corda. Produzir WAV a partir de `boardVelocity` como se fosse som acústico seria incorreto.

## Código e testes em isolamento
- `research/measured-radiation-adapter.mjs`: contrato de resposta impulsiva **medida, causal, sincronizada, calibrada e com autorização comercial documentada** de aceleração da ponte para pressão sonora estéreo, `H(f)=Pa/(m/s²)`. Corrige unidade da entrada por diferença de velocidade × taxa de amostragem. FIR circular causal, sem alocação em `render()/renderBlock()`, limitado a **1024 coeficientes**. Não usa EQ/IR fictícia como resposta de produto.
- `CalibratedPassivePianoResearchChain`: apenas experimento que conecta E2.1 à transformação estéreo quando a coordenada mecânica já foi calibrada para m/s e o FIR é fornecido por medição autorizada. Nenhum fallback é gerado.
- `tests/measured_radiation_adapter.test.mjs`: **somente IRs matemáticas sintéticas criadas no próprio teste**, para verificar conversão de unidades, FIR causal, equivalência amostra/bloco, contagem de energia da física, zero-input e rejeição de metadados ausentes. Os campos `sourceId` e `rightsDocumentId` dos testes são deliberadamente `SYNTHETIC` e **não autorizam uso real**.
- `step()` tem retorno por objeto para pesquisa offline; só `render()/renderBlock()` evitam alocações. Para integração real será necessário ainda escolher uma convolução eficiente para respostas longas e auditar o custo AudioWorklet.

**Importante:** as verificações em tempo de execução asseguram apenas que o fornecedor **declarou** origem, calibração, licença e unidades. Elas não conferem juridicamente direitos ou autenticidade do dataset. Nenhuma IR física medida foi carregada, e o campo `bridgeCoordinateCalibrated` não calibra automaticamente as coordenadas normalizadas.

## Fontes primárias verificadas e suas incompatibilidades

1. **Plath / Universidade de Hamburgo —** [Zenodo 3271370](https://zenodo.org/records/3271370). Contém, para o mesmo evento a 50 kHz, força de impacto na base da tecla [N], **aceleração da ponte** [m/s²], e pressões esquerda/direita no manequim [Pa]. Esses pares são adequados para estimar **transferência relativa da aceleração da ponte para pressão** por H1, se alinhados e calibrados. **Não fornecem diretamente mobilidade mecânica `v_ponte/F_ponte`**: força no leito da tecla não é força aplicada na ponte. Na página consultada, a seção *Rights → License* não exibe licença específica; disponibilidade para download **não prova autorização comercial**. O pacote tem 4,6 GB; não foi obtido nem incorporado.
2. **AudioLabs Erlangen —** [site 2023 PianoSynth](https://audiolabs-erlangen.de/resources/MIR/2023-ISMIR-PianoSynth/). As IRs Yamaha C3 descritas foram medidas usando **alto-falante de contato no tampo**, excitação por chirp e microfones estéreo acima do piano em sala. **Não são** transferência calibrada da aceleração da ponte [m/s²] para pressão [Pa] e incluem componente da sala. Seu conteúdo e seus direitos de uso comercial não foram verificados. Portanto **não podem ser conectadas diretamente** ao contrato E2.2.
3. `research/bridge-radiation-h1.mjs` calcula H1/coerência em sinais sincronizados. Um espectro estimado com lacunas de coerência **não é um FIR causal pronto**; precisa de estimação temporal, tratamento de fase/alinhamento e validação com outro evento.

## Gates de liberação
1. Medição própria ou acordo/licença comercial verificável, incluindo posição do sensor e microfones, calibração e carimbo de relógio comum.
2. Calibração SI dos graus de liberdade do laboratório e caracterização de mobilidade `força_ponte→velocidade_ponte`, separada de `aceleração_ponte→pressão`.
3. Identificação de transferência radiativa com faixa de coerência, causalidade, resposta no tempo e eventos de validação independentes; sem interpolar indiscriminadamente lacunas.
4. A/B de notas C2/C3 e outras regiões versus referências sonoras com controle de volume, escuta cega e análise de cauda/harmônicos. Nem engenharia de testes nem amplitude de saída demonstram qualidade de piano.
5. Testes completos de AudioWorklet em PC/Android com 32/48/64 notas, MIDI, FX e pedal, com preservação do seletor existente de Piano Acústico.

**Decisão:** manter E2.2 somente como infraestrutura de pesquisa da [PR #37](https://github.com/estevaofurt/palco-midi-stage-synth/pull/37). O motor D público v1.12.8 e A/B/C/Clássico continuam byte a byte intocados; 0/7 R-GATEs comerciais fechados. Não gerar um WAV fictício nem declarar melhoria de timbre.
