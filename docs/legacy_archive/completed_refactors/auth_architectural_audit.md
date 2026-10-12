# Auth Module Architectural Audit

**Date:** March 2026
**Target:** `app/modules/auth/`

## Executive Summary
The `auth` module provides the core identity management layer connected to Supabase. Like the previously assessed modules, it was built prior to the strict directory isolation and Domain-Driven Design constraints dictated by our new Architecture SOP. 

While the module isn't suffering from extreme monolith bloat (it handles only `User` models), it severely violates the structural layout, Single-Responsibility, and Object-Oriented Service rules.

## Discovered Architectural Violations

### 1. Flat Directory Structure
- **Problem:** All module scripts (`auth_models.py`, `auth_repository.py`, `auth_schemas.py`, `auth_service.py`, `role_types.py`) are placed in the root directory.
- **Target Fix:** Must be extracted into the standardized 4 sub-packages: `models/`, `schemas/`, `repositories/`, and `services/`.

### 2. Contamination of Models and Schemas
- **Problem:** Inside `auth_models.py`, there is a mix of SQLAlchemy table models (`User`, `UserBase`) directly alongside pure Pydantic response DTOs (`UserCreate`, `UserRead`, `UserPublic`).
- **Target Fix:** Table definitions must stay in `models/auth_models.py`, while the pure data-transfer definitions (`UserRead`, `UserCreate`, etc.) must be migrated into `schemas/auth_schemas.py`.

### 3. Functional Service Layer (Missing OOP)
- **Problem:** `auth_service.py` relies solely on raw un-encapsulated functional programming (`def get_user_by_username()`, `def link_employee_to_new_user()`). Each function directly manages its own database session.
- **Target Fix:** Wrap these global functions into an `AuthService` class. This is non-negotiable for adhering to the dependency injection design pattern enforced across the app's backend.

### 4. Constants Misplacement
- **Problem:** `role_types.py` effectively acts as the module's localized constants registry but uses a distinct filename.
- **Target Fix:** Rename `role_types.py` into a standardized `constants.py` file within the module root to maintain uniformity with other modules.

### 5. Missing Compatibility Facade
- **Problem:** The module is exposed randomly depending on caller imports.
- **Target Fix:** Instantiate the new `AuthService` inside `app/modules/auth/__init__.py`, then explicitly expose the 6 legacy method names to protect UI and downstream dependencies from breaking.
