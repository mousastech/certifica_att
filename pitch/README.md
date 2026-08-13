# Pitch deck

`certifica-pitch.html` — deck interno (EN) para posicionar o Certifica como
**asset reusável de Field Engineering**: uma plataforma multi-tenant de
preparação para certificações Databricks onde cada candidato ganha um tutor de
IA pessoal.

Abrir direto no navegador (nenhum servidor necessário). Navegação por
`↓`/`↑`/`PageUp`/`PageDown`/`Home`/`End`, ou scroll normal.

## Duas formas do mesmo deck

| | Arquivo | Imagens | Quando usar |
|---|---|---|---|
| **Versionada** | `certifica-pitch.html` (49 KB) | referencia `assets/*.jpg` | editar e revisar (o diff do git fica legível) |
| **Standalone** | gerada por `build-standalone.py` (~833 KB) | base64 embutido | apresentar offline, enviar por e-mail |

```bash
python3 pitch/build-standalone.py    # -> pitch/certifica-pitch.standalone.html
```

A standalone não faz **nenhuma requisição externa** (CSS inline, sem build, sem
CDN) — abre em qualquer navegador sem a pasta `assets/` ao lado.

Para trocar um screenshot: substitua o `.jpg` em `assets/` mantendo o nome, ou
edite o caminho na chave correspondente do objeto `SHOTS` (`program`,
`overview`, `practice`, `studyai`, `admin`, `activity`, `tabs`) — os `<img>` se
ligam a ele pelo atributo `data-shot`. Depois rode o script de novo.

Os JPEGs têm 1400px de largura (~2.4× o tamanho exibido), então ficam nítidos
em tela retina.

## ⚠️ Dados de cliente

Os prints de `/admin` e `/admin/activity` são do tenant real de um cliente. Os
**nomes, e-mails pessoais e IPs dos trainees foram difuminados em pixel**
(blur destrutivo, não overlay CSS — não há como reverter a partir do arquivo).
As métricas agregadas seguem legíveis, que é o que o slide precisa mostrar.

Se você regerar qualquer um desses dois prints a partir do app, **reaplique o
blur antes de embutir**.

## Conteúdo

14 slides: hero · elevator pitch · problema (4 vazamentos do funil) · o
programa · modelo de mastery por pessoa · as 5 abas · practice + mock exam
ponderado · study with AI · o loop de 5 passos de IA · grounding
anti-alucinação · telemetria para o sponsor · o que já entrega hoje ·
multi-tenant · o pedido.
