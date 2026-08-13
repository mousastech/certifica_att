# Certifica

Plataforma **multi-tenant** de preparación para **certificaciones Databricks** —
simulacros con corrección y explicaciones, flashcards y generación de preguntas vía IA.
Vendible a múltiples clientes (tenants): cada empresa tiene su propio branding, sus
usuarios y sus resultados aislados, compartiendo un banco común de preguntas.

Basado en *gol-ml-certified-app* (a su vez inspirado en *Databricks Get CertifAIed*).
**Deploy actual: Databricks Apps** (host alternativo AWS documentado más abajo).
Disponible en **español, português e inglés** (selector de idioma en la UI).

- **Frontend** React + TypeScript + Vite → servido por el backend (SPA en `/static`)
- **Backend** FastAPI (Python) → **Databricks Apps**
- **Datos** Postgres → **Databricks Lakebase** (un schema, multi-tenant row-level)
- **LLM** generación de preguntas → **Databricks Foundation Model API** (Claude Opus 4.8)

---

## Modelo multi-tenant

Aislamiento **row-level**: el banco de preguntas (`certifications` / `questions` /
`flashcards`) es **global y compartido**; lo específico de cada cliente lleva `tenant_id`
(`users`, `test_sessions`, `test_answers`). El branding (color, logo, nombre) se aplica
**en runtime** por tenant, así que un solo build sirve a todos.

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
