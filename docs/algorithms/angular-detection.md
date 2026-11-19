# Detecções em ângulos e junção entre vistas

**Código:** `ipsurvey.domain.detection`, `ipsurvey.application.use_cases.detect_structures` · **Versão:** `angular_merge_v1`

## Método

1. O panorama é fatiado nas vistas de `view_ring` ([vistas planas](perspective-views.md)).
2. O detector (porta `Detector`) roda em cada vista e devolve caixas em pixels.
3. `to_angular` amostra a borda de cada caixa e devolve o envelope em (azimute, elevação), com o
   azimute do centro, a elevação do pé (`el_min`) e a do topo (`el_max`). Também registra quais
   bordas encostavam na borda da vista (`cut_bottom`, `cut_top`, `cut_side`).
4. `merge_detections` junta, por classe, as detecções que se sobrepõem em azimute (≥ 50% da mais
   estreita) e em elevação (ou com folga ≤ 2°), por transitividade. No objeto resultante:
   - o azimute vem da detecção com lados inteiros e maior score;
   - o pé vem da detecção com a menor elevação;
   - o topo vem da detecção com a maior elevação.

Isso resolve o poste alto e próximo, que nenhuma vista vê inteiro: a fileira do horizonte vê o pé
e a fileira inclinada vê a luminária.

## Testes

Panorama sintético com um poste em posição conhecida e um detector falso (pixels claros). O
resultado é um único poste, com azimute ±0,5° e pé e topo ±1°. Testado com poste alto (−20° a
+45°), poste na costura de ±180° e poste distante.

## Limitações

- Postes no mesmo azimute (um atrás do outro) viram um só. A triangulação em vários quadros separa.
- Braço e luminária são classes separadas. A associação luminária → poste fica para a etapa de
  medidas.
