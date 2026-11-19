# Vistas planas a partir do panorama 360°

**Código:** `ipsurvey.domain.geometry.perspective` · **Versão:** `persp_views_v1`

## Por quê

Detectores (OWLv2, Grounding DINO, RT-DETR) são treinados em fotos comuns. Na projeção
equirretangular, as linhas retas se curvam e o topo da imagem fica esticado, justamente onde estão
braços e luminárias. Por isso cada panorama é fatiado em vistas planas, a detecção roda em cada
vista e o resultado volta para **ângulos (azimute, elevação)**, que são a moeda comum do pipeline
(triangulação, altura, associação).

## Método

- Câmera virtual pinhole apontada para (yaw, pitch), com FOV horizontal e pixels quadrados.
- Pixel da vista → raio → (azimute, elevação) → (u, v) no panorama → amostragem bilinear. A costura
  em ±180° é contínua.
- Conjunto padrão (`view_ring`): 8 azimutes × pitch 0° e 35°, FOV 75°, 1024 px. São 16 vistas por
  panorama. Garantias testadas: todo objeto de até 20° de largura cabe inteiro em alguma vista do
  horizonte, e a cobertura vertical chega a 70° de elevação.

## Testes

- Centro da vista = eixo óptico; bordas a ±FOV/2; ida e volta pixel ↔ ângulo (hypothesis).
- Renderização comparada com um panorama analítico (erro ≤ 2 níveis de cinza), inclusive na costura.
- Um ponto marcado no panorama aparece na vista onde a projeção prevê (±3 px).

## Limitações

- Sem modelo de lente: assume o panorama já costurado pela câmera (Insta360 Studio/SDK).
- Custo de 16 vistas por quadro: medir na S4. Pode cair com seleção de vistas pelo lado da via.
