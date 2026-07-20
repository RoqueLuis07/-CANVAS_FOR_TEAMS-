# 📚 USIL Gestión TI - Guía de Uso

Sistema integral de automatización y gestión para Canvas LMS y Microsoft Teams. Permite el alta unificada de usuarios, matrículas, control de asistencias, gestión de equipos y auditoría completa de forma masiva y automatizada.

🔗 **Producción (Live):** [https://canvasforteams-production.up.railway.app/](https://canvasforteams-production.up.railway.app/)

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.10+
- Credenciales de Canvas LMS (Token de Administrador)
- Credenciales de Microsoft Teams/Azure AD (App Registration con permisos Graph API)

### 1. Instalación

```bash
# Clonar o navegar al directorio del proyecto
cd -canvas_for_teams-

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo de configuración
cp .env.example .env
```

### 2. Configuración (.env)
Edita el archivo `.env` con tus credenciales:

```env
CANVAS_BASE_URL=https://usilparaguay.instructure.com
CANVAS_ACCESS_TOKEN=tu_token_de_canvas
CANVAS_ACCOUNT_ID=1

AZURE_TENANT_ID=tu_tenant_id
AZURE_CLIENT_ID=tu_client_id
AZURE_CLIENT_SECRET=tu_client_secret
INSTITUTIONAL_DOMAIN=tu_dominio.edu.py

SMTP_FROM=it@usil.edu.py

ADMIN_ALLOWED_EMAILS=admin1@usil.edu.py,admin2@usil.edu.py
```

> El envío de correos de credenciales se hace vía Microsoft Graph (`sendMail`), reutilizando las credenciales de Azure de arriba — no hace falta usuario/contraseña SMTP. Requiere el permiso de aplicación `Mail.Send` con consentimiento de administrador sobre el buzón indicado en `SMTP_FROM`.

> **Acceso al sistema:** solo los correos institucionales listados en `ADMIN_ALLOWED_EMAILS` (separados por coma) pueden iniciar sesión — cualquier otra cuenta de Azure AD del tenant (alumnos, docentes) queda bloqueada aunque se autentique correctamente contra Azure. Para dar de alta a un nuevo administrador de TI, agregá su correo a esa variable y reiniciá el servidor.

### 3. Ejecutar el Servidor

**Opción A: Script PowerShell (Recomendado en Windows)**
```powershell
.\run.ps1
```

**Opción B: Comando directo**
```bash
cd Backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 3000 --reload
```

El sistema estará disponible en: **http://localhost:3000** o **http://127.0.0.1:3000**

---

## 🏗️ Estructura del Proyecto

- **Frontend/**: Contiene la interfaz de usuario.
  - `templates/`: Plantillas HTML (Jinja2).
  - `static/`: Archivos estáticos (CSS, JS, imágenes).
- **Backend/**: Contiene el servidor y la lógica de negocio.
  - `app/`: Código fuente de la API (FastAPI, routers, modelos).
  - Persistencia en PostgreSQL (Supabase) — ver `SUPABASE_DATABASE_URL` en `.env`.
  - Archivos de configuración (`.env`, `requirements.txt`, etc.).

---

## 📖 Guía Completa de Uso

La plataforma ha sido optimizada para enfocarse **exclusivamente en procesos masivos y automatizados**, eliminando las funciones redundantes que Canvas o Teams ya ofrecen de forma nativa.

### 🏠 Página Principal (Dashboard)

**URL**: http://localhost:3000/ui/home

Es tu portal de entrada con acceso rápido a las funcionalidades principales:
- 🧑‍🎓 **Nuevo Ingreso (Alta Unificada)**
- 🎓 **Matriculaciones (Unificadas)**
- 📚 **Cursos (Canvas)**
- 🤝 **Equipos (Teams)**
- 📊 **Asistencias**
- 📋 **Historial de Trabajos**

---

## 🧑‍🎓 Nuevo Ingreso (Alta Unificada)

### ¿Para qué sirve?
Proceso masivo para dar de alta a nuevos alumnos y docentes simultáneamente en **Azure AD/Teams** y **Canvas LMS**, con generación automática de contraseñas y envío de credenciales por correo electrónico.

### Pasos para Usar:
1. Accede a **Directorio & Ingresos → Alta Unificada** (`/ui/ingreso`).
2. Descarga la plantilla Excel provista en la vista.
3. Completa el Excel con los datos: Nombre, Apellidos, Correo Personal, Cédula/DNI, Tipo (student/teacher), Sede, y Programa.
4. Sube el Excel al sistema.
5. Selecciona a qué correo enviar el reporte de ejecución (opcional) y si deseas enviar los correos de bienvenida a los usuarios automáticamente.
6. Haz clic en procesar. El sistema creará las cuentas en ambas plataformas y enviará los correos desde `it@usil.edu.py`.

---

## 🚫 Desvinculación Unificada (Egreso)

### ¿Para qué sirve?
Desactivar o eliminar cuentas de alumnos retirados o egresados de forma masiva en ambas plataformas para liberar licencias y mantener la seguridad.

### Pasos para Usar:
1. Accede a **Directorio & Ingresos → Egreso / Desvinculación** (`/egreso`).
2. Descarga la plantilla y llénala con los correos institucionales de los usuarios a desvincular.
3. Sube el Excel y el sistema procederá a suspender las cuentas en Azure AD y eliminarlas/desactivarlas en Canvas.

---

## 🎓 Matriculación Unificada

### ¿Para qué sirve?
Enrolar listas masivas de alumnos a sus respectivos **Cursos en Canvas** y añadirlos como miembros en sus **Equipos de Teams** de forma simultánea.

### Pasos para Usar:
1. Accede a **Matriculaciones** (`/ui/unified-enrollments`).
2. Descarga la plantilla Excel.
3. Llena el Excel especificando el ID de Canvas, el ID de Teams, y el correo institucional del usuario.
4. Carga el Excel y procesa.

---

## 🤝 Gestión de Equipos (Teams)

### ¿Para qué sirve?
Administrar de forma eficiente los Equipos de Microsoft Teams, con herramientas enfocadas en la adición masiva de miembros.

### Pasos para Usar:
1. Accede a **Equipos (Teams)** (`/ui/teams/teams`).
2. Selecciona un Equipo de la lista para ver sus detalles.
3. Puedes añadir miembros usando **Carga Múltiple (Excel)** o **Carga por Correos (Pegar lista de correos)**.
4. La adición individual y creación individual de Teams se han retirado para enfocarnos en procesos masivos (puedes crear Teams individuales directamente desde la app nativa de Teams).

---

## 📚 Gestión de Cursos (Canvas)

### ¿Para qué sirve?
Ver el listado de todos los cursos de Canvas, actualizar configuraciones de forma ágil y sincronizarlos con Teams.

### Pasos para Usar:
1. Accede a **Cursos (Canvas)** (`/ui/canvas/courses`).
2. Puedes buscar cursos y ver cuántos estudiantes tienen.
3. Usa la opción **Añadir miembros Excel** para procesar listas masivas.

---

## 📊 Reportes de Asistencia

### ¿Para qué sirve?
Descargar matrices de asistencia de todos los cursos de Canvas en Excel de forma organizada, sin tener que descargar archivos manualmente desde el correo que envía Canvas.

### Pasos para Usar:
1. Cada mes, descarga los reportes CSV crudos desde la herramienta "Attendance" de Canvas.
2. Guárdalos en la carpeta correspondiente (`Carpeta de plantillas/`).
3. Entra a **Asistencias** (`/ui/canvas/attendance`) y presiona "Refrescar".
4. El sistema compilará y formateará los datos, permitiéndote descargar un reporte en Excel limpio y listo para enviar a directivos.

---

## 📋 Historial de Trabajos (Jobs) - ⭐ Control Total

### ¿Para qué sirve?
Ver el resultado detallado de **TODAS** las operaciones masivas realizadas (altas, matrículas, desvinculaciones). Todo queda guardado de forma persistente.

### ¿Cómo usarlo?
1. Entra a **Historial Trabajos** (`/ui/jobs`).
2. Filtra por "Hoy", "Esta semana" o por operación específica (ej. "Alta Unificada").
3. Si subiste un Excel con 100 alumnos, aquí verás cuántos se crearon con **Éxito (✓)** y cuántos tuvieron **Errores (✗)**.
4. Puedes leer el mensaje de error exacto (ej. "El correo ya existe en Azure") para corregir el archivo y volver a intentarlo.

---

## 🔒 Auditoría y Logs

### ¿Para qué sirve?
Ver un registro completo (log) de quién hizo qué en el sistema. Registra todas las solicitudes HTTP, endpoints accedidos y usuarios responsables, ideal para control de seguridad y trazabilidad.

- Accede desde **Auditoría** (`/ui/audit`).

---

## 💾 Base de Datos

El sistema usa una única base **PostgreSQL en Supabase** (`SUPABASE_DATABASE_URL` en `.env`), con estas tablas principales:

1. **canvas_courses / canvas_users / canvas_enrollments** - Caché local de Canvas (sincronizada, no es la fuente de verdad).
2. **azure_users** - Caché local de usuarios de Azure AD/Teams.
3. **jobs** - Historial detallado de operaciones masivas (background jobs).
4. **audit_logs** - Log de auditoría de solicitudes.

Todos los datos se **persisten automáticamente** aunque el servidor se reinicie.

---

## 🛠️ Stack Técnico (Para Administradores)

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12 + FastAPI |
| **Servidor** | Uvicorn (ASGI) |
| **Integraciones** | Canvas LMS REST API v1, Microsoft Graph API |
| **Autenticación** | OAuth2, Graph API Tokens, envío de correo vía Microsoft Graph |
| **Base de Datos** | PostgreSQL (Supabase) |
| **Frontend** | Jinja2 Templates + Vanilla JS + Bootstrap 5.3 |
| **Despliegue** | Dockerizado para Railway (`railway up`) |

---

## ⚠️ Solución de Problemas Frecuentes

**1. "Error 403 al subir código a GitHub"**
Si usaste una cuenta diferente a la configurada en Windows, ve al "Administrador de Credenciales" de Windows, borra la credencial antigua de GitHub y vuelve a hacer `git push`.

**2. "Los correos de bienvenida no llegan"**
Verifica que `SMTP_FROM` en tu `.env` sea la cuenta institucional correcta (ej. `it@usil.edu.py`) y que la App Registration de Azure tenga concedido el permiso de aplicación `Mail.Send` (con consentimiento de administrador) sobre ese buzón.

**3. "No aparecen datos al subir el Excel de Nuevo Ingreso"**
Asegúrate de haber descargado la plantilla oficial desde el botón "Plantilla Excel" y no alterar los nombres de las cabeceras (columnas). Si falla, revisa el **Historial de Trabajos** para leer el error exacto.
