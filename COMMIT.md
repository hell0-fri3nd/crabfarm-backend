# COMMITS.md

# 1. Commit Principles

All commits must follow **Conventional Commits**.

Commits must be:

* Small and focused.
* Related to a single purpose.
* Easy to review.
* Easy to revert.
* Grouped by module or feature.

Avoid large commits that mix unrelated changes.

---

# 2. Conventional Commit Format

All commits must follow:

```text
<type>(<scope>): <description>
```

Example:

```text
feat(reservations): add room availability check

fix(auth): handle expired JWT tokens

refactor(guests): simplify guest query logic
```

---

# 3. Commit Types

Use the correct commit type:

| Type     | Usage                                           |
| -------- | ----------------------------------------------- |
| feat     | Add new functionality                           |
| fix      | Fix a bug                                       |
| refactor | Change code structure without changing behavior |
| perf     | Performance improvement                         |
| docs     | Documentation changes                           |
| style    | Formatting or styling changes only              |
| test     | Adding or updating tests                        |
| chore    | Tooling, dependencies, configuration            |
| build    | Build system changes                            |
| ci       | CI/CD changes                                   |
| revert   | Reverting a previous commit                     |
| chore    | changes/clean up                                |

---

# 4. Commit Scope Rules

The scope identifies the affected module or area.

Use feature/module names whenever possible.

Examples:

```text
feat(auth): create reservation workflow

feat(chat): add guest registration

fix(crabs): correct invoice calculation

refactor(prediction): simplify session validation
```

Rules:

* Scope must represent the main affected module.
* Do not use generic scopes like `update`, `changes`, or `misc`.
* If multiple modules are changed, split the commit whenever possible.

---

# 5. Commit Grouping Rules

Group commits based on related changes.

Good:

```text
feat(reservations): add reservation creation

feat(reservations): add reservation validation

test(reservations): add reservation service tests
```

Bad:

```text
feat: add reservations, fix auth, update dashboard, change database
```

A commit should not contain unrelated changes.

---

# 6. Module-Based Commit Strategy

Each feature should be committed by module.

Example:

## Reservation Feature

```text
feat(reservations): add reservation schema

feat(reservations): implement reservation service

feat(reservations): add reservation server action

test(reservations): test reservation workflow
```

## Authentication Feature

```text
feat(auth): add JWT login flow

fix(auth): refresh expired session handling

test(auth): add authentication tests
```

---

# 7. Commit Description Rules

Descriptions must:

* Use imperative mood.
* Be lowercase.
* Be concise.
* Explain the change.

Good:

```text
feat(rooms): add room availability query
```

Bad:

```text
feat(rooms): added some room stuff
```

Good:

```text
fix(payments): prevent duplicate invoice creation
```

Bad:

```text
fix: fixed bug
```

---

# 8. Breaking Changes

Breaking changes must be clearly marked.

Format:

```text
feat(api)!: change reservation response format
```

or:

```text
feat(api): change reservation response format

BREAKING CHANGE:
Reservation responses now return a nested data object.
```

---

# 9. Database Changes

Database changes must have their own commits.

Examples:

Schema changes:

```text
feat(database): add payment transaction model
```

Migration changes:

```text
chore(database): add reservation status migration
```

Rules:

* Never mix unrelated schema changes.
* Prisma migrations must be included with the related feature.
* Migration names must clearly describe the change.

---

# 10. Refactoring Rules

Refactoring commits must not include unrelated features.

Good:

```text
refactor(reservations): extract pricing calculation service
```

Bad:

```text
refactor: clean up reservation and add payment feature
```

---

# 11. Dependency Changes

Dependency updates must use:

```text
chore(dependencies): update package versions
```

For a dependency required by a feature:

```text
chore(auth): add authentication dependency
```

---

# 12. Pull Request Commit Rules

Before merging:

* Commits must follow Conventional Commits.
* Commits must have clear scopes.
* Related changes must be grouped together.
* Unrelated changes must be separated.
* Temporary commits should be squashed.

Avoid:

```text
fix
update
changes
wip
test123
```

---

# 13. Final Rule

A commit should answer:

1. What changed?
2. Which module changed?
3. Why does this commit exist?

A good commit tells a clear story of how the system evolved.
