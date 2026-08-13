# AT&T Certifica

**Plano de capacitação corporativa em Databricks** para a AT&T — **não** apenas
preparação para certificação. Cada **área/persona** (CDO, Ciberseguridad/CSO,
Finanças-Genie, Engenharia de Dados, Ciência de Dados, Analistas, Liderança) recebe
**trilhas personalizadas** de aprendizagem (cursos, hands-on, docs, vídeos) com
**simulados opcionais**, além de flashcards, geração de questões por IA, **gamificação**
(pontos/níveis/medalhas/ranking) e carga de usuários **em lote via planilha**. Pensada
para o **RH da AT&T** operar capacitação em massa.

Fork **single-tenant** de *Santander Certifica* (mantém o motor de simulados/IA por baixo,
exclusivo para a AT&T). Deploy em **Databricks Apps** (`certifica-att` em fevm-moi-ai).
UI em **português, español e inglés**.

- **Frontend** React + TypeScript + Vite → servido pelo backend (SPA em `/static`)
- **Backend** FastAPI (Python) → **Databricks Apps**
- **Dados** Postgres → **Databricks Lakebase** (schema dedicado `certifica_att`)
- **LLM** geração de questões/estudo → **Databricks Foundation Model API** (Claude)

Deploy: veja **[DEPLOY_ATT.md](DEPLOY_ATT.md)**. Modelo de planilha em **[templates/](templates/)**.

---

## Conceitos: grupos, trilhas e personalização

- **Trilha (track)** — percurso curado de aprendizagem: aulas (eLearning/hands-on/doc/vídeo)
  + simulados **opcionais**. Vive em `tenants.routes` (JSONB) com uma `key` estável.
- **Grupo (área/persona)** — tabela `groups`: recebe um conjunto de trilhas (`track_keys`)
  e, opcionalmente, simulados (`certification_ids`). Ex.: `cdo`, `cso`, `finanzas`.
- **Usuário** — pertence a um grupo (`users.group_key`) e pode ter trilhas extras
  (`users.extra_track_keys`). O que ele vê é resolvido em runtime
  (`services/groups.visible_tracks_for_user`).
- **Gamificação** — pontos derivados do progresso real (aulas concluídas + simulados +
  aprovações), com níveis, medalhas e ranking por área (`services/gamification`).

```
   Navegador  ──HTTPS──►  Databricks Apps (certifica-att)
                          ┌────────────────────────────────────────────┐
                          │ FastAPI ──serve──► SPA React (/static)       │
                          │   ├── SQL ──► Lakebase (schema certifica_att) │  grupos + trilhas + progresso
                          │   └── FMAPI ─► Claude                         │  geração de questões / estudo IA
                          └────────────────────────────────────────────┘
```

### Telas principais (admin/RH)
- **Grupos** (`/admin/grupos`) — cria áreas e escolhe quais trilhas/simulados cada uma vê.
- **Trilhas** (`/admin/trilhas`) — visão por trilha: matriculados, % de progresso, simulados, aprovações.
- **Importar planilha** — carga em lote (CSV/XLSX: `nome, email, area, grupo`).
- **Ranking** (`/ranking`) — gamificação, aberto a todos os usuários.

---

## (Legado) Modelo multi-tenant

> A AT&T Certifica é **single-tenant** (tenant fixo `att`). A base multi-tenant abaixo
> permanece no motor, mas as telas de plataforma/seleção de empresa foram removidas.

```
   Navegador  ──HTTPS──►  Databricks Apps
                          ┌───────────────────────────────────────┐
                          │ FastAPI ──sirve──► SPA React (/static)  │
                          │   ├── SQL ──► Lakebase (schema certifica)│  row-level por tenant_id
                          │   └── FMAPI ─► Claude Opus 4.8           │  generación de preguntas
                          └───────────────────────────────────────┘
```

### Tres niveles de acceso (áreas administrativas)

| Rol | Dónde | Qué hace |
|---|---|---|
| **Operador / superadmin** | Consola **`/platform`** (login en el tenant `platform`) | Gestiona **clientes (tenants)**: crear, suspender/activar, link "Acceder" a cada entorno. Gestiona **operadores** (otros usuarios administrativos del console: crear / listar / quitar). |
| **Admin del tenant** | Panel **`/admin`** (login en su tenant) | Gestiona **los usuarios de su empresa**: alta manual, editar nombre/área, cambiar contraseña, suspender/activar, eliminar. Ve el seguimiento (intentos, puntajes) y exporta PDF/CSV. |
| **Usuario final (trainee)** | App del tenant (`/t/<slug>`) | Hace simulacros, flashcards, ve su historial. Puede auto-registrarse si el tenant lo permite. |

> Un **operador** es simplemente un usuario del tenant interno `platform`. Cualquiera que
> inicie sesión en `platform` es superadmin del console. El env `SUPERADMIN_EMAILS` solo
> siembra el primer operador.

