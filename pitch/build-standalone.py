#!/usr/bin/env python3
"""Gera a versão standalone do deck: embute assets/*.jpg em base64.

O `certifica-pitch.html` versionado referencia `assets/` (arquivos separados,
para o diff do git ficar legível). Para apresentar offline sem carregar a pasta
junto — sala de cliente, avião, enviar por e-mail — este script produz um HTML
único e autossuficiente.

    python3 pitch/build-standalone.py            # -> pitch/certifica-pitch.standalone.html
    python3 pitch/build-standalone.py /tmp/x.html

O resultado fica em ~850 KB e não faz nenhuma requisição externa.
"""
import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "certifica-pitch.html"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "certifica-pitch.standalone.html"

html = SRC.read_text()

# Bloco `const SHOTS = { chave: "assets/arquivo.jpg", ... };`
m = re.search(r"const SHOTS = \{(.*?)\n\};", html, re.S)
if not m:
    sys.exit("SHOTS block not found in certifica-pitch.html")

entries = re.findall(r'(\w+)\s*:\s*"([^"]+)"', m.group(1))
if not entries:
    sys.exit("no entries inside SHOTS")

lines = []
for key, rel in entries:
    path = HERE / rel
    if not path.exists():
        sys.exit(f"missing asset: {rel}")
    b64 = base64.b64encode(path.read_bytes()).decode()
    lines.append(f'  {key}: "data:image/jpeg;base64,{b64}"')

OUT.write_text(html.replace(m.group(0), "const SHOTS = {\n" + ",\n".join(lines) + "\n};"))
print(f"{OUT}  ({OUT.stat().st_size / 1024:.0f} KB, {len(entries)} images embedded)")
