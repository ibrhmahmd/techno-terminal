# Technical Report: Data Standardization Project
**Organization:** Techno Education Center
**Generated:** 2026-02-25 00:06
**Pipeline mode:** Full Execute

---

## 1. Executive Summary

This report documents the automated analysis, classification, and reorganization of **201 Excel files** found in the `techno_data_ Copy` directory. The pipeline successfully classified **95.0%** of files into structured business domains, exceeding the 95% acceptance threshold.

---

## 2. Current State Analysis

### 2.1 File Distribution Statistics

| Metric | Value |
|---|---|
| Total files scanned | 338 |
| Valid Excel files (.xlsx/.xls/.xlsm) | 201 |
| Temp/lock files excluded (~$*) | 136 |
| Other non-Excel files | 1 |
| Unreadable/corrupt files | 8 |
| Total worksheets found | 795 |
| Total data rows (all sheets) | 14299 |

### 2.2 Original Folder Structure

```
techno_data_ Copy/
├── CRM/                          (1 file — SAT.xlsx)
├── Esraa/                         (6 files + 7 subdirectories)
│   ├── 8mon/                      (day-of-week course registers)
│   ├── Meeting Recordings/        (4 Robofest sub-categories + 1 video)
│   ├── ROBOFEST SHEETS/           (competition Excel files)
│   ├── fll sheets/                (FLL competition file)
│   ├── شهر مايو/ (May)            (monthly course registers)
│   ├── شهر يونيو/ (June)          (monthly course registers)
│   └── شهر7/ (Month 7)            (monthly course registers)
├── attendance/                    (8 day-of-week attendance files)
└── courses 2/                     (active courses + Old Courses archive)
    ├── Old Courses/               (monthly archives: Mar-Oct 2024)
    │   ├── FLL/                   (8 FLL monthly files)
    │   ├── AAFFIAT/               (specialized sub-course)
    │   ├── Codeavour/             (competition)
    │   └── [Month YYYY] folders   (March–October 2024)
    └── Robofest 2025/             (Robofest 2025 files)
```

### 2.3 Key Observations

- **Naming inconsistency**: Files use day abbreviations (`fri.xlsx`), course+time slots (`CSS L1 Fri 11-2.xlsx`), and month names in both English and Arabic
- **Arabic folder names**: `شهر مايو`, `شهر يونيو`, `شهر7` represent monthly groupings and must be handled with UTF-8 encoding
- **Temp lock files**: 165-byte `~$*.xlsx` files (Excel lock files) are present in nearly every folder — excluded from migration
- **Deep nesting**: Up to 4 levels of subfolder depth; some single-file folders (e.g., `fll sheets/`)
- **Duplicate content**: SHA-256 hashing identifies any files with identical content across folder locations

---

## 3. Discovered Data Patterns

### 3.1 Business Domain Classification

| Domain | File Count | Classification |
|---|---|---|
| CourseAttendance | 189 | 94.0% |
| Unclassified | 10 | 5.0% |
| StaffAttendance | 1 | 0.5% |
| CRM_SAT | 1 | 0.5% |

### 3.2 Top Schema Patterns

The following recurring column fingerprints were identified across the file collection:

**Pattern 1** — 213 files sharing this column structure:
```
  Columns: 
  Examples: attendance\tuesday.xlsx::Sheet1; attendance\tuesday.xlsx::Sheet2
```

**Pattern 2** — 133 files sharing this column structure:
```
  Columns: age, fee_paid, grade, mobile, month_paid, name, s2, s3, s4, s5 ...
  Examples: courses 2\Old Courses\Junior Electronics fri 2-4.xlsx::Sheet1; courses 2\Old Courses\spike fri2-4.xlsx::Sheet2
```

**Pattern 3** — 53 files sharing this column structure:
```
  Columns: age, fee_paid, grade, mobile, month_paid, name, s2, s3, s4, s_1
  Examples: courses 2\Old Courses\AAFFIAT\AAFFIAT December.xlsx::Fri 11-2; courses 2\Old Courses\AAFFIAT\AAFFIAT December.xlsx::Wed 4-6
```

**Pattern 4** — 32 files sharing this column structure:
```
  Columns: age, name, number, paid, s1, s2, s3, s4, s5
  Examples: courses 2\Code.org sat 11-2 nada.xlsx::Sheet1; courses 2\Code.org sat 11-2 nada.xlsx::Sheet2
```

