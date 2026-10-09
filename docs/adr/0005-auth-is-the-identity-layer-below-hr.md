---
status: accepted
---

# auth is the identity layer at the bottom; hr sits above it

auth and hr imported each other:
- The `User` model imported `Employee`.
- hr imported `User` in seven places and wrote `users` rows directly.
- Logins were created in three places: `auth_service.invite_user`, `auth_service.link_employee_to_new_user` and `hr/staff_account_service.create_account`.

The FK graph settled it. About 40 audit FKs (`created_by`, `performed_by`) across every module point at `users`, and only `users.employee_id` points from auth to hr. So auth is the bottom module: it owns users, roles, the audit log, login and Supabase identity, and it never imports hr. hr owns employee records. "Give an employee a login" is an hr use case that calls one auth facade function, `provision_login(...)`. The three creation paths collapse into that one implementation, and the existing endpoints stay unchanged.

## Considered Options

- **Staff accounts move into auth, auth above hr**: rejected. `employees.created_by → users` would then point upward, and hr could not receive `User` or `UserRole` for audit fields.
- **Merge auth and hr into one identity module**: rejected. It would mix HR records with login and security code.
