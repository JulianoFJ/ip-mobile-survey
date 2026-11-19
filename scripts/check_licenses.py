"""Falha se alguma dependência de runtime tiver licença proibida (§15.3)."""

import json
import subprocess
import sys

FORBIDDEN = ("AGPL", "SSPL", "Affero")

out = subprocess.run(
    ["pip-licenses", "--format=json", "--with-system"], capture_output=True, text=True, check=True
).stdout
bad = [p for p in json.loads(out) if any(f in p["License"] for f in FORBIDDEN)]
for p in bad:
    print(f"PROIBIDO: {p['Name']} {p['Version']} ({p['License']})")
sys.exit(1 if bad else 0)
