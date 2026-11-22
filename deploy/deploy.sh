#!/usr/bin/env bash
# Publica o módulo no servidor de teste.
#   deploy/deploy.sh [usuario@servidor]
# Envia web/ (com os dados de demonstração de web/public/demo) por rsync, constrói a
# imagem no servidor e sobe o contêiner em 127.0.0.1:3100. Não mexe no Caddy.
set -euo pipefail
ALVO="${1:-ipsurvey@187.53.103.33}"
CHAVE="${IPSURVEY_SSH_KEY:-$HOME/.ssh/id_ed25519_ipsurvey}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$CHAVE" -o IdentitiesOnly=yes -o BatchMode=yes)

[ -f "$RAIZ/web/public/demo/campanhas.json" ] || {
  echo "Faltam os dados de demonstração: rode scripts/export_web_demo.py antes." >&2; exit 1; }

rsync -az --delete -e "${SSH[*]}" \
  --exclude node_modules --exclude .next --exclude '*.tsbuildinfo' \
  "$RAIZ/web" "$RAIZ/deploy" "$ALVO:~/ipsurvey/"
"${SSH[@]}" "$ALVO" 'cd ~/ipsurvey/deploy && docker compose up -d --build && docker compose ps'
