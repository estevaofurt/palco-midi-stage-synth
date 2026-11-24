# Stage Concert Grand — F6.1 placa ortotrópica de referência

Data 24/11/2026. Base 245531befb1e2b15fb0350297b59351445b956fb. F6 em andamento. Pesquisa offline, sem alteração de main, V10, DSP, UI ou áudio. Não há acoplamento com a ponte nesta etapa; nenhum WAV.

## Fundamentação e escopo
Roteiro autoral blob 8c051340510084593f9361035fb784bb9ab7ee1d; F5.3 blob be37045882a81ad093d2bf96b2f4f5561d2d1e9a; exact-modal.mjs 5421be767601a96fab1e430453dc5e9b9ea1e2f1; polarized-bridge.mjs 2b5820bc5e2779ffd0c6983bcc4dc10f8f768719; V10 shared_mechanics.py 185f1e7824e6f5c31ff3039c4984cef11eb3c046 consultado e preservado.
Referências metodológicas: Chabassier et al., Time domain simulation of a piano. Part 1: model description, https://www.numdam.org/item/M2AN_2014__48_5_1241_0/ (placa ortotrópica espessa, heterogênea e amortecida Reissner-Mindlin, mais completa que a presente referência); Modal Analysis of Orthotropic Thin Rectangular Plate Based on Analytical and Finite Element Approaches, https://www.academia.edu/117950124/Modal_Analysis_of_Orthotropic_Thin_Rectangular_Plate_Based_on_Analytical_and_Finite_Element_Approaches (equações de Kirchhoff e modos simplesmente apoiados). Valores abaixo são hipóteses de projeto de madeira tipo spruce, não extraídos dessas referências como medidas nem de Yamaha. Não confundir retângulo sem nervuras com geometria de piano. Modelo linear de placa fina, material uniforme, fibras alinhadas aos eixos, bordas simplesmente apoiadas. Não inclui cisalhamento transversal, inércia rotatória, coroa, pré-tensão, nervuras, ponte ou radiação; validade em altas frequências não comprovada.

## Equações e parâmetros
Lx=1,4 m, Ly=1,1 m, espessura 0,008 m, rho=430 kg/m³, Ex=11 GPa, Ey=0,8 GPa, Gxy=0,65 GPa, nuXY=0,3, nuYX=nuXY*Ey/Ex=0,02181818. Rigidez de flexão D11=Ex*h³/(12*(1-nuXY*nuYX)), D22 análoga, D12=nuXY*D22, D66=Gxy*h³/12. Tensor positivo D11*D22>D12², D66>0. D11=472,42557345, D22=34,35822352, D12=10,30746706, D66=27,73333333 N m. Massa areal 3,44 kg/m², área 1,54 m², massa 5,2976 kg, massa modal 1,3244 kg.
w(x,y)=sum q_mn*sin(m*pi*x/Lx)*sin(n*pi*y/Ly); kx=m*pi/Lx, ky=n*pi/Ly. Frequência angular natural ao quadrado = (D11*kx^4+2*(D12+2D66)*kx²*ky²+D22*ky^4)/massa_areal; rigidez modal=m_modal*omega². Limite enumerativo derivado das parcelas positivas da frequência, verificado por enumeração 100x100 a 4 kHz. Força total sobre retângulo de largura dx,dy: peso=sin(kx*x0)*sin(ky*y0)*sinc(kx*dx/2)*sinc(ky*dy/2). Mesmo peso para projeção de deslocamento/velocidade e força generalizada. Perdas modais provisórias sigma=2+0,0005*omega [s^-1], c=2*m*sigma; não representam radiação. Integração local exata F2.2 sob força constante por passo, não acoplamento global. Perda calculada por diferença de trabalho e energia; monotonicidade e conservação verificadas separadamente. Mobilidade contínua entre portas Y_ab=sum i*omega*w_a*w_b/(K-m*omega²+i*omega*c). Não medição.

## Resultados
Primeiros modos (m,n): (1,1)=12.034311 Hz; (1,2)=22.730253 Hz; (2,1)=39.840742 Hz; (1,3)=42.540404 Hz; (2,2)=48.137243 Hz; (2,3)=64.861379 Hz; (1,4)=70.949434 Hz; (3,1)=86.715978 Hz; (2,4)=90.921013 Hz; (3,2)=94.055053 Hz. Frequência fundamental 12,03 Hz da placa ideal, não uma previsão confiável do primeiro modo de um piano completo.
| corte Hz | modos | flexibilidade pontual m/N | flexibilidade média de área m/N |
|---:|---:|---:|---:|
|250|27|1.389593113e-4|1.386943813e-4|
|500|59|1.403451693e-4|1.400373088e-4|
|1000|123|1.410327987e-4|1.406819002e-4|
|2000|253|1.413612046e-4|1.409701367e-4|
|4000|516|1.415216216e-4|1.410931147e-4|
|8000|1049|1.416036056e-4|1.411411898e-4|
|16000|2116|1.416435273e-4|1.411543744e-4|
Porta de ensaio x0=0,83 m, y0=0,46 m, dx=0,04 m, dy=0,025 m. Referência finita 16 kHz, 2116 modos. Em 4 kHz faltam 0.043399% de flexibilidade estática média; não garante convergência de mobilidade dinâmica nem radiação. Nenhum corte homologado. A banda superior da teoria de placa fina é apenas referência matemática.
Comparação espacial independente do modo (4,5) com autovalores de diferenças centrais (não solver de malha completo): 16 intervalos: -6.066765%; 32 intervalos: -1.547259%; 64 intervalos: -0.388753%; 128 intervalos: -0.097310%. Convergência de segunda ordem. Quadratura separável de ponto médio com 2048 intervalos por eixo: erro absoluto de peso 6.527286e-10. Primeira tentativa com 128 intervalos falhou a tolerância 1e-7, refinada sem alterar a fórmula nem tolerância. Mobilidade recíproca e parte real PSD verificadas em sete frequências de 50 a 4000 Hz; não varredura completa.

## Testes e decisão
16/16 verificações em V8, repetidas com leitura dos arquivos gravados. Tensor, massa, limite isotrópico, anisotropia, enumeração, contorno, quadratura, potência, silêncio, conservação, dissipação, trabalho, mobilidade, convergência estática e espacial, entradas inválidas. Reprodução: `node research/stage-concert-grand/orthotropic-plate.test.mjs`. Commits 7373ab2994d8128beefc2606abfd984cf95a969b e d585fbc29bcf1ded6da67456ac4ad08fc01ec686. Sem novo CI Node ou hardware.
F6.1 entregue. Próxima F6.2: nervuras como contribuição positiva de massa e rigidez na base espacial, verificar frequências e formas acopladas por problema generalizado de autovalores, convergência de base, efeito de reforço e massa separadamente; avaliar validade da placa fina, condições de borda e limitações de alta frequência. F6.3: acoplamento bidirecional da ponte F5 ao tampo, sem duplicar rigidez/perdas de apoio provisório, conservar energia e trabalho conjugado. F7 radiação, F8 primeiro WAV completo, F9 validação auditiva. F12/F13 e 32–64 vozes não homologados. Tampo deve ser compartilhado, não duplicado por nota. Nenhum aceite automático por contagem.
