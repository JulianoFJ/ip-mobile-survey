# Interface web: inspeção de campo

É o módulo do Ignis para analisar os resultados da inspeção de campo de iluminação pública. Ele cobre o envio dos arquivos, o mapa dos resultados, a revisão das detecções e o relatório. A pilha e o visual são os mesmos do portal, para a integração ser só mover a pasta de rotas (ver [ADR 0007](../docs/adr/0007-web-pilha-do-ignis.md)).

## Rodar

```bash
# 1. Dados de demonstração: golden dataset + resultados do detector
uv run python scripts/fetch_datasets.py panoramax-br-v0
uv run --extra vision python scripts/eval_zero_shot.py run panoramax-br-v0    # ~20 s por panorama
uv run --extra vision python scripts/export_web_demo.py panoramax-br-v0       # → web/public/demo/

# 2. Interface
cd web && pnpm install && pnpm dev   # http://localhost:3100
```

Para verificar: `pnpm typecheck` e `pnpm test`.

## Telas

| Rota | O que faz |
|---|---|
| `/inspecao` | Lista de inspeções e as etapas do módulo |
| `/inspecao/nova` | Assistente: identificação, equipamento (altura da câmera), envio dos arquivos com conferência no navegador (formato 2:1 e GPS no EXIF) e resumo do processamento |
| `/inspecao/[id]` | Painel: indicadores, mapa com capturas e postes estimados (Carto e Esri), filtro por cidade, prévia da captura |
| `/inspecao/[id]/revisao` | Panorama com as caixas; confirmar ou rejeitar cada detecção (atalhos de teclado); aba **Via e malha** com a planta, onde se corrigem as larguras arrastando o meio-fio |
| `/inspecao/[id]/relatorio` | Relatório para imprimir ou salvar em PDF, e os postes em CSV |

## Ainda não ligado

- O envio ao servidor e o processamento dependem da API de ingestão.
- As revisões (decisões e larguras corrigidas) ficam no navegador; o botão "Exportar revisões" baixa um JSON. As larguras corrigidas são os rótulos para retreinar o segmentador (ADR 0008).
- A planilha de inspeção `.xlsx` já existe no Python (`ipsurvey exportar-planilha`), mas ainda não é servida.
- O confronto com o cadastro depende da issue #14.