**Pattern 5** — 19 files sharing this column structure:
```
  Columns: age, fee_paid, grade, mobile, month_paid, name, s2, s3, s4, s5 ...
  Examples: Esraa\8mon\fri8.xlsx::Sheet3; Esraa\8mon\fri8.xlsx::Sheet4
```

**Pattern 6** — 16 files sharing this column structure:
```
  Columns: name, number, paid, s1, s2, s3, s4, s5, start, teacher ...
  Examples: courses 2\Old Courses\April 2024\Ev3 Sat 5-8.xlsx::Sheet1; courses 2\Old Courses\April 2024\Spike fri 5-8.xlsx::Sheet1
```

**Pattern 7** — 15 files sharing this column structure:
```
  Columns: age, fee_paid, grade, mobile, month_paid, name, s1, s2, s3, s4
  Examples: courses 2\Old Courses\Wedo sun 3.30.xlsx::Sheet1; courses 2\Old Courses\Wedo sun 3.30.xlsx::Sheet2
```

**Pattern 8** — 15 files sharing this column structure:
```
  Columns: age, fee_paid, grade, mobile, month_paid, name, s1, s2, s3, s4 ...
  Examples: courses 2\Old Courses\ramadan course sun 8-10.xlsx::Sheet1; courses 2\Old Courses\wedo sat 2-4.xlsx::NOV
```

### 3.3 Attendance Grid Pattern

A majority of files use a **wide attendance format**: one column per session date, with cell values encoding presence/absence using symbols (`✓`, `1`, `P`, `A`, Arabic `حضر`/`غاب`). The migration pipeline normalizes these to a **long format** (one row per person per date), enabling time-series analysis without schema changes.

---

## 4. Proposed Folder Structure

```
_REORGANIZED/
├── 01_CourseAttendance/
│   ├── Active/          ← Current academic year course registers
│   └── Archive/         ← Previous months/years (Old Courses, Arabic month folders)
├── 02_CompetitionTracking/
│   ├── FLL/             ← FIRST Lego League monthly files
│   └── Robofest/        ← Robofest competition files
├── 03_StaffAttendance/  ← Instructor/staff day-of-week attendance
├── 04_CRM_SAT/          ← CRM records and SAT group files
└── 05_Unclassified/
    ├── corrupt/         ← Unreadable files
    └── protected/       ← Password-protected files
```

**Justification:**
- Separation by business function enables domain-specific access control
- Active vs. Archive split for CourseAttendance reflects operational vs. historical use
- FLL/Robofest sub-split within Competitions matches the center's two main competition programs
- All files COPIED (not moved) — originals preserved, zero rollback risk

---

## 5. Standardized Schema Documentation

### 5.1 Master Unified Flat Table: `unified_attendance`

| Field | Type | Required | Description |
|---|---|---|---|
| `record_id` | UUID | Yes | Auto-generated primary key |
| `source_file` | TEXT | Yes | Relative path of source Excel file |
| `source_sheet` | TEXT | No | Worksheet tab name |
| `domain` | ENUM | Yes | Business domain classification |
| `migrated_at` | TIMESTAMP | Yes | Time of migration |
| `person_name` | TEXT | No | Student, staff, or team member name |
| `phone` | TEXT | No | 10–15 digit phone number |
| `course_name` | TEXT | No | Course or program name |
| `course_level` | INTEGER | No | Course level (1, 2, 3…) |
| `session_day` | TEXT | No | Day of week (e.g., Saturday) |
| `session_time` | TEXT | No | Time slot (HH:MM-HH:MM) |
| `instructor_name` | TEXT | No | Instructor name |
| `team_name` | TEXT | No | Competition team name |
| `member_list` | TEXT | No | Semicolon-separated members |
| `competition_category` | TEXT | No | FLL / Robofest / WRO |
| `group_code` | TEXT | No | SAT group or CRM batch code |
| `enrollment_status` | TEXT | No | Active / Completed / Pending |
| `score` | FLOAT | No | Numeric score or grade |
| `attendance_date` | DATE | No | Specific date of attendance record |
| `attendance_status` | SMALLINT | No | 1=present, 0=absent, NULL=unknown |
| `source_row_number` | INTEGER | Yes | Original row in source sheet |
| `extra_fields` | JSON | No | Overflow columns not in schema |
| `quality_flags` | TEXT | No | Pipe-separated QA issues |