### Cómo entra cada quien
- **Cliente nuevo**: `/signup` (self-service, crea tenant + su primer admin) o lo crea un operador desde `/platform`.
- **Usuarios de un tenant**: van a `/` (Landing → escriben el slug de su empresa) o directo a `/t/<slug>` → login branded.
- **Operadores**: `/platform`.

---

## Banco de preguntas (global, compartido)

608+ preguntas y 200 flashcards (`backend/seed/seed_data.json`):

| Certificación | Preguntas | Flashcards |
|---|---|---|
| Data Engineer Associate | 100 | 40 |
| Data Engineer Professional | 100 | 40 |
| Data Analyst Associate | 110 | 40 |
| Machine Learning Associate | 100 | 40 |
| Machine Learning Professional | 98 | 40 |
| Generative AI Engineer Associate | 100 | 0 |

---

## Desarrollo local (mock, sin Databricks)

```bash
make install
make dev-backend      # terminal 1 — http://localhost:8005
make dev-frontend     # terminal 2 — http://localhost:3006
```

Con `MOCK_MODE=true` (default) el backend lee de `seed/seed_data.json` y "Generar vía IA"
produce preguntas sintéticas locales (sin llamar al LLM).

---

## Deploy en Databricks Apps (actual)

```bash
databricks auth login --profile fe-vm-serverless-stable-cvpomp
```

1. **Lakebase**: crear una instancia y habilitar PG native login.
   ```bash
   databricks database create-database-instance certifica-db --capacity CU_1 -p <profile>
   databricks database update-database-instance certifica-db enable_pg_native_login --enable-pg-native-login -p <profile>
   ```
   Crear el usuario Postgres del app (`certifica_app`) con contraseña y `GRANT` sobre el schema `certifica`.

2. **Secrets** (scope del app): `jwt_secret` (`openssl rand -hex 32`) y `pg_password`.
   El `app.yaml` los referencia con `valueFrom` (no van en git).

3. **Seed** (crea schema multi-tenant + banco global + tenant `platform` + 1er cliente):
   ```bash
   cd backend && python -m seed.seed_db   # con .env apuntando a Lakebase
   ```

4. **Deploy**: `make deploy-dev` (build Vite → `backend/static` + `databricks bundle deploy` + `run`).

El backend sirve SPA y API en el mismo origin; el LLM usa la identidad del app (FMAPI),
sin secretos. El JWT del app viaja en `X-Santander-Auth` (el gateway de Databricks Apps
consume `Authorization` para su propio OAuth). Auth a Postgres por **native login**
(`certifica_app` + `pg_password`).

---

## Deploy en AWS (host alternativo)

`db.py` soporta RDS (`PGPASSWORD` o token IAM) y el repo trae `backend/Dockerfile`
(App Runner), `amplify.yml` (frontend) y `make deploy-backend` (ECR). El frontend usa
`VITE_API_BASE_URL` para apuntar al backend cuando viven en orígenes distintos. Ver
`backend/.env.example` y `frontend/.env.example`.

---

## Estructura

```
certifica/
├── Makefile                       ← dev local + seed + deploy-dev/prod (Databricks Apps)
├── amplify.yml                    ← build spec frontend (host alternativo AWS)
├── backend/
│   ├── app.yaml                   ← config del Databricks App (command + env + secrets)
│   ├── databricks.yml             ← Asset Bundle (targets dev/prod)
│   ├── Dockerfile                 ← imagen App Runner (host alternativo AWS)
│   ├── seed/seed_db.py            ← schema multi-tenant + banco global + tenants (make seed)
│   └── app/
│       ├── main.py                ← FastAPI + sirve SPA desde /static
│       ├── config.py              ← Settings (MOCK_MODE, Lakebase/RDS, LLM, JWT, superadmins)
│       ├── db.py                  ← Postgres: native login | Lakebase OAuth | RDS (IAM)
│       ├── auth/                  ← JWT (tenant_id + roles) + bcrypt + WorkspaceClient (FMAPI)
│       ├── services/              ← tenants, users, repo, test_service, llm_gen, pdf_report
│       └── api/                   ← tenants(+platform), certifications, tests, generate, auth, tracking
└── frontend/
    └── src/
        ├── i18n/                  ← es / pt / en + selector de idioma
        ├── context/               ← Auth + Theme (branding runtime) + i18n
        └── pages/                 ← Landing, Login, Signup, Home, CertDetail, PracticeTest,
                                      Flashcards, History, Admin, AdminUser, Platform
```

---

## Estado

- Multi-tenant row-level con branding runtime + i18n (es/pt/en).
- Consola `/platform`: gestión de tenants + operadores.
- Panel `/admin`: gestión completa de usuarios del tenant + seguimiento + export PDF/CSV.
- LLM Claude Opus 4.8 validado. UI y reporte PDF traducidos.

> **Santander** queda como uno de los tenants de ejemplo — el producto no es específico de
> ningún cliente.
