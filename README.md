# 💰 FINNY — Student Finance App v3.0

Aplicación de finanzas personal para estudiantes con **autenticación completa**, base de datos **SQLite/PostgreSQL/MySQL**, arquitectura de **3 capas** y sistema de gamificación.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🔐 **Autenticación multi-usuario** | Login, registro y recuperación de contraseña |
| 🔒 **Contraseñas hasheadas** | Werkzeug Security (PBKDF2-SHA256) — nunca texto plano |
| 🛡️ **Rutas protegidas** | Flask-Login con sesiones seguras |
| 🗄️ **Base de datos flexible** | SQLite (demo) · PostgreSQL · MySQL — configurable por variable de entorno |
| 🏗️ **Arquitectura 3 capas** | Frontend · Backend (routes/services/repositories/models) · DB |
| 📊 **Dashboard completo** | Resumen de gastos diarios, semanales y mensuales por usuario |
| 🎮 **Gamificación** | XP, niveles, rachas, misiones y logros por usuario |
| 💡 **Consejos inteligentes** | Tips personalizados según el comportamiento del usuario |

---

## 🗂️ Arquitectura del Proyecto

```
FINNY/
├── api/
│   └── index.py            # Punto de entrada para Vercel (serverless)
│
├── backend/
│   ├── app.py              # Factory de Flask + registro de blueprints
│   ├── config.py           # Configuración DB, sesiones, tokens
│   │
│   ├── models/             # Capa de modelos (SQLAlchemy ORM)
│   ├── repositories/       # Capa de acceso a datos
│   ├── services/           # Capa de lógica de negocio
│   ├── routes/             # Capa de rutas (Flask Blueprints)
│   └── utils/
│
├── frontend/
│   ├── index.html          # UI completa (auth + dashboard)
│   └── app.js              # Lógica JS con detección automática de entorno
│
├── vercel.json             # Configuración de despliegue en Vercel
├── requirements.txt
└── .env.example            # Variables de entorno de referencia
```

---

## 🚀 Ejecutar localmente

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. (Opcional) Configurar variables de entorno

```bash
copy .env.example .env
# Editar .env con tu SECRET_KEY y DATABASE_URL si usas PostgreSQL/MySQL
```

### 3. Iniciar el backend

```bash
python backend/app.py
```

Deberías ver:
```
FINNY Finance App Backend v3.0
DB → sqlite:///G:\...\backend\finny.db
Server → http://localhost:5000
```

> Por defecto usa **SQLite** — no se necesita ninguna instalación extra.

### 4. Iniciar el frontend

```bash
python -m http.server 8080 --directory frontend
```

### 5. Abrir la aplicación

Ve a: `http://localhost:8080`

---

## ☁️ Despliegue en Vercel

### Opción A — CLI de Vercel (recomendada)

```bash
npm install -g vercel
vercel login
vercel
```

Vercel detectará automáticamente el `vercel.json` y desplegará:
- El **frontend** como archivos estáticos
- El **backend Flask** como Serverless Function en `api/index.py`

### Opción B — GitHub + Vercel Dashboard

1. Sube el proyecto a GitHub
2. Ve a [vercel.com](https://vercel.com) → **Add New Project**
3. Importa tu repositorio
4. En **Environment Variables** agrega:
   - `SECRET_KEY` → genera con: `python -c "import secrets; print(secrets.token_hex(32))"`
5. Click **Deploy**

### Variables de entorno en Vercel

| Variable | Requerida | Descripción |
|---|---|---|
| `SECRET_KEY` | ✅ Sí | Clave para sesiones Flask (PBKDF2) |
| `DATABASE_URL` | Opcional | URL de PostgreSQL/MySQL. Si no se define, usa SQLite |
| `FRONTEND_URL` | Opcional | URL del dominio custom para CORS |

> **⚠️ Nota sobre SQLite en Vercel**: Vercel usa filesystem efímero. Los datos en SQLite se pierden entre despliegues (funciona para demos). Para persistencia real usa **Neon** (PostgreSQL gratuito).

### Usar PostgreSQL con Neon (persistencia real)

1. Crea cuenta en [neon.tech](https://neon.tech) — gratis
2. Crea un proyecto y copia la **Connection String**
3. En Vercel → Environment Variables → agrega `DATABASE_URL` con el valor de Neon
4. Descomenta `psycopg2-binary` en `requirements.txt`

---

## 🔌 Endpoints de la API

### Autenticación (públicos)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/register` | Crear cuenta nueva |
| `POST` | `/auth/login` | Iniciar sesión |
| `POST` | `/auth/logout` | Cerrar sesión |
| `GET`  | `/auth/me` | Usuario autenticado actual |
| `POST` | `/auth/forgot-password` | Solicitar token de recuperación |
| `POST` | `/auth/reset-password` | Cambiar contraseña con token |

### Privados (requieren sesión activa)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/dashboard` | Resumen completo del dashboard |
| `GET` | `/compras` | Listar compras (`?category=`) |
| `POST` | `/compras` | Registrar una compra |
| `GET` | `/compras/<id>` | Obtener compra por ID |
| `DELETE` | `/compras/<id>` | Eliminar una compra |
| `GET` | `/estadisticas` | Estadísticas por categoría |
| `GET` | `/tendencia` | Tendencia de gasto (`?days=7`) |
| `GET` | `/presupuesto` | Presupuesto del mes actual |
| `POST` | `/presupuesto` | Guardar presupuesto mensual |
| `GET` | `/racha` | Estado de la racha diaria |
| `GET` | `/misiones` | Misiones con progreso |
| `GET` | `/logros` | Logros desbloqueados/bloqueados |
| `GET` | `/consejos` | Consejos personalizados |
| `POST` | `/consejos/leer` | Marcar consejo como leído (+5 XP) |
| `GET` | `/perfil` | Perfil del usuario |
| `PUT` | `/perfil` | Actualizar nombre o avatar |
| `GET` | `/categorias` | Categorías disponibles |
| `GET` | `/health` | Health check |

---

## 🛠️ Solución de problemas

### ❌ CORS Error en el navegador
→ Usa `http://localhost:8080` (NO abrir el HTML como `file://…`)  
→ Verifica que el backend esté corriendo en el puerto 5000.

### ❌ Datos no persisten en Vercel
→ SQLite en Vercel es efímero. Configura `DATABASE_URL` con Neon/PostgreSQL.

### ❌ ModuleNotFoundError en Vercel
→ Verifica que `requirements.txt` esté en la raíz del proyecto.

---

## 📄 Licencia

Proyecto educativo de código abierto. Úsalo, modifícalo y compártelo libremente.

---

*Happy tracking with FINNY! 💰*