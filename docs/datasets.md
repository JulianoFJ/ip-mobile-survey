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

### panoramax-br-v0-vizinhos

São 136 fotos: a anterior e a seguinte, na sequência do Panoramax, de cada captura do `panoramax-br-v0`. Servem para a [triangulação](algorithms/triangulacao.md). Mesmos autores e mesma licença (CC BY-SA 4.0). Para baixar: `uv run python scripts/fetch_neighbors.py panoramax-br-v0`.

## Cadastro BDGD (via Ignis)

O adaptador `BdgdParquetCadastre` lê os parquets que o Ignis extrai da BDGD da ANEEL. Aceita várias pastas, em ordem (`IPSURVEY_BDGD_DIR`, separadas por `:`). Use a publicada (`app/cadastro_bdgd/data/cadastros`, com MG e MS) e a de trabalho local (`dados/bdgd/cadastros`), onde ficam os municípios extraídos sob demanda com `py -m cadastro_bdgd.extracao --remoto <IBGE>`.

- O arquivo é lido inteiro para a memória antes de abrir. Em pasta sincronizada pelo Google Drive, a leitura por trechos do pyarrow pega dados inválidos em arquivo recém-gravado.
- **DF:** a extração remota do Ignis não descobre a distribuidora de Brasília (não está no agregado do Hub). É preciso passar a base da Neoenergia Brasília direto para `extrair_remoto`.
