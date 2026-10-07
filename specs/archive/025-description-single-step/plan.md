# Implementation Plan - Single-Step Student Registration with Status

Transition the student creation flow from a multi-step sequence (creation followed by status update) to a single-step atomic transaction.

## User Review Required

- **Duplicate Checking (Same Name + DOB)**: A duplicate check is introduced during registration. If a student with the same full name (case-insensitive) and date of birth is already registered, the backend will reject with a `409 Conflict` error. This check is bypassed if the date of birth is not provided.
- **Redundant Table Cleanup**: We are completely removing code references to the deprecated `student_status_history` table and unifying all status tracking under the `student_activity_log` table.

## Proposed Changes

### Database Schema & Migration

#### [MODIFY] [40_functions.sql](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/db/schema/40_functions.sql)
* Update `update_waiting_since()` function to handle both `INSERT` and `UPDATE` operations:
  ```sql
  CREATE OR REPLACE FUNCTION update_waiting_since()
  RETURNS TRIGGER AS $$
  BEGIN
      IF TG_OP = 'INSERT' THEN
          IF NEW.status = 'waiting' THEN
              NEW.waiting_since = CURRENT_TIMESTAMP;
          END IF;
      ELSIF TG_OP = 'UPDATE' THEN
          IF NEW.status = 'waiting' AND (OLD.status IS NULL OR OLD.status != 'waiting') THEN
              NEW.waiting_since = CURRENT_TIMESTAMP;
          ELSIF NEW.status != 'waiting' AND OLD.status = 'waiting' THEN
              NEW.waiting_since = NULL;
              NEW.waiting_priority = NULL;
          END IF;
      END IF;
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;
  ```

#### [MODIFY] [50_triggers.sql](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/db/schema/50_triggers.sql)
* Update `trg_update_waiting_since` trigger on the `students` table to execute on `BEFORE INSERT OR UPDATE`.

#### [NEW] [077_update_waiting_since_trigger.sql](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/db/migrations/077_update_waiting_since_trigger.sql)
* Create a database migration script containing the updated function and trigger to be applied to the database.

---

### Backend Components

#### [MODIFY] [__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/interfaces/__init__.py)
* Add `get_by_name_and_dob` to `IStudentRepository`:
  ```python
  def get_by_name_and_dob(self, full_name: str, dob: datetime) -> Optional[Student]: ...
  ```

#### [MODIFY] [student_repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repositories/student_repository.py)
* Implement `get_by_name_and_dob` method returning an active student by case-insensitive name match and exact date of birth.
* Delete the `log_status_change` method completely.

#### [MODIFY] [student_schemas.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/schemas/student_schemas.py)
* Update `RegisterStudentDTO` status field to accept `Optional[StudentStatus] = None`.

#### [MODIFY] [student_crud_service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/services/student_crud_service.py)
* In `register_student()`, add duplicate check by name and birthdate:
  ```python
  if dob is not None:
      existing = self._uow.students.get_by_name_and_dob(command_dto.student_data.full_name, dob)
      if existing:
          raise ConflictError(f"Student with name '{command_dto.student_data.full_name}' and date of birth '{dob.date()}' already exists.")
  ```
* Resolve the status fallback (default to `StudentStatus.WAITING` if not provided).
* Call `self._activity_svc.log_status_change()` to record the initial status change from `None` to the selected status.
* Remove call to `self._uow.students.log_status_change` inside `update_status` and other methods.

---

### Frontend Components

#### [MODIFY] [inputs.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/api/crm/students/types/inputs.ts)
* Add `status?: StudentStatus` to the `CreateStudentDTO` interface.

#### [MODIFY] [useStudentActions.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/components/directory/hooks/useStudentActions.ts)
* Pass the `status` inside the `CreateStudentDTO` data payload to `createStudentMutation.mutateAsync({...data, status})`.
* Remove the secondary `updateStudentStatus` call block from `handleCreateStudent`.

#### [MODIFY] [QuickActionsGrid.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/components/dashboard/QuickActionsGrid.tsx)
* Pass the `status` inside the `CreateStudentDTO` payload in `createStudentMutation.mutateAsync({...data, status})`.
* Remove the secondary `updateStudentStatus` call block from `handleCreateStudent`.

---

## Verification Plan

### Automated Tests
* Run `npm run build` inside the UI workspace to ensure compile safety.
* (No backend automated tests will be run since we are operating in a production environment as instructed).

### Manual Verification
* Register a new student with status set to "Waiting" in a single action, and verify they appear immediately on the waiting list directory with the current date/time registered as their wait time.
* Register a student with the same name and date of birth as an existing student, and verify that the backend returns a `409 Conflict` error.
