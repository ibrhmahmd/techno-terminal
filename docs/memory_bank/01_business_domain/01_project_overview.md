# Project Context: Data Standardization Pipeline

## Origin

This project originated from a messy Workspace directory called `techno_data_ Copy` containing over 200 disconnected Excel files. The files represented attendance logs for a technical education / robotics center (like FLL, Robofest, WEDO, etc.), staff attendance sheets, and CRM data.

The primary goal of the project was to **standardize the data**, extract it from the wildly inconsistent Excel layouts, and push it into a clean, unified `Master_Database.xlsx` suitable for injection into a relational database (PostgreSQL/MySQL) and dashboard visualizations.

## Core Problem

The central problem was that the Excel files were filled out by human instructors using non-standardized templates. Key issues included:

- **No strict schema**: One sheet might say "Mobile", another "Phone", a third "رقم الهاتق".
- **Nested directories**: Data was scattered across folders like `courses 2/شهر مايو` (May) in both English and Arabic.
- **Pivot Tables vs Flat Data**: Attendance was marked horizontally (columns for each date showing '1', '✓', 'absent'), requiring unpivoting to hit a normalized `(student, date, status)` table.
- **Metadata Leakage**: Excel headers were often pushed down to Row 3, with Row 1 and Row 2 left for metadata like "Session Date" or "Course Name: Robotics".

## Project Evolution

The project evolved from a "file analysis" task into a 2-Phase ETL System:

### Phase 1: File Reorganization

We wrote heuristic-based Python scripts (`01_` through `05_`) to scan all Excel files, sample their contents, identify their business domain (CourseAttendance, StaffAttendance, CRM, Competition), and copy them into a clean `data/processed/_REORGANIZED` structure.

### Phase 2: Data Transformation (ETL)

We wrote `06_transform_data.py` to iterate over the reorganized folder. It executes the core mapping logic, handling the complex unpivoting of horizontal dates into vertical `attendance_date`, `attendance_status` relational records.

### Phase 3: Project Restructuring (Current)

As the codebase grew, we separated the logic from the data.

- Scripts moved to `src/`
- Raw user data moved to `data/raw/`
- Generated output moved to `data/processed/`
- Context moved to this Memory Bank `docs/memory_bank/`.

### Phase 4: Web Application & Database Design (Current)

Based on lessons learned from the messy Excel data, we are now designing a proper PostgreSQL-backed web application that will prevent unstructured data from ever accumulating again. The database schema (13 tables) was designed through multiple rounds of business rule clarification with the center's admin. Key decisions:

- **PostgreSQL** chosen over NoSQL for relational integrity and financial audit trails.
- **Sibling detection** via `sibling_group_id` column (Option C).
- **Competition categories** as proper tables linked to annual editions.
- **JSONB metadata columns** on 6 tables for future flexibility.
- **Business rules enforced at app level**, not database level (admin is always right).

## The Result

A robust Python pipeline that converts ~200 scattered, corrupted, and wildly varying Excel files into a single, clean Pandas DataFrame (which outputs to `Master_Database.xlsx`), achieving a 95% automated categorization rate and successfully normalizing ~17,791 rows of attendance data without human entry.
