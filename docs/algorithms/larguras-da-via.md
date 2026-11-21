# Larguras da via pela imagem 360°

Código: `domain/extraction/cross_section.py` e `scripts/eval_cross_section.py`.

1. **Vistas de chão:** 8 vistas de 1024 px, FOV de 100°, inclinadas 30° para baixo. A 10 m da câmera, cada pixel cobre cerca de 0,1 m.
2. **Segmentação:** OneFormer (ADR 0008), com as classes do ADE20K reduzidas a pista, passeio, verde, veículo e outros.
3. **Grade do chão:** células de 0,1 m de x = −20 a +20 m e de y = −10 a +15 m, no referencial do deslocamento. Cada célula recebe o rótulo da vista onde cai mais perto do centro. Embaixo do próprio carro conta como pista.
4. **Corte transversal:** em cada fatia de y = −6 a +10 m, as faixas a partir do carro.
   - Veículo conta como pista: carro estacionado ocupa a faixa de estacionamento.
   - Faixas com menos de 0,4 m são ruído e se juntam à vizinha.
   - Canteiro é o que fica entre a pista do carro e outra pista, até 15 m. Pode ter várias faixas e mureta (outros com até 2 m).
   - A medida final é a mediana das fatias. Só vale com pelo menos 30% das fatias.

## Frente do veículo

O `view:azimuth` do Panoramax supõe que o centro da imagem é a frente do veículo. Na GoPro Max do golden, a frente fica **a +90°** do centro: o para-brisa aparece desse lado, e a planta só sai com a rua na vertical com esse giro.

Por isso a frente é **medida** em cada panorama: o eixo principal das células de pista num anel de 3 a 10 m dá a direção, e o padrão da câmera (+90° na GoPro Max) desempata o sentido. Quando o eixo é fraco (anisotropia abaixo de 2, típico de cruzamento), vale o padrão da câmera, e a medida sai marcada como "provável cruzamento".

O rumo do centro da imagem é o **rumo de deslocamento** (fotos vizinhas na sequência) **menos a frente**. Isso corrige também a posição dos postes no mapa, que antes saía girada.

## Limitações

- Chão plano: rampa e meio-fio alto distorcem.
- Passeio central (U, V), ciclovia e estacionamento (Z a AC) não são separados pelo ADE20K.
- Em cruzamento, a "pista" inclui a via transversal.
