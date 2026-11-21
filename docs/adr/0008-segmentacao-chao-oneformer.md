# 0008: Segmentação do chão com OneFormer (ADE20K) como linha de base

- **Status:** aceita (linha de base; revisar antes de uso comercial em produção)
- **Data:** 2026-11-21

## Contexto

As larguras da via (colunas S a Y e AI da planilha de simulação) não vêm do mapa: o OSM não tem largura em nenhuma das ruas do golden. É preciso separar pista, passeio, verde e veículo na imagem 360° e projetar no chão.

## Decisão

- Segmentador: **OneFormer Swin-L treinado no ADE20K** (`shi-labs/oneformer_ade20k_swin_large`). Código e pesos têm licença MIT. Ele separa "road", "sidewalk", "grass" e "car" com bordas limpas.
- Atrás de uma porta (`GroundSegmenter`), no extra opcional `vision`, como o detector.
- Comparado no mesmo panorama com o **CLIPSeg** (Apache-2.0): o CLIPSeg ficou grosseiro (352 px), não achou o passeio e borrou as bordas.

## Alternativas consideradas

- **SegFormer / Mask2Former treinados em Cityscapes ou Mapillary Vistas:** a licença dos pesos ou dos dados não permite uso comercial (NVIDIA Source Code License; CC BY-NC-SA).
- **SAM2 + Grounding DINO** (Apache-2.0): mais pesado e sem classes de chão prontas. Fica como opção para rotular dados próprios.

## Consequências

- Os **termos do ADE20K** são voltados a pesquisa e educação. Os pesos são MIT, mas o uso comercial de um modelo treinado nesses dados é zona cinzenta. Antes da produção: revisão jurídica, ou retreino com imagens próprias rotuladas (o fluxo de revisão da interface já produz parte desses rótulos).
- Leva cerca de 12 s por panorama (8 vistas de 1024 px) num Apple M3.
