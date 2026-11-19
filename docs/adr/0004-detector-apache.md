# 0004: Detector com licença Apache (sem AGPL)

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto
Produto comercial servido via rede: AGPL obrigaria abrir o código (§15.3).

## Decisão
Detecção com RT-DETR (transformers), Detectron2 ou MMDetection; segmentação com SAM 2. **Ultralytics YOLO proibido** sem licença comercial.

## Consequências
`ultralytics` está banido no ruff (`banned-api`) e o job `licenses` falha com AGPL/SSPL.
