# MER Físico — FINNY Finance App

> Modelo físico de la base de datos **MySQL 8.x** con tipos de datos reales, índices y claves foráneas.
> Generado a partir del schema en [`migrations/001_init_mysql.sql`](file:///g:/FINNY/migrations/001_init_mysql.sql).

---

## Tabla: `users`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK, AUTO_INCREMENT | Identificador único |
| `email` | `VARCHAR(255)` | NO | — | UNIQUE | Email del usuario |
| `username` | `VARCHAR(100)` | NO | — | — | Nombre de usuario |
| `password_hash` | `VARCHAR(255)` | NO | — | — | Hash PBKDF2-SHA256 de la contraseña |
| `reset_token` | `VARCHAR(255)` | SÍ | NULL | — | Token de recuperación de contraseña |
| `reset_expires` | `DATETIME` | SÍ | NULL | — | Expiración del token (UTC) |
| `is_active` | `TINYINT(1)` | NO | `1` | — | Estado de la cuenta |
| `created_at` | `DATETIME` | NO | `CURRENT_TIMESTAMP` | — | Fecha de registro |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (email)`, `INDEX (email)`

> [!CAUTION]
> `password_hash` es `VARCHAR(255)` — si en algún UML antiguo aparece como `INT`, ese UML estaba **incorrecto**. Un hash de contraseña es texto, nunca un número.

---

## Tabla: `purchases`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK → users.id | Propietario del gasto |
| `name` | `VARCHAR(100)` | NO | — | — | Nombre del gasto |
| `amount` | `DECIMAL(12,2)` | NO | — | — | Monto en moneda local |
| `category` | `VARCHAR(50)` | NO | `'Other'` | — | Categoría del gasto |
| `created_at` | `DATETIME` | NO | `CURRENT_TIMESTAMP` | — | Fecha de registro |

**Índices**: `PRIMARY KEY (id)`, `INDEX (user_id)`, `INDEX (created_at)`  
**FK**: `ON DELETE CASCADE` — al eliminar el usuario se eliminan sus compras.

---

## Tabla: `budgets`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK → users.id | Propietario del presupuesto |
| `monthly_amount` | `DECIMAL(12,2)` | NO | `0.00` | — | Monto mensual |
| `month` | `VARCHAR(7)` | NO | — | UNIQUE(user,month) | Formato `YYYY-MM` |
| `created_at` | `DATETIME` | NO | `CURRENT_TIMESTAMP` | — | Fecha de creación |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (user_id, month)`, `INDEX (user_id)`

---

## Tabla: `user_profiles`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK, UNIQUE | Propietario (1:1 con users) |
| `name` | `VARCHAR(100)` | SÍ | `'Joven'` | — | Apodo en la app |
| `xp` | `INT` | NO | `0` | — | Puntos de experiencia |
| `level` | `INT` | NO | `1` | — | Nivel actual |
| `avatar` | `VARCHAR(10)` | SÍ | `'JV'` | — | Iniciales (máx. 2 letras) |
| `tips_read` | `INT` | NO | `0` | — | Contador de consejos leídos |
| `created_at` | `DATETIME` | NO | `CURRENT_TIMESTAMP` | — | Fecha de creación |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (user_id)`

---

## Tabla: `streaks`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK, UNIQUE | Propietario (1:1 con users) |
| `current_streak` | `INT` | NO | `0` | — | Racha actual en días |
| `longest_streak` | `INT` | NO | `0` | — | Mejor racha histórica |
| `last_active_date` | `CHAR(10)` | SÍ | NULL | — | Última fecha de actividad (YYYY-MM-DD) |
| `total_active_days` | `INT` | NO | `0` | — | Total de días activos |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (user_id)`

---

## Tabla: `missions`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK → users.id | Propietario |
| `key` | `VARCHAR(50)` | NO | — | UNIQUE(user,key) | Código interno de la misión |
| `title` | `VARCHAR(100)` | NO | — | — | Título visible |
| `description` | `VARCHAR(255)` | NO | — | — | Descripción |
| `icon` | `VARCHAR(10)` | SÍ | `'🎯'` | — | Emoji |
| `type` | `VARCHAR(50)` | NO | — | — | Tipo de trigger (`expense_count`, `streak`, …) |
| `target_value` | `DECIMAL(10,2)` | SÍ | `1.00` | — | Meta numérica |
| `current_value` | `DECIMAL(10,2)` | SÍ | `0.00` | — | Progreso actual |
| `completed` | `TINYINT(1)` | NO | `0` | — | ¿Completada? |
| `reward_xp` | `INT` | NO | `50` | — | XP a otorgar |
| `completed_at` | `DATETIME` | SÍ | NULL | — | Fecha de completación |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (user_id, key)`, `INDEX (user_id)`

---

## Tabla: `achievements`

| Columna | Tipo MySQL | Nulo | Default | Clave | Descripción |
|---|---|---|---|---|---|
| `id` | `INT` | NO | — | PK | Identificador |
| `user_id` | `INT` | NO | — | FK → users.id | Propietario |
| `key` | `VARCHAR(50)` | NO | — | UNIQUE(user,key) | Código interno |
| `title` | `VARCHAR(100)` | NO | — | — | Título visible |
| `description` | `VARCHAR(255)` | NO | — | — | Descripción |
| `icon` | `VARCHAR(10)` | SÍ | `'🏆'` | — | Emoji |
| `unlocked` | `TINYINT(1)` | NO | `0` | — | ¿Desbloqueado? |
| `unlocked_at` | `DATETIME` | SÍ | NULL | — | Fecha de desbloqueo |

**Índices**: `PRIMARY KEY (id)`, `UNIQUE (user_id, key)`, `INDEX (user_id)`

---

## Diagrama de Relaciones Físicas

```
users (PK: id)
  ├── user_profiles.user_id  (FK, UNIQUE — 1:1)
  ├── streaks.user_id         (FK, UNIQUE — 1:1)
  ├── purchases.user_id       (FK — 1:N, CASCADE DELETE)
  ├── budgets.user_id         (FK — 1:N, CASCADE DELETE)
  ├── missions.user_id        (FK — 1:N, CASCADE DELETE)
  └── achievements.user_id   (FK — 1:N, CASCADE DELETE)
```
