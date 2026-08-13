# Modelo de planilha — carga em lote de usuários (AT&T Certifica)

Use estes modelos para importar usuários em massa no painel **Admin → Importar planilha**.

- `modelo_usuarios_att.csv` — abre no Excel/Google Sheets.
- `modelo_usuarios_att.xlsx` — mesmo conteúdo, formato Excel.

## Colunas

| Coluna  | Obrigatória | Descrição |
|---------|-------------|-----------|
| `nome`  | sim         | Nome completo do colaborador. |
| `email` | sim         | E-mail corporativo (login). |
| `area`  | não         | Área/departamento (texto livre). |
| `grupo` | não         | **Chave** ou **nome** de um grupo existente (ex.: `cdo`, `cso`, `finanzas`, `data_eng`, `data_science`, `analistas`, `liderazgo`). Define a trilha personalizada que o usuário verá. |

Cabeçalhos aceitos em PT/ES/EN (ex.: `nome`/`nombre`/`name`, `grupo`/`ruta`/`rota sugerida`).

> Novos usuários recebem uma **senha inicial** (informada no momento do import) e trocam no
> primeiro acesso. E-mails já cadastrados apenas têm área/grupo atualizados.
>
> O mesmo modelo pode ser baixado direto do app (botões *Modelo CSV / Modelo XLSX*).
