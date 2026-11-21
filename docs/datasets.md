# Bases de dados e licenças

| Base | Licença | Uso permitido |
|---|---|---|
| Panoramax (`panoramax-br-v0`) | CC-BY-SA 4.0 | Avaliação visual de detecção em vias brasileiras; sem rótulos |
| Mapillary | CC-BY-SA 4.0 | Detecção/associação; não usar para métricas de precisão |
| Amsterdam Open Panorama | verificar termos | Reconstrução, posição vs. registro municipal |
| KITTI-360 | CC BY-NC-SA 3.0 | **Só P&D** |
| Toronto-3D / Paris-Lille-3D | verificar | Teste da extração geométrica |

## Golden datasets

Os manifestos ficam em `benchmarks/golden/`. As imagens não entram no git:

```bash
uv run python scripts/fetch_datasets.py panoramax-br-v0           # baixa para data/
uv run python scripts/fetch_datasets.py panoramax-br-v0 --verify  # só confere os hashes
```

### panoramax-br-v0

Tem 68 panoramas 360° equirretangulares de vias urbanas de 17 cidades brasileiras. Foram escolhidos à mão por terem postes, braços e luminárias visíveis. A maioria tem 5760×2880 e foi feita com GoPro Max no teto de um carro, a cerca de 1,9 m do chão. O autor de cada imagem está no manifesto. Para redistribuir, é preciso citar o autor e manter a licença CC BY-SA 4.0.

O nadir mostra o capô do carro e uma faixa com logotipo, abaixo de cerca de −60°. As vistas de detecção não chegam até lá.
