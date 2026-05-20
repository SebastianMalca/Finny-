-- ═══════════════════════════════════════════════════════════════════════
-- FINNY — MySQL Schema (Migration 001)
-- Equivalente físico al MER lógico actualizado.
-- Base de datos: finny_db
-- Codificación: utf8mb4 / utf8mb4_unicode_ci
-- ═══════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS finny_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finny_db;

-- ── 1. USERS ──────────────────────────────────────────────────────────────────
-- Almacena credenciales. password_hash es VARCHAR(255) — NUNCA texto plano.
CREATE TABLE IF NOT EXISTS users (
    id            INT          NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL,
    username      VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,          -- bcrypt/PBKDF2 hash
    reset_token   VARCHAR(255)     NULL,          -- token de recuperación (URL-safe)
    reset_expires DATETIME         NULL,          -- expiración del token (UTC)
    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 2. PURCHASES ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS purchases (
    id         INT            NOT NULL AUTO_INCREMENT,
    user_id    INT            NOT NULL,
    name       VARCHAR(100)   NOT NULL,
    amount     DECIMAL(12, 2) NOT NULL,
    category   VARCHAR(50)    NOT NULL DEFAULT 'Other',
    created_at DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_purchases_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_purchases_user (user_id),
    INDEX idx_purchases_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 3. BUDGETS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    id             INT            NOT NULL AUTO_INCREMENT,
    user_id        INT            NOT NULL,
    monthly_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    month          VARCHAR(7)     NOT NULL,          -- YYYY-MM
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_user_month (user_id, month),
    CONSTRAINT fk_budgets_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_budgets_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 4. USER_PROFILES ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id         INT         NOT NULL AUTO_INCREMENT,
    user_id    INT         NOT NULL,
    name       VARCHAR(100)    NULL DEFAULT 'Joven',
    xp         INT         NOT NULL DEFAULT 0,
    level      INT         NOT NULL DEFAULT 1,
    avatar     VARCHAR(10)     NULL DEFAULT 'JV',
    tips_read  INT         NOT NULL DEFAULT 0,
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_profile_user (user_id),
    CONSTRAINT fk_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 5. STREAKS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS streaks (
    id                INT     NOT NULL AUTO_INCREMENT,
    user_id           INT     NOT NULL,
    current_streak    INT     NOT NULL DEFAULT 0,
    longest_streak    INT     NOT NULL DEFAULT 0,
    last_active_date  CHAR(10)    NULL,            -- YYYY-MM-DD
    total_active_days INT     NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_streak_user (user_id),
    CONSTRAINT fk_streaks_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 6. MISSIONS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS missions (
    id            INT             NOT NULL AUTO_INCREMENT,
    user_id       INT             NOT NULL,
    `key`         VARCHAR(50)     NOT NULL,
    title         VARCHAR(100)    NOT NULL,
    description   VARCHAR(255)    NOT NULL,
    icon          VARCHAR(10)         NULL DEFAULT '🎯',
    type          VARCHAR(50)     NOT NULL,
    target_value  DECIMAL(10, 2)      NULL DEFAULT 1.00,
    current_value DECIMAL(10, 2)      NULL DEFAULT 0.00,
    completed     TINYINT(1)      NOT NULL DEFAULT 0,
    reward_xp     INT             NOT NULL DEFAULT 50,
    completed_at  DATETIME            NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_user_mission_key (user_id, `key`),
    CONSTRAINT fk_missions_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_missions_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 7. ACHIEVEMENTS ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS achievements (
    id          INT         NOT NULL AUTO_INCREMENT,
    user_id     INT         NOT NULL,
    `key`       VARCHAR(50) NOT NULL,
    title       VARCHAR(100)    NOT NULL,
    description VARCHAR(255)    NOT NULL,
    icon        VARCHAR(10)         NULL DEFAULT '🏆',
    unlocked    TINYINT(1)  NOT NULL DEFAULT 0,
    unlocked_at DATETIME        NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_user_achievement_key (user_id, `key`),
    CONSTRAINT fk_achievements_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_achievements_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
