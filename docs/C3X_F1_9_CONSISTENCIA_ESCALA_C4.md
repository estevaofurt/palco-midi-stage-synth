# F1.9 — consistência física da escala do Dó4 (24/11/2026)

**F1 permanece PENDENTE.** Base: 09d59060470f709d6c9928bdb6312dc33c5b8b93 (F1.8). Auditoria matemática isolada. Sem alteração da V10, aplicativo publicado, DSP, áudio ou avanço F2–F13. Não é especificação de fabricação, regulagem ou segurança de cordas reais.

## Evidências e hipótese

- V10 parameters.py, blob b23c89225c1ed0d1ad7e1a2ecd9976fe29d82339: C4 MIDI60, não enrolada, L=0,545 m, d=1,0328947368421053 mm, T=702,6315789473684 N, E=200e9 Pa, rho=7850 kg/m³. Constantes de aço e escala hipotéticas, não medidas Yamaha. O código usa mu=T/(4 L² f_alvo²) e B=pi³ E d⁴/(64 T L²).
- V10 tuning.py, blob 88ca68af75eb1abb847d8c32da0e36409137aefb: perfil equal corrige T por 1-B e B por B/(1-B), mantendo T*B.
- F1.8: B mediano estimado=0,00029561290712381465, obtido de picos acústicos arquivados do C5, Alexander Holm / Salamander Grand Piano v3 / CC BY 3.0, https://github.com/sfzinstruments/SalamanderGrandPiano, commit 3382bf9496bba2486f5ab0de55a264d1dfc38404. Não é dado C3X, não é medição individual de corda nem alvo homologado.
- Hipótese de auditoria: fio circular maciço, uniforme, homogêneo, tensionado, apoiado idealmente nas extremidades; modelo linear de corda rígida. Não aplicar a cordas enroladas, geometria real das terminações ou contato não linear.

## Equações SI

A=pi*d²/4 [m²]; I=pi*d⁴/64 [m⁴]; mu=rho*A [kg/m]; EI=E*I [N m²]; B=pi²*EI/(T*L²); f1=sqrt(T*(1+B)/mu)/(2L) [Hz]; tensão mecânica axial nominal sigma=T/A [Pa].

A hipótese maciça exige que massa e seção concordem. V10 mu=0,008640011278329232 kg/m, contra mu_geom=0,006577663726507621 kg/m. Excesso 31,3538003% em relação ao fio maciço; rho implícita=10311,2733 kg/m³. EI=0,011174398427346958 N m². Isso evidencia inconsistência entre hipóteses de geometria e massa, não erro de afinação do áudio V10: a rotina de afinação utiliza a massa derivada e produz sua própria frequência alvo. Se mu for interpretada como massa efetiva, deve-se explicitar e justificar a equivalência em vez de chamá-la massa física do fio.

| Cenário matemático | T (N) | f1 (Hz) | B |
|---|---:|---:|---:|
| Fio maciço com T inicial V10 | 702,631579 | 299,927455 | 0,000528449180 |
| Fio maciço com T equal V10 | 702,260274 | 299,848238 | 0,000528728586 |
| Fio maciço, d e L fixos, tensão recalculada para C4 | 534,543998 | 261,625565 | 0,000694620243 |
| Fio maciço, L fixo, f1 e B equal da V10 preservados; d resolvido | 407,017251 | 261,625565 | 0,000528728586 |

Na última linha d=0,901228139 mm, mu=0,005007593012 kg/m. Demonstra que é possível conservar as frequências teóricas sem manter todas as hipóteses geométricas originais; não significa conservar amplitudes, impedâncias, martelo, perdas ou timbre.

## Família inversa: não identificabilidade

Fixar E, rho, f1 e B não determina L, d e T unicamente. Para cada L positivo:
d²=64*rho*L⁴*f1²*B/(pi²*E*(1+B)); T=4*L²*rho*pi*d²/4*f1²/(1+B).
Logo d varia como L² e T como L⁶. Mesmo conjunto de frequências de parciais idealizados, diferentes massas e impedâncias. Exemplo: f1=261,6255653 Hz, B mediano C5, E/rho do código:

| L (m) | d (mm) | T (N) | mu (g/m) | sigma nominal (MPa) |
|---:|---:|---:|---:|---:|
| 0,450 | 0,459476 | 72,144277 | 1,301622 | 435,098 |
| 0,500 | 0,567254 | 135,752185 | 1,983877 | 537,158 |
| 0,545 | 0,673955 | 227,670004 | 2,800405 | 638,197 |
| 0,600 | 0,816846 | 405,353852 | 4,113768 | 773,507 |
| 0,650 | 0,958659 | 655,249868 | 5,666152 | 907,796 |

Valores hipotéticos, não selecionados por plausibilidade comercial ou resistência à ruptura; nenhuma carga autorizada para um piano real. Nenhuma inferência de comprimento C3X ou C5. A frequência do C4 foi nominalmente igualada para isolar o efeito de B.

## Testes

17/17 verificações executadas em ambiente JavaScript V8 antes de gravação: área, inércia, massa, reprodução B e mu V10, inconsistência, invariância EI, afinação, retensionamento, inversão, famílias distintas, leis de escala, validação de entradas. Reproduzir em checkout Node:
`node research/c3x-physical/c4-wire-consistency.test.mjs`
Sem nova execução de CI/hardware. Commits 9a883fb40799ce8a762d6d7bbdcbd8a0021e45e9 e 6a72ccc9ebbe7370879a431d8875d575ba9b3855.

**Decisão:** não retocar V10 ou copiar B do C5. Próximo F1.10: quantificar sensibilidade de f1 e B a incertezas independentes de L,d,T,E,rho, distinguir massa efetiva de massa geométrica e documentar quais medições eliminam a ambiguidade (priorizar L e d reais). Não prolongar pesquisas teóricas como se fossem medição C3X; manter bloqueio explícito de F1. Meta 32–64 vozes intacta, não homologada.
