# Canvas for Teams – USIL Paraguay

Sistema de gestión de credenciales institucionales que integra **Canvas LMS** y **Microsoft Teams** para la Universidad San Ignacio de Loyola (USIL Paraguay).

---

## Índice

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [API Reference](./API.md)
- [Guía de Desarrollo](./DESARROLLO.md)

---

## Descripción General

La aplicación permite al departamento de TI gestionar el ciclo de vida de las cuentas de estudiantes y docentes:

| Función | Descripción |
|---|---|
| **Crear usuario** | Crea cuenta en Canvas y/o Azure AD (Teams) con credenciales generadas automáticamente |
| **Reenviar credenciales** | Reenvía el correo de bienvenida sin recrear la cuenta |
| **Verificar cuenta** | Comprueba si un usuario ya existe antes de intentar crearlo |
| **Carga desde planilla** | Crea múltiples usuarios desde una tabla web o archivo Excel |
| **Correo de bienvenida** | Envía email HTML personalizado según el tipo de programa (Grado, MBA, Diplomado) |

### Flujo Principal

```
Operador ingresa datos
        ↓
Generar credenciales (nombre + cédula → email + contraseña)
        ↓
Verificar si ya existe en Canvas / Teams
        ↓
Crear en Canvas LMS  →  Crear en Azure AD  →  Asignar licencia Teams
        ↓
Enviar correo de bienvenida (con PDFs adjuntos para diplomados)
```

---

## Arquitectura

```
app/
├── main.py                  # Aplicación FastAPI, monta todos los routers
├── core/
│   ├── config.py            # Settings (Pydantic BaseSettings, lee .env)
│   ├── database.py          # Caché local de Canvas/Azure (PostgreSQL/Supabase)
│   └── cache.py             # Cache en memoria simple
├── routers/
│   ├── ingreso.py           # ★ Core: crear/reenviar/verificar credenciales
│   ├── web.py               # Sirve plantillas HTML (SSR)
│   ├── auth.py              # Login/logout con Azure AD (OAuth2)
│   ├── canvas/              # Gestión de cursos, usuarios, matrículas
│   ├── teams/               # Gestión de teams y usuarios de Teams
│   ├── excel.py             # Importación/exportación de Excel
│   ├── sync.py              # Sincronización Canvas ↔ Teams
│   └── audit.py             # Registros de auditoría
├── services/
│   ├── canvas_client.py     # Cliente HTTP para Canvas LMS REST API v1
│   ├── teams_client.py      # Cliente Microsoft Graph API (MSAL)
│   ├── email_service.py     # Plantillas HTML + envío vía Graph sendMail
│   ├── credential_generator.py  # Genera login/email/contraseña desde nombre+cédula
│   └── auth.py              # JWT + sesiones con cookie HttpOnly
├── models/
│   └── canvas.py            # Modelos Pydantic compartidos (BulkResult, etc.)
├── templates/               # Jinja2 HTML
│   ├── base.html            # Layout base con sidebar
│   ├── ingreso.html         # ★ UI de gestión de credenciales
│   └── ...
└── static/
    └── templates/           # PDFs instructivos para diplomados
```

### Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | FastAPI + Uvicorn |
| Autenticación | Azure AD OAuth2 (MSAL) |
| Templates | Jinja2 (SSR) |
| Canvas | Canvas LMS REST API v1 |
| Teams | Microsoft Graph API v1 |
| Email | Microsoft Graph `sendMail` |
| Config | Pydantic BaseSettings + `.env` |

---

## Configuración

Crear archivo `.env` en la raíz del proyecto:

```env
# ── Canvas LMS ──────────────────────────────────────
CANVAS_BASE_URL=https://usilparaguay.instructure.com
CANVAS_ACCESS_TOKEN=<token de acceso de Canvas>
CANVAS_ACCOUNT_ID=1

# ── Azure AD / Microsoft Teams ──────────────────────
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
AZURE_SKU_STUDENTS=STANDARDWOFFPACK_STUDENT
AZURE_SKU_TEACHERS=STANDARDWOFFPACK_FACULTY

# ── Aplicación ──────────────────────────────────────
PORT=3000
ENVIRONMENT=development
SITE_URL=http://localhost:3000
SECRET_KEY=<clave-secreta-aleatoria>

# ── Dominio institucional ────────────────────────────
INSTITUTIONAL_DOMAIN=usil.edu.py
USAGE_LOCATION=PY

# ── Email (Microsoft Graph sendMail) ──────────────────
SMTP_FROM=resteche@usil.edu.py
```

El envío de credenciales usa la API de Microsoft Graph (`POST /users/{buzón}/sendMail`),
autenticada con las mismas credenciales de Azure AD (arriba) que ya se usan para Canvas/Teams
— no SMTP directo, y no depende de MFA ni de una contraseña de buzón. `SMTP_FROM` es el
único dato propio de email: el buzón desde el que se envía. El CC de cada correo depende del
tipo de programa y está fijo en `app/services/email_service.py` (ver también la hoja "CC Envío
Credenciales" del archivo `referencias_excel/USIL_Config_Referencia.xlsx`).

### Permisos Requeridos en Azure AD

La app registration de Azure necesita los siguientes **Application permissions** con admin consent:

| Permiso | Uso |
|---|---|
| `User.ReadWrite.All` | Crear y leer usuarios en Azure AD, liberar licencias al dar de baja |
| `GroupMember.ReadWrite.All` | Gestionar miembros de Teams |
| `Team.ReadBasic.All` | Leer equipos de Teams |
| `Mail.Send` | Enviar el correo de credenciales (desde el buzón SMTP_FROM) |

Permisos adicionales **no concedidos todavía**, requeridos por funciones de
`/reports/*` (ver `app/routers/reports.py`). Sin ellos, esos endpoints
responden 403 con instrucciones de cómo habilitarlos:

| Permiso | Uso | Endpoint que lo necesita |
|---|---|---|
| `AuditLog.Read.All` | Ver último inicio de sesión (`signInActivity`) | `GET /reports/inactive-teams-users` |
| `Reports.Read.All` | Reporte de actividad de Teams por usuario | `GET /reports/teams-activity` (además, desactivar "Reports concealment" en el Admin Center para ver nombres reales) |
| `Mail.Read` (o `Mail.ReadBasic.All`) | Confirmar en la carpeta Enviados si un correo realmente salió del buzón SMTP_FROM | `POST /reports/verify-email-sent` |

Para otorgarlos: Azure Portal → App Registrations → (la app) → API Permissions
→ Add a permission → Microsoft Graph → Application permissions → buscar y
agregar cada uno → **Grant admin consent**.

---

## Ejecución

### Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor con recarga automática
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Producción (servidor local)

```bash
# Sin recarga automática
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
```

### URLs Principales

| URL | Descripción |
|---|---|
| `http://localhost:3000/` | Dashboard principal |
| `http://localhost:3000/ui/ingreso` | **Gestión de credenciales** (requiere auth) |
| `http://localhost:3000/ui/login` | Inicio de sesión |
| `http://localhost:3000/docs` | Documentación interactiva de la API (Swagger) |
| `http://localhost:3000/diagnostics` | Estado de conexiones (Canvas + Azure) |
