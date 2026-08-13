# Deploy — AT&T Certifica (fevm-moi-ai)

Plataforma **single-tenant AT&T**: plano de capacitação corporativa em Databricks
(trilhas por área/usuário, simulados, gamificação). App **`certifica-att`** no
workspace **fevm-moi-ai**, schema Lakebase dedicado **`certifica_att`**.

> Não altera o app `certifica` (Santander) — bundle, app e schema são separados.

## 0. Pré-requisito: autenticar

```bash
databricks auth login --host https://fevm-moi-ai.cloud.databricks.com --profile fevm-moi-ai
databricks current-user me --profile fevm-moi-ai   # confirma
```

## 1. Confirmar a instância Lakebase e o PGHOST

```bash
databricks database list-database-instances --profile fevm-moi-ai
```

- Anote o `read_write_dns` da instância (ex.: `ep-...database.us-east-2.cloud.databricks.com`).
- Se **não houver** instância, crie uma (Lakebase Postgres) e um role `certifica_app`
  com senha; o schema `certifica_att` é criado sozinho no 1º boot (DDL idempotente).
- Ajuste `backend/app.yaml` → `PGHOST` para o DNS confirmado (o valor atual é uma
  estimativa a partir das notas).

## 2. Criar o secret scope `certifica-att`

```bash
databricks secrets create-scope certifica-att --profile fevm-moi-ai 2>/dev/null || true
# JWT: qualquer string forte e estável
databricks secrets put-secret certifica-att jwt_secret \
  --string-value "$(openssl rand -hex 32)" --profile fevm-moi-ai
# Senha do role Postgres 'certifica_app' na instância Lakebase
databricks secrets put-secret certifica-att pg_password \
  --string-value "<SENHA_DO_certifica_app>" --profile fevm-moi-ai
```

## 3. Build do frontend + deploy do bundle

```bash
cd ~/projects/certifica-att
make build                              # vite build → backend/static/
cd backend
databricks bundle deploy --target moiai -p fevm-moi-ai
databricks bundle run certifica_att --target moiai -p fevm-moi-ai   # inicia o app
```

- O 1º boot roda o seed (`SEED_ON_STARTUP=true`): cria schema `certifica_att`, banco
  global de questões, tenant `att`, **8 trilhas** e **7 grupos** (CDO, CSO, Finanças-Genie,
  Eng. Dados, Ciência de Dados, Analistas, Liderança). Admin inicial:
  `moises.santos@databricks.com` / senha `Certifica@2026` (troque depois).

## 4. Depois do 1º seed — desligar o seed

Edite `backend/app.yaml` → `SEED_ON_STARTUP: "false"` e faça deploy de novo (evita reseed
a cada boot). O DDL continua rodando (idempotente) para novas tabelas.

## 5. Validar

```bash
databricks apps list --profile fevm-moi-ai | grep certifica-att   # pega a URL
```

Abra a URL → login AT&T → confira: trilhas por área, /ranking, e no Admin:
**Grupos**, **Trilhas** (visão por trilha) e **Importar planilha**.

## Notas

- LLM (geração de questões/IA) usa OBO — requer o scope `serving.serving-endpoints`
  na *User authorization* do app (já declarado em `databricks.yml`). Modelos padrão:
  `databricks-claude-sonnet-4-5` (+ `-haiku-4-5` para geração em massa). Ajuste em
  `app.yaml` se o workspace expõe outros endpoints (ex.: Opus 4.8).
- Custos: pausar a instância Lakebase quando não estiver em uso.
