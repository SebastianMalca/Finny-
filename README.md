# 💰 FINNY — Student Finance App v3.0

Aplicación de finanzas personal para estudiantes con **autenticación completa**, base de datos **MySQL**, arquitectura de **3 capas** y sistema de gamificación.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🔐 **Autenticación multi-usuario** | Login, registro y recuperación de contraseña |
| 🔒 **Contraseñas hasheadas** | Werkzeug Security (PBKDF2-SHA256) — nunca texto plano |
| 🛡️ **Rutas protegidas** | Flask-Login con sesiones seguras |
| 🗄️ **Base de datos MySQL** | Migrado desde SQLite — coherente con la documentación |
| 🏗️ **Arquitectura 3 capas** | Frontend · Backend (routes/services/repositories/models) · MySQL |
| 📊 **Dashboard completo** | Resumen de gastos diarios, semanales y mensuales por usuario |
| 🎮 **Gamificación** | XP, niveles, rachas, misiones y logros por usuario |
| 💡 **Consejos inteligentes** | Tips personalizados según el comportamiento del usuario |

---

## 🗂️ Arquitectura del Proyecto

```
FINNY/
├── backend/
│   ├── app.py              # Factory de Flask + registro de blueprints
│   ├── config.py           # Configuración MySQL, sesiones, tokens
│   │
│   ├── models/             # Capa de modelos (SQLAlchemy ORM)
│   │   ├── user.py         # User con password_hash VARCHAR(255)
│   │   ├── purchase.py
│   │   ├── budget.py
│   │   ├── profile.py
│   │   ├── streak.py
│   │   ├── mission.py
│   │   └── achievement.py
│   │
│   ├── repositories/       # Capa de acceso a datos
│   │   ├── user_repository.py
│   │   ├── purchase_repository.py
│   │   ├── budget_repository.py
│   │   ├── profile_repository.py
│   │   ├── streak_repository.py
│   │   ├── mission_repository.py
│   │   └── achievement_repository.py
│   │
│   ├── services/           # Capa de lógica de negocio
│   │   ├── auth_service.py     # register, login, reset password
│   │   ├── purchase_service.py
│   │   ├── budget_service.py
│   │   ├── profile_service.py
│   │   ├── gamification_service.py
│   │   ├── tips_service.py
│   │   └── dashboard_service.py
│   │
│   ├── routes/             # Capa de rutas (Flask Blueprints)
│   │   ├── auth_routes.py      # /auth/*
│   │   ├── purchase_routes.py  # /compras
│   │   ├── budget_routes.py    # /presupuesto
│   │   ├── stats_routes.py     # /estadisticas, /tendencia
│   │   ├── profile_routes.py   # /perfil
│   │   ├── gamification_routes.py
│   │   ├── tips_routes.py      # /consejos
│   │   └── dashboard_routes.py # /dashboard
│   │
│   └── utils/
│       ├── auth_decorators.py  # @login_required_json
│       └── validators.py
│
├── frontend/
│   ├── index.html          # UI con pantallas de login/registro
│   └── app.js              # Lógica JS con flujo de autenticación
│
├── transversal/
│   └── constants.py
│
├── migrations/
│   └── 001_init_mysql.sql  # DDL completo MySQL
│
├── docs/
│   ├── MER_logico.md       # Modelo Entidad-Relación lógico
│   ├── MER_fisico.md       # Modelo físico MySQL
│   └── diccionario_datos.md
│
└── requirements.txt
```

---

## ⚙️ Requisitos

- **Python 3.10+**
- **MySQL 8.x** (o MariaDB 10.5+)
- Un navegador moderno (Chrome, Firefox, Edge…)

---

## 🚀 Cómo ejecutar el proyecto

### 1. Crear la base de datos MySQL

```sql
CREATE DATABASE finny_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

O usa el script completo:
```bash
mysql -u root -p < migrations/001_init_mysql.sql
```

### 2. Configurar credenciales (opcional)

Por defecto se usa `root / root`. Para cambiarlo, define variables de entorno antes de iniciar:

```bash
set MYSQL_USER=tu_usuario
set MYSQL_PASSWORD=tu_contrasena
set MYSQL_DB=finny_db
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Iniciar el backend (Terminal 1)

```bash
python backend/app.py
```

Deberías ver:
```
==========================================================
  FINNY Finance App Backend v3.0  (MySQL + Auth)
  Server → http://localhost:5000
==========================================================
[DB] MySQL schema applied / verified.
```

### 5. Iniciar el servidor del frontend (Terminal 2)

```bash
python -m http.server 8080
```

### 6. Abrir la aplicación

Ve a: `http://localhost:8080`

Crea tu cuenta en la pantalla de registro y empieza a usar FINNY.

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

---

## 🛠️ Solución de problemas

### ❌ Error de conexión a MySQL
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) Can't connect to MySQL
```
→ Verifica que MySQL esté corriendo: `mysql -u root -p`  
→ Revisa las credenciales en `config.py` o variables de entorno.

### ❌ La base de datos no existe
```
Unknown database 'finny_db'
```
→ Ejecuta: `CREATE DATABASE finny_db;` en MySQL.

### ❌ ModuleNotFoundError
```
ModuleNotFoundError: No module named 'pymysql'
```
→ Ejecuta: `pip install -r requirements.txt`

### ❌ CORS Error en el navegador
→ Asegúrate de acceder desde `http://localhost:8080` (NO abrir el HTML directamente como `file://…`)  
→ Verifica que el backend esté corriendo en el puerto 5000.

---

## 📄 Licencia

Proyecto educativo de código abierto. Úsalo, modifícalo y compártelo libremente.

---

*Happy tracking with FINNY! 💰*