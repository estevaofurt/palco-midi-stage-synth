# Stage Synth — E2.4: mobilidade real da ponte, contrato de medição e gates

**23/11/2026 — pesquisa isolada, PR #37.** O titular não identifica evolução do timbre de piano nos experimentos D; as etapas E2.0–E2.3 demonstraram passividade numérica e custo de vários modos, mas ainda não identificaram as propriedades do instrumento real. A v1.12.8 publicada fica preservada.

## Grandeza física que realmente falta

A **mobilidade de ponto da ponte** é `Y(f) = V_ponte(f) / F_ponte(f)`, com unidades **(m/s)/N** e força/velocidade medidas no **mesmo ponto e direção**. A **força no leito da tecla ou martelo não substitui a força da ponte**. `H_pa(f)=Pressão_microfone(f)/Aceleração_ponte(f)` tem unidades Pa/(m/s²) e identifica outra propriedade — a radiação da estrutura ao ar. Não confundir uma medida com outra e não interpretar `boardVelocity` normalizado da E2.3 como velocidade calibrada.

A nova biblioteca `research/bridge-mobility-h1.mjs` implementa estimativa espectral offline Welch H1 complexa, coerência e rejeição de frequências sem energia ou coerência suficiente. `estimateDocumentedBridgeMobility()` exige um manifesto que declare sensores, calibração, relógio comum, força e velocidade no mesmo ponto da ponte, fonte e direitos comerciais. **A checagem de metadados não é prova de licença nem de calibração — evidência externa continua obrigatória.** O algoritmo e o método de H1 são baseados em análise de sinais, não em conteúdo acústico proprietário.

## Protocolo mínimo para dados próprios ou licenciados

1. **Instrumentação:** excitação por martelo de impacto instrumentado **no ponto da ponte** e captação de velocidade por vibrometria laser ou acelerômetro calibrado integrado corretamente em m/s; documentar posição, direção e massas adicionadas. Para radiação acústica, captar microfones calibrados em Pa **sincronizados** na mesma sessão, com posição, distância, resposta e ambiente declarados.
2. **Aquisição:** mesmo relógio/sample rate e alinhamento temporal de força, velocidade e pressão; registrar unidades SI, pré-amplificadores, calibração e latência. Preferir séries de diferentes posições e ataques para obter banda larga confiável. Separar os pontos de medição e as posições de microfone de treino e validação.
3. **Qualidade de sinal:** rejeitar saturação, sinais quase silenciosos e deriva DC. Estimar H1 e coerência; marcar bins ruins como **indisponíveis**, não inventar frequências de tampo por interpolação arbitrária. Repetir a aquisição para medir variabilidade e coerência média; controlar causalidade no domínio do tempo.
4. **Validação independente:** prever medições e decaimentos para notas **não usadas no ajuste**, especialmente C2/C3 e regiões C4–C6, antes de calcular pressão sonora por uma IR medida e licenciada. Não usar uma melhoria de RMS sem percepção como indicador de realismo.
5. **Direitos:** anexar titular, tipo de licença, uso comercial, redistribuição, data, hash de origem e escopo de autorização no manifesto externo. Arquivos Zenodo/AudioLabs não entram no produto sem confirmação. Nem transcrição de notas nem a disponibilidade pública do dataset provam autorização.

## Implementação e evidência E2.4

- `research/bridge-mobility-h1.mjs`: H1 complexo e coerência de força real da ponte para velocidade real da ponte, mais contrato de proveniência, **sem ligação ao AudioWorklet**.
- `tests/bridge_mobility_h1.test.mjs`: cinco testes com ruído branco determinístico **SINTÉTICO**. Verificam ganho constante conhecido (0,002 (m/s)/N), atraso de três amostras/posição de fase, bins de baixa energia, argumentos inválidos e rejeição de força de tecla/sensor de microfone como substitutos da força de ponte.
- [GitHub Actions E2.4 — 45199247168](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45199247168): **197/197 testes passaram** e o diff de DSP/FX/UI/MIDI/presets públicos permaneceu vazio. O teste **não contém uma amostra real de piano**, não verifica mobilidade medida e não calibra as frequências, massas e perdas do laboratório.

## Próximo trabalho com gate objetivo

Somente a partir de uma aquisição com autorização e SI verificáveis: `F_ponte(t)`, `v_ponte(t)`, `a_ponte(t)` e `p_L(t),p_R(t)` sincronizados, gerar relatórios de coerência e parâmetros por banda, identificar uma rede mecânica passiva que reproduza `Y(f)`, e medir a radiação separadamente. Se não houver dados, o avanço é **identificar claramente o bloqueio físico** — não fingir nova versão sonora.

**Decisão:** manter PR #37 em draft, sem WAV anunciado como piano aprimorado e sem alterar motor D v1.12.8, A/B/C/Clássico/default C ou histórico. R-GATEs 0/7; 32/48/64 notas só são benchmarks de solver Node, não de PC ou Android.
