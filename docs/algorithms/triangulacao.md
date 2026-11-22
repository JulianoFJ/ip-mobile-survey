# Triangulação entre quadros consecutivos

Código: `domain/geometry/triangulation.py` (domínio, testado) e `scripts/export_web_demo.py` (uso no golden). Fotos vizinhas: `scripts/fetch_neighbors.py`, manifesto `benchmarks/golden/panoramax-br-v0-vizinhos.yaml`.

## Por quê

A estimativa de quadro único tira a distância do ângulo do pé abaixo do horizonte, supondo chão plano. Ela falha quando o pé está escondido (carro, muro, vegetação) ou o chão tem rampa, e a altura herda o erro. Com o mesmo poste visto de duas ou três posições, a posição sai da interseção dos raios e a altura sai do ângulo do topo à distância triangulada.

## Como

1. **Raios:** cada detecção de poste é uma semirreta no chão. A origem é a posição da foto pelo GPS, num referencial local em metros. O rumo de mundo é o rumo do centro do panorama mais o azimute da detecção.
2. **Rumo do centro das vizinhas:** o rumo de deslocamento da vizinha menos a frente do veículo. A frente é a mesma medida na captura central, porque a câmera não se mexe no carro (ver [larguras](larguras-da-via.md)).
3. **Associação:** em cada vizinha, o raio que aponta para a posição de quadro único do poste, com tolerância de 3° ou do ângulo de 4 m laterais àquela distância (o que for maior).
4. **Interseção:** ponto de menor distância quadrática a todos os raios. É recusado quando:
   - o ângulo entre raios fica abaixo de 4° (raios quase paralelos);
   - o RMS passa de 1,5 m (raios de postes diferentes);
   - o ponto cai atrás de alguma câmera;
   - a distância fica fora de 2 a 60 m.
5. **Altura:** mediana de `h_câmera + distância × tan(elevação do topo)` entre os quadros. Vira limite inferior quando o topo está cortado em todos.

O valor de quadro único fica guardado em `unicoQuadro`, para comparar.

## Limitações

- Postes **sem o pé visível** não têm posição prévia para guiar a associação e ficam de fora nesta versão. Associar só por consistência entre raios é o próximo passo.
- As posições relativas vêm do GPS da câmera. Entre fotos a segundos de distância o erro é quase o mesmo e se cancela em boa parte, mas não totalmente; GNSS RTK resolve.
- Com fotos a cada 3 a 6 m, postes muito à frente no eixo da via dão raios quase paralelos e são recusados.

## Resultado no golden (21/11/2026)

68 capturas, 136 fotos vizinhas (mediana de 13,9 m entre fotos consecutivas). **205 postes triangulados**, 105 deles com 3 fotos.

**Validação com foto deixada de fora** (`scripts/eval_triangulation.py`): triangula com a captura central e uma vizinha, e prevê o rumo do poste na outra vizinha.

| Posição | Erro mediano de previsão | p75 |
|---|---|---|
| Quadro único | 3,84° | 6,75° |
| Triangulada | **3,29°** | 6,46° |

A triangulação acerta melhor em 142 de 261 pares (54%). **O ganho é real, mas modesto (−14%).** O limite é o GPS da câmera: a diferença de rumo entre os trechos anterior→central e central→seguinte tem mediana de 2,1° e p90 de 17°, parte por curva e parte por tremor do GPS. Com GNSS RTK o ganho deve ser bem maior. Vale repetir este teste nos primeiros dados com RTK.

**Contra a BDGD não dá para medir:** a posição triangulada e a de quadro único ficam a mediana de 12,7 m e 12,6 m do poste da BDGD mais próximo. A coordenada da BDGD é do desenho da rede e não serve de régua no nível de poucos metros. Por isso a validação acima é interna.

A posição triangulada passa a ser a usada quando existe. A de quadro único fica guardada em `unicoQuadro`.
