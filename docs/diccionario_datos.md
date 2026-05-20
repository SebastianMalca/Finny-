# Diccionario de Datos — FINNY Finance App

> Actualizado para la versión 3.0 con autenticación multi-usuario y MySQL.
> Cada campo incluye: tipo físico MySQL, restricciones, descripción y reglas de negocio.

---

## Tabla `users`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria autoincremental | Generado por MySQL |
| `email` | `VARCHAR(255)` | NO | — | Dirección de correo electrónico | Único en la tabla; se almacena en minúsculas |
| `username` | `VARCHAR(100)` | NO | — | Nombre de usuario visible en la app | Mínimo 2 caracteres |
| `password_hash` | `VARCHAR(255)` | NO | — | Hash de la contraseña (PBKDF2-SHA256 via Werkzeug) | Nunca texto plano; mínimo 8 caracteres antes de hashear |
| `reset_token` | `VARCHAR(255)` | SÍ | NULL | Token URL-safe para recuperar contraseña | Generado con `secrets.token_urlsafe(32)` |
| `reset_expires` | `DATETIME` | SÍ | NULL | Expiración del token (UTC) | Expira en 1 hora desde la generación |
| `is_active` | `TINYINT(1)` | NO | `1` | Estado de la cuenta | `0` = desactivada; no puede iniciar sesión |
| `created_at` | `DATETIME` | NO | `NOW()` | Fecha y hora de registro | UTC; asignado automáticamente |

---

## Tabla `purchases`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` | CASCADE DELETE |
| `name` | `VARCHAR(100)` | NO | — | Nombre del gasto | Máximo 100 caracteres; requerido |
| `amount` | `DECIMAL(12,2)` | NO | — | Monto del gasto | Debe ser > 0; máx. 1,000,000 |
| `category` | `VARCHAR(50)` | NO | `'Other'` | Categoría del gasto | Valores: Food, Transport, Study, Entertainment, Health, Other |
| `created_at` | `DATETIME` | NO | `NOW()` | Fecha del registro | UTC |

---

## Tabla `budgets`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` | CASCADE DELETE |
| `monthly_amount` | `DECIMAL(12,2)` | NO | `0.00` | Presupuesto mensual asignado | Debe ser ≥ 0 |
| `month` | `VARCHAR(7)` | NO | — | Mes del presupuesto | Formato `YYYY-MM`; único por usuario |
| `created_at` | `DATETIME` | NO | `NOW()` | Fecha de creación | UTC |

---

## Tabla `user_profiles`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` (1:1) | UNIQUE; CASCADE DELETE |
| `name` | `VARCHAR(100)` | SÍ | `'Joven'` | Nombre visible en la app | Máximo 100 caracteres |
| `xp` | `INT` | NO | `0` | Puntos de experiencia acumulados | +5 XP por gasto; +50-500 por misión completada |
| `level` | `INT` | NO | `1` | Nivel actual calculado desde XP | `nivel = xp // 200 + 1` |
| `avatar` | `VARCHAR(10)` | SÍ | `'JV'` | Iniciales del avatar | Máximo 2 caracteres, en mayúsculas |
| `tips_read` | `INT` | NO | `0` | Contador de consejos leídos | Incrementa +1 en `POST /consejos/leer` |
| `created_at` | `DATETIME` | NO | `NOW()` | Fecha de creación | UTC |

---

## Tabla `streaks`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` (1:1) | UNIQUE; CASCADE DELETE |
| `current_streak` | `INT` | NO | `0` | Días consecutivos con actividad | Se resetea si se salta un día |
| `longest_streak` | `INT` | NO | `0` | Máxima racha histórica | Solo aumenta, nunca disminuye |
| `last_active_date` | `CHAR(10)` | SÍ | NULL | Última fecha con actividad | Formato `YYYY-MM-DD`; actualizado al registrar gasto |
| `total_active_days` | `INT` | NO | `0` | Total acumulado de días con actividad | Siempre incrementa |

---

## Tabla `missions`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` | CASCADE DELETE |
| `key` | `VARCHAR(50)` | NO | — | Identificador interno de la misión | Único por usuario |
| `title` | `VARCHAR(100)` | NO | — | Título visible | — |
| `description` | `VARCHAR(255)` | NO | — | Descripción de la misión | — |
| `icon` | `VARCHAR(10)` | SÍ | `'🎯'` | Emoji representativo | — |
| `type` | `VARCHAR(50)` | NO | — | Tipo de trigger de progreso | `expense_count`, `streak`, `category_count`, `tips_read`, `under_budget` |
| `target_value` | `DECIMAL(10,2)` | SÍ | `1.00` | Valor meta a alcanzar | — |
| `current_value` | `DECIMAL(10,2)` | SÍ | `0.00` | Progreso actual | Actualizado automáticamente al cumplir condición |
| `completed` | `TINYINT(1)` | NO | `0` | ¿Misión completada? | `1` cuando `current_value >= target_value` |
| `reward_xp` | `INT` | NO | `50` | XP otorgado al completar | Varía por misión: 30–500 XP |
| `completed_at` | `DATETIME` | SÍ | NULL | Fecha-hora de completación | UTC |

---

## Tabla `achievements`

| Campo | Tipo | Nulo | Default | Descripción | Regla de negocio |
|---|---|---|---|---|---|
| `id` | `INT` | NO | AUTO | Clave primaria | — |
| `user_id` | `INT` | NO | — | FK → `users.id` | CASCADE DELETE |
| `key` | `VARCHAR(50)` | NO | — | Identificador interno | Único por usuario |
| `title` | `VARCHAR(100)` | NO | — | Nombre del logro | — |
| `description` | `VARCHAR(255)` | NO | — | Descripción del logro | — |
| `icon` | `VARCHAR(10)` | SÍ | `'🏆'` | Emoji del logro | — |
| `unlocked` | `TINYINT(1)` | NO | `0` | ¿Logro desbloqueado? | `1` al cumplir condición |
| `unlocked_at` | `DATETIME` | SÍ | NULL | Fecha-hora de desbloqueo | UTC |

---

## Resumen de Types por Entidad

| Entidad | Registros iniciales | Scope |
|---|---|---|
| `users` | 0 (creados al registrarse) | Global |
| `user_profiles` | 1 por usuario | Por usuario (1:1) |
| `streaks` | 1 por usuario | Por usuario (1:1) |
| `budgets` | 1 por usuario por mes | Por usuario (1:N) |
| `purchases` | N por usuario | Por usuario (1:N) |
| `missions` | 9 por usuario (al registrarse) | Por usuario (1:N) |
| `achievements` | 8 por usuario (al registrarse) | Por usuario (1:N) |
