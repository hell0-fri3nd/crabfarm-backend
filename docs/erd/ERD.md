# CrabFarm Database Design

## Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐
│      users       │       │      batch       │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ name             │       │ created_at       │
│ email        (U) │       │ user_id (FK) ────┼─── users.id
│ password         │       └────────┬─────────┘
│ pin              │                │
│ role             │                │
│ created_at       │       ┌────────┴─────────┐
│ updated_at       │       │    crab_logs     │
└────────┬─────────┘       ├──────────────────┤
         │                 │ id (PK)          │
         │                 │ batch_id (FK) ───┼─── batch.id
         ├─────────────────┼── crab_id (FK)   │
         │                 │ type             │
         │                 │ width            │
         ├─────────────────┼── user_id (FK)   │
         │                 │ created_at       │
         │                 └──────────────────┘
         │
┌────────┴─────────┐       ┌──────────────────┐
│   scheduler      │       │      chat        │
│   settings       │       │    sessions      │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ type             │       │ user_id (FK) ────┼─── users.id
│ scheduler_type   │       │ status           │
│ hour             │       │ created_at       │
│ seconds          │       │ updated_at       │
│ is_enabled       │       └────────┬─────────┘
│ created_at       │                │
│ user_id (FK) ────┼─── users.id    │
└──────────────────┘       ┌────────┴─────────┐
                           │  chat_messages   │
┌──────────────────┐       ├──────────────────┤
│ activity_logs    │       │ id (PK)          │
├──────────────────┤       │ session_id (FK) ─┼─── chat_sessions.id
│ id (PK)          │       │ role             │
│ activity_type    │       │ content          │
│ description      │       │ created_at       │
│ value            │       └──────────────────┘
│ created_at       │
│ user_id (FK) ────┼─── users.id
└──────────────────┘

┌──────────────────┐
│ sensor_logs      │
├──────────────────┤
│ id (PK)          │
│ sensor_type      │
│ status           │
│ value            │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      crab        │
├──────────────────┤
│ id (PK)          │
│ name        (U)  │
│ group_by         │
└──────────────────┘
```

---

## Tables

### `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `name` | `VARCHAR(150)` | NOT NULL |
| `email` | `VARCHAR(254)` | UNIQUE, NOT NULL |
| `password` | `CHAR(60)` | NOT NULL |
| `pin` | `CHAR(60)` | NOT NULL |
| `role` | `CHAR(6)` | NOT NULL |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |

---

### `crab`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `name` | `VARCHAR(50)` | UNIQUE, NOT NULL |
| `group_by` | `VARCHAR(10)` | NOT NULL |

---

### `batch_crab`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |
| `user_id` | `INTEGER` | FK → `users.id`, NOT NULL |

---

### `crab_logs`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `batch_id` | `INTEGER` | FK → `batch_crab.id` |
| `crab_id` | `INTEGER` | FK → `crab.id`, NOT NULL |
| `type` | `ENUM('prediction', 'actual')` | NOT NULL |
| `width` | `DECIMAL(10,2)` | |
| `weight` | `DECIMAL(10,2)` | |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |
| `user_id` | `INTEGER` | FK → `users.id`, NOT NULL |

**Indexes:**
- `idx_crab_logs_id` on `id`
- `idx_crab_logs_type` on `type`

---

### `sensor_logs`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `sensor_type` | `ENUM('temperature', 'turbidity', 'ph', 'tds', 'ammonium', 'do')` | NOT NULL |
| `status` | `ENUM('NORMAL', 'WARNING', 'DANGER')` | |
| `value` | `DECIMAL(10,2)` | |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |

**Indexes:**
- `idx_sensor_logs_id` on `id`

---

### `activity_logs`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `activity_type` | `ENUM('sensors', 'auth', 'crab_logs', 'scheduler')` | NOT NULL |
| `description` | `VARCHAR(100)` | |
| `value` | `DECIMAL(10,2)` | |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |
| `user_id` | `INTEGER` | FK → `users.id`, NOT NULL |

---

### `scheduler_settings`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` | PK, auto-increment |
| `type` | `ENUM('feeding', 'valve')` | NOT NULL |
| `scheduler_type` | `ENUM('daily', 'weekly', 'monthly', 'custom')` | NOT NULL |
| `hour` | `INTEGER` | default: 0 |
| `seconds` | `INTEGER` | default: 0 |
| `is_enabled` | `BOOLEAN` | default: false |
| `created_at` | `TIMESTAMP` | default: `CURRENT_TIMESTAMP` |
| `user_id` | `INTEGER` | FK → `users.id`, NOT NULL |

---

### `chat_sessions`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `VARCHAR(36)` | PK |
| `user_id` | `INTEGER` | FK → `users.id` |
| `status` | `ENUM('active', 'ended')` | NOT NULL, default: 'active' |
| `created_at` | `DATETIME` | NOT NULL, default: `now()` |
| `updated_at` | `DATETIME` | NOT NULL, default: `now()` |

**Indexes:**
- `user_id`

---

### `chat_messages`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `VARCHAR(36)` | PK |
| `session_id` | `VARCHAR(36)` | FK → `chat_sessions.id`, NOT NULL |
| `role` | `ENUM('user', 'assistant')` | NOT NULL |
| `content` | `TEXT` | NOT NULL |
| `created_at` | `DATETIME` | NOT NULL, default: `now()` |

**Indexes:**
- `ix_chat_messages_session_id` on `session_id`

---

## Relationships

| From | To | Type |
|------|----|------|
| `crab_logs.user_id` | `users.id` | Many-to-One |
| `crab_logs.crab_id` | `crab.id` | Many-to-One |
| `crab_logs.batch_id` | `batch_crab.id` | Many-to-One |
| `activity_logs.user_id` | `users.id` | Many-to-One |
| `scheduler_settings.user_id` | `users.id` | Many-to-One |
| `chat_sessions.user_id` | `users.id` | Many-to-One |
| `chat_messages.session_id` | `chat_sessions.id` | Many-to-One |
| `batch_crab.user_id` | `users.id` | Many-to-One |