### 5.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Column names | `snake_case` | `student_name`, `session_day` |
| Domain values | `PascalCase` | `CourseAttendance`, `CRM_SAT` |
| Attendance status | Binary integer | `1` (present), `0` (absent) |
| Date format | ISO 8601 | `2024-03-15` |
| Phone format | Digits only, no spaces | `01012345678` |
| File names | `[CourseName]_[Day]_[Time].xlsx` | `HTML_Sat_10-12.xlsx` |
| Folder names | `NN_CategoryName/SubCategory` | `01_CourseAttendance/Active` |

---

## 6. Implementation Roadmap

| Step | Script | Command | Duration |
|---|---|---|---|
| 1 | Install dependencies | `pip install openpyxl pandas xlrd` | 2 min |
| 2 | File scan & metadata | `python 01_analyze_files.py` | 2–5 min |
| 3 | Schema analysis | `python 02_schema_analysis.py` | < 1 min |
| 4 | Review unresolved | Edit `unresolved_columns.csv` | 15–30 min |
| 5 | Dry-run migration | `python 03_reorganize.py` | < 1 min |
| 6 | Execute migration | `python 03_reorganize.py --execute` | 2–5 min |
| 7 | Validate | `python 04_validate.py` | < 1 min |
| 8 | Generate templates | `python 05_generate_schema_template.py` | < 1 min |
| 9 | One-shot pipeline | `python run_all.py --execute` | 5–10 min |

---

## 7. Risk Mitigation Strategies

| Risk | Mitigation |
|---|---|
| Corrupt/unreadable Excel files | try-except → move to `05_Unclassified/corrupt/` |
| Arabic filenames causing path errors | `pathlib.Path` with UTF-8 throughout |
| Header not in row 1 | Auto-scan first 10 rows; pick highest string-density row |
| Temp lock files (~$) | Skipped by prefix check before any file operation |
| Duplicate files (same content) | SHA-256 deduplication; only one copy migrated |
| Merged cells causing data offset | `openpyxl` unmerge + forward-fill |
| Column synonym missing | Written to `unresolved_columns.csv` for manual mapping |
| Large files (>5MB) causing memory | `read_only=True` mode in openpyxl |
| File written halfway (power loss) | Copy-before-move; audit log tracks SUCCESS/ERROR |
| Password-protected files | Caught, logged, moved to `05_Unclassified/protected/` |

---

## 8. Migration Quality Results

| Metric | Value |
|---|---|
| Total files processed | 201 |
| Successfully copied | 201 |
| Errors | 0 |
| Success rate | 100.0% |

---

## 9. Data Analysis Readiness

Before handing the unified schema to data analysts, verify all of the following:

- [ ] `04_validate.py` reports **ALL CHECKS PASSED**
- [ ] `unresolved_columns.csv` reviewed and addressed
- [ ] `MasterSchema_UnifiedTable.xlsx` template spot-checked with sample queries
- [ ] `CourseAttendance_Template.xlsx` validated with 2–3 representative source files
- [ ] Data profile metrics meet thresholds (Completeness ≥ 90%, Accuracy ≥ 95%)
- [ ] No ERROR rows in `migration_audit.csv`
- [ ] All 5 template files exist in `_standardization_output/templates/`

---

## 10. Output Files Summary

| File | Location | Purpose |
|---|---|---|
| `file_metadata.json` | `_standardization_output/` | Full per-file metadata |
| `file_inventory.csv` | `_standardization_output/` | Spreadsheet-friendly summary |
| `schema_patterns.json` | `_standardization_output/` | Domain classifications |
| `schema_analysis_report.txt` | `_standardization_output/` | Human-readable analysis |
| `unresolved_columns.csv` | `_standardization_output/` | Columns needing manual review |
| `migration_audit.csv` | `_standardization_output/` | Full copy audit trail |
| `validation_report.txt` | `_standardization_output/` | QA check results |
| `TECHNICAL_REPORT.md` | `_standardization_output/` | This report |
| `CourseAttendance_Template.xlsx` | `_standardization_output/templates/` | Course template |
| `Competition_Template.xlsx` | `_standardization_output/templates/` | Competition template |
| `StaffAttendance_Template.xlsx` | `_standardization_output/templates/` | Staff template |
| `CRM_SAT_Template.xlsx` | `_standardization_output/templates/` | CRM template |
| `MasterSchema_UnifiedTable.xlsx` | `_standardization_output/templates/` | Master schema |
| `_REORGANIZED/` | Root of workspace | Reorganized copy of all files |

---

*Report auto-generated by `run_all.py` — 2026-02-25 00:06*