# 0007: Interface web na pilha do Ignis

- **Status:** aceita
- **Data:** 2026-11-21

## Contexto

Este projeto vai virar um módulo do Ignis, a plataforma de IP da Houer: a ferramenta de análise dos resultados da inspeção de campo. A especificação (§4) previa React + TypeScript + Vite, com Marzipano/Pannellum para o 360°.

Já a versão web do Ignis (repositório HouerIgnis, `apps/web` e `packages/ui`) usa Next.js 15 (App Router), React 19 e Tailwind 3. Ela tem design system próprio (`@apphouer/ui`, com tokens de cor, Material Symbols, Radix, MapLibre e deck.gl) e os mapas de fundo Carto e Esri, sem chave.

## Decisão

- `web/` usa **as mesmas versões** do Ignis: Next.js 15.5, React 19.1, Tailwind 3.4, MapLibre 5.6 com react-map-gl 8, TanStack Query 5, Radix e Material Symbols.
- As rotas ficam em `src/app/(portal)/inspecao/…`. Na integração, essa pasta entra como está no `apps/web` do Ignis, na seção "Diagnóstico (DTO)".
- Um subconjunto do `@apphouer/ui` foi **copiado sem alteração** para `web/src/ui/`: tokens, CSS base, preset do Tailwind, Ícone, Botão, Cartão de KPI e Selo. Cada arquivo diz de onde veio. Na integração, os imports passam a ser do pacote e a pasta some.
- A casca (`componentes/Casca.tsx`) imita a casca do portal e some na integração.
- O panorama é desenhado como imagem equirretangular com sobreposição SVG, nas mesmas contas do domínio Python (`web/src/dados/geometria.ts`, testado). Um visualizador 360° imersivo pode vir depois. O Ignis já tem three.js.
- Os dados chegam pela camada `web/src/dados/api.ts`, com tipos em `tipos.ts`. Hoje ela lê JSON estáticos gerados por `scripts/export_web_demo.py`. Depois passa a ler da API FastAPI, sem mudar as telas.

## Alternativas consideradas

- **Vite + React Router (a especificação):** é mais leve, mas a integração obrigaria a reescrever rotas e casca.
- **Usar o `@apphouer/ui` como dependência:** é um pacote de workspace de repositório privado. Exigiria acesso no CI e acoplaria os dois repositórios antes da hora.

## Consequências

- A especificação §4 passa a ler "Next.js" no lugar de "Vite" (este ADR prevalece).
- Enquanto não houver integração, mudanças nos tokens do Ignis precisam ser copiadas à mão para `web/src/ui/tokens.css`.
- As revisões (confirmar ou rejeitar) ficam no navegador até existir a API. Por isso há "Exportar revisões" em JSON.
