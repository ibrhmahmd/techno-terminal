# Auth Module Refactoring Plan

**Date:** March 2026

## Objective
To modernize and strictly structure the `auth` module by partitioning its file layout, encapsulating its functional service logic into an OOP class, perfectly separating Data Models from Pydantic Schemas, and securing UI compatibility through a seamless Facade.

## Refactoring Execution Steps (7-Phase SOP)

### Phase 1: Constants Restructuring
1. Rename [role_types.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/role_types.py) to [constants.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/shared/constants.py).
2. Update all internal imports referencing `role_types` to pull from `constants`.

### Phase 2: DTO Schema Design & Folders
1. Create standard module directories: `models/`, `schemas/`, `repositories/`, `services/`.
2. **Models:** Move [UserBase](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#11-23) and [User](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#24-33) (SQLModel table defs) into `models/auth_models.py`.
3. **Schemas:** Extract [UserCreate](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#34-38), [UserRead](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#39-45), and [UserPublic](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#47-57) out of the models file and place them cleanly inside `schemas/auth_schemas.py`, alongside the existing [PasswordResetBody](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_schemas.py#11-15).

### Phase 3 & 4: Data Layer Split (Repositories)
1. Relocate [auth_repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_repository.py) to `repositories/auth_repository.py`.
2. Generate [repositories/__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/analytics/repositories/__init__.py) to cleanly export all DB-level repository functions ([get_user_by_username](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#19-22), [create_user](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_repository.py#19-24), etc.).

### Phase 5: Business Logic Split (Services)
1. Relocate [auth_service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py) to `services/auth_service.py`.
2. **OOP Conversion:** Refactor [get_user_by_supabase_uid](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#13-17), [get_user_by_username](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#19-22), [update_last_login](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#24-28), [get_users_for_employee](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#30-33), [force_reset_password](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#35-51), and [link_employee_to_new_user](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py#53-97) into instance methods of a new `AuthService` class.

### Phase 6: Compatibility Facade 
1. Rewrite [app/modules/auth/__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/__init__.py).
2. Instantiate `AuthService` as a singleton-style variable (`_auth_svc = AuthService()`).
3. Explicitly alias the 6 legacy function names to the exact methods of `_auth_svc` so that all external imports (UI, Admin routers) continue to function identically.
4. Export the renamed [constants.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/shared/constants.py), the new [User](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#24-33) model, and all explicit DTOs natively from the [__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/__init__.py).
5. Finally, permanently delete the raw root files ([auth_models.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py), [auth_schemas.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_schemas.py), [auth_repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_repository.py), [auth_service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_service.py), [role_types.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/role_types.py)).

### Phase 7: UI Adapter Cleanup
Given that the Auth module mostly returns pure SQLModel instances ([User](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/auth_models.py#24-33)) which are inherently compatible with Streamlit and object dot-notation, the downstream UI breakage should be practically zero. We will audit any immediate downstream crashes or imports and patch them accordingly.

---
**Status:** Waiting on user approval to proceed into the Execution Mode.
