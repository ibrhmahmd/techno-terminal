"""
run_all.py — Full Pipeline Orchestrator
========================================
Runs all 5 scripts in sequence and generates the final technical report.

Usage:
  python run_all.py              # Scan + Analyze + Dry-run + Validate + Templates
  python run_all.py --execute    # Full pipeline including actual file copy

Steps:
  1. 01_analyze_files.py        — Excel scan & metadata extraction
  2. 02_schema_analysis.py      — Domain classification & schema patterns
  3. 03_reorganize.py            — Folder reorganization (dry-run or --execute)
  4. 04_validate.py              — Quality validation
  5. 05_generate_schema_template.py — Excel templates
  6. Generate TECHNICAL_REPORT.md
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime

import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "_standardization_output"


# ─────────────────────────────────────────────────────────────────────────────
# Run each script as a module (avoids subprocess PATH issues)
# ─────────────────────────────────────────────────────────────────────────────
def run_step(name, func, *args, **kwargs):
    print(f"\n{'▸' * 70}")
    print(f"  STEP: {name}")
    print(f"{'▸' * 70}")
    try:
        result = func(*args, **kwargs)
        print(f"  ✓ {name} completed successfully.\n")
        return result
    except Exception as e:
        print(f"  ✗ {name} FAILED: {e}")
        import traceback

        traceback.print_exc()
        return None


def generate_technical_report():
    """Generate the final TECHNICAL_REPORT.md from all output files."""
    report_path = OUTPUT_DIR / "TECHNICAL_REPORT.md"

    # Load data
    metadata = {}
    md_path = OUTPUT_DIR / "file_metadata.json"
    if md_path.exists():
        with open(md_path, encoding="utf-8") as f:
            metadata = json.load(f)

    patterns = {}
    pat_path = OUTPUT_DIR / "schema_patterns.json"
    if pat_path.exists():
        with open(pat_path, encoding="utf-8") as f:
            patterns = json.load(f)

    audit_rows = []
    audit_path = OUTPUT_DIR / "migration_audit.csv"
    if audit_path.exists():
        with open(audit_path, encoding="utf-8-sig", newline="") as f:
            audit_rows = list(csv.DictReader(f))

    stats = metadata.get("stats", {})
    domain_counts = patterns.get("domain_counts", {})
    classification_rate = patterns.get("classification_rate_pct", 0)
    file_classes = patterns.get("file_classifications", [])

    # Aggregate sizes per domain
    domain_sizes = {}
    for fc in file_classes:
        d = fc.get("domain", "Unclassified")
        domain_sizes[d] = domain_sizes.get(d, 0) + fc.get("file_size_bytes", 0)

    # Top schema patterns
    top_patterns = patterns.get("top_schema_clusters", [])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    execute_mode = "--execute" in sys.argv

    lines = [
        "# Technical Report: Data Standardization Project",
        f"**Organization:** Techno Education Center",
        f"**Generated:** {now}",
        f"**Pipeline mode:** {'Full Execute' if execute_mode else 'Analysis + Dry-Run Only'}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"This report documents the automated analysis, classification, and reorganization of **{stats.get('excel_files', 'N/A')} Excel files** found in the `techno_data_ Copy` directory. "
        f"The pipeline successfully classified **{classification_rate:.1f}%** of files into structured business domains, "
        f"exceeding the 95% acceptance threshold."
        if classification_rate >= 95
        else f"The pipeline classified **{classification_rate:.1f}%** of files (target: ≥95%). Some manual review is required.",
        "",
        "---",
        "",
        "## 2. Current State Analysis",
        "",
        "### 2.1 File Distribution Statistics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total files scanned | {stats.get('total_files_found', 'N/A')} |",
        f"| Valid Excel files (.xlsx/.xls/.xlsm) | {stats.get('excel_files', 'N/A')} |",
        f"| Temp/lock files excluded (~$*) | {stats.get('temp_lock_files', 'N/A')} |",
        f"| Other non-Excel files | {stats.get('other_files', 'N/A')} |",
        f"| Unreadable/corrupt files | {stats.get('unreadable_files', 'N/A')} |",
        f"| Total worksheets found | {stats.get('total_sheets', 'N/A')} |",
        f"| Total data rows (all sheets) | {stats.get('total_rows', 'N/A')} |",
        "",
        "### 2.2 Original Folder Structure",
        "",
        "```",
        "techno_data_ Copy/",
        "├── CRM/                          (1 file — SAT.xlsx)",
        "├── Esraa/                         (6 files + 7 subdirectories)",
        "│   ├── 8mon/                      (day-of-week course registers)",
        "│   ├── Meeting Recordings/        (4 Robofest sub-categories + 1 video)",
        "│   ├── ROBOFEST SHEETS/           (competition Excel files)",
        "│   ├── fll sheets/                (FLL competition file)",
        "│   ├── شهر مايو/ (May)            (monthly course registers)",
        "│   ├── شهر يونيو/ (June)          (monthly course registers)",
        "│   └── شهر7/ (Month 7)            (monthly course registers)",
        "├── attendance/                    (8 day-of-week attendance files)",
        "└── courses 2/                     (active courses + Old Courses archive)",
        "    ├── Old Courses/               (monthly archives: Mar-Oct 2024)",
        "    │   ├── FLL/                   (8 FLL monthly files)",
        "    │   ├── AAFFIAT/               (specialized sub-course)",
        "    │   ├── Codeavour/             (competition)",
        "    │   └── [Month YYYY] folders   (March–October 2024)",
        "    └── Robofest 2025/             (Robofest 2025 files)",
        "```",
        "",
        "### 2.3 Key Observations",
        "",
        "- **Naming inconsistency**: Files use day abbreviations (`fri.xlsx`), course+time slots (`CSS L1 Fri 11-2.xlsx`), and month names in both English and Arabic",
        "- **Arabic folder names**: `شهر مايو`, `شهر يونيو`, `شهر7` represent monthly groupings and must be handled with UTF-8 encoding",
        "- **Temp lock files**: 165-byte `~$*.xlsx` files (Excel lock files) are present in nearly every folder — excluded from migration",
        "- **Deep nesting**: Up to 4 levels of subfolder depth; some single-file folders (e.g., `fll sheets/`)",
        "- **Duplicate content**: SHA-256 hashing identifies any files with identical content across folder locations",
        "",
        "---",
        "",
        "## 3. Discovered Data Patterns",
        "",
        "### 3.1 Business Domain Classification",
        "",
        "| Domain | File Count | Classification |",
        "|---|---|---|",
    ]
    total_files = sum(domain_counts.values()) if domain_counts else 1
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct = count / total_files * 100
        lines.append(f"| {domain} | {count} | {pct:.1f}% |")

    lines += [
        "",
        "### 3.2 Top Schema Patterns",
        "",
        "The following recurring column fingerprints were identified across the file collection:",
        "",
    ]
    for i, cluster in enumerate(top_patterns[:8], 1):
        fp = cluster.get("fingerprint", "")
        count = cluster.get("file_count", 0)
        examples = cluster.get("examples", [])[:2]
        cols = fp.split("|") if fp else []
        lines.append(f"**Pattern {i}** — {count} files sharing this column structure:")
        lines.append(f"```")
        lines.append(
            "  Columns: " + ", ".join(cols[:10]) + (" ..." if len(cols) > 10 else "")
        )
        lines.append(f"  Examples: {'; '.join(examples)}")
        lines.append("```")
        lines.append("")

    lines += [
        "### 3.3 Attendance Grid Pattern",
        "",
        "A majority of files use a **wide attendance format**: one column per session date, with cell values encoding presence/absence "
        "using symbols (`✓`, `1`, `P`, `A`, Arabic `حضر`/`غاب`). The migration pipeline normalizes these to a **long format** (one row per person per date), "
        "enabling time-series analysis without schema changes.",
        "",
        "---",
        "",
        "## 4. Proposed Folder Structure",
        "",
        "```",
        "_REORGANIZED/",
        "├── 01_CourseAttendance/",
        "│   ├── Active/          ← Current academic year course registers",
        "│   └── Archive/         ← Previous months/years (Old Courses, Arabic month folders)",
        "├── 02_CompetitionTracking/",
        "│   ├── FLL/             ← FIRST Lego League monthly files",
        "│   └── Robofest/        ← Robofest competition files",
        "├── 03_StaffAttendance/  ← Instructor/staff day-of-week attendance",
        "├── 04_CRM_SAT/          ← CRM records and SAT group files",
        "└── 05_Unclassified/",
        "    ├── corrupt/         ← Unreadable files",
        "    └── protected/       ← Password-protected files",
        "```",
        "",
        "**Justification:**",
        "- Separation by business function enables domain-specific access control",
        "- Active vs. Archive split for CourseAttendance reflects operational vs. historical use",
        "- FLL/Robofest sub-split within Competitions matches the center's two main competition programs",
        "- All files COPIED (not moved) — originals preserved, zero rollback risk",
        "",
        "---",
        "",
        "## 5. Standardized Schema Documentation",
        "",
        "### 5.1 Master Unified Flat Table: `unified_attendance`",
        "",
        "| Field | Type | Required | Description |",
        "|---|---|---|---|",
        "| `record_id` | UUID | Yes | Auto-generated primary key |",
        "| `source_file` | TEXT | Yes | Relative path of source Excel file |",
        "| `source_sheet` | TEXT | No | Worksheet tab name |",
        "| `domain` | ENUM | Yes | Business domain classification |",
        "| `migrated_at` | TIMESTAMP | Yes | Time of migration |",
        "| `person_name` | TEXT | No | Student, staff, or team member name |",
        "| `phone` | TEXT | No | 10–15 digit phone number |",
        "| `course_name` | TEXT | No | Course or program name |",
        "| `course_level` | INTEGER | No | Course level (1, 2, 3…) |",
        "| `session_day` | TEXT | No | Day of week (e.g., Saturday) |",
        "| `session_time` | TEXT | No | Time slot (HH:MM-HH:MM) |",
        "| `instructor_name` | TEXT | No | Instructor name |",
        "| `team_name` | TEXT | No | Competition team name |",
        "| `member_list` | TEXT | No | Semicolon-separated members |",
        "| `competition_category` | TEXT | No | FLL / Robofest / WRO |",
        "| `group_code` | TEXT | No | SAT group or CRM batch code |",
        "| `enrollment_status` | TEXT | No | Active / Completed / Pending |",
        "| `score` | FLOAT | No | Numeric score or grade |",
        "| `attendance_date` | DATE | No | Specific date of attendance record |",
        "| `attendance_status` | SMALLINT | No | 1=present, 0=absent, NULL=unknown |",
        "| `source_row_number` | INTEGER | Yes | Original row in source sheet |",
        "| `extra_fields` | JSON | No | Overflow columns not in schema |",
        "| `quality_flags` | TEXT | No | Pipe-separated QA issues |",
        "",
        "### 5.2 Naming Conventions",
        "",
        "| Element | Convention | Example |",
        "|---|---|---|",
        "| Column names | `snake_case` | `student_name`, `session_day` |",
        "| Domain values | `PascalCase` | `CourseAttendance`, `CRM_SAT` |",
        "| Attendance status | Binary integer | `1` (present), `0` (absent) |",
        "| Date format | ISO 8601 | `2024-03-15` |",
        "| Phone format | Digits only, no spaces | `01012345678` |",
        "| File names | `[CourseName]_[Day]_[Time].xlsx` | `HTML_Sat_10-12.xlsx` |",
        "| Folder names | `NN_CategoryName/SubCategory` | `01_CourseAttendance/Active` |",
        "",
        "---",
        "",
        "## 6. Implementation Roadmap",
        "",
        "| Step | Script | Command | Duration |",
        "|---|---|---|---|",
        "| 1 | Install dependencies | `pip install openpyxl pandas xlrd` | 2 min |",
        "| 2 | File scan & metadata | `python 01_analyze_files.py` | 2–5 min |",
        "| 3 | Schema analysis | `python 02_schema_analysis.py` | < 1 min |",
        "| 4 | Review unresolved | Edit `unresolved_columns.csv` | 15–30 min |",
        "| 5 | Dry-run migration | `python 03_reorganize.py` | < 1 min |",
        "| 6 | Execute migration | `python 03_reorganize.py --execute` | 2–5 min |",
        "| 7 | Validate | `python 04_validate.py` | < 1 min |",
        "| 8 | Generate templates | `python 05_generate_schema_template.py` | < 1 min |",
        "| 9 | One-shot pipeline | `python run_all.py --execute` | 5–10 min |",
        "",
        "---",
        "",
        "## 7. Risk Mitigation Strategies",
        "",
        "| Risk | Mitigation |",
        "|---|---|",
        "| Corrupt/unreadable Excel files | try-except → move to `05_Unclassified/corrupt/` |",
        "| Arabic filenames causing path errors | `pathlib.Path` with UTF-8 throughout |",
        "| Header not in row 1 | Auto-scan first 10 rows; pick highest string-density row |",
        "| Temp lock files (~$) | Skipped by prefix check before any file operation |",
        "| Duplicate files (same content) | SHA-256 deduplication; only one copy migrated |",
        "| Merged cells causing data offset | `openpyxl` unmerge + forward-fill |",
        "| Column synonym missing | Written to `unresolved_columns.csv` for manual mapping |",
        "| Large files (>5MB) causing memory | `read_only=True` mode in openpyxl |",
        "| File written halfway (power loss) | Copy-before-move; audit log tracks SUCCESS/ERROR |",
        "| Password-protected files | Caught, logged, moved to `05_Unclassified/protected/` |",
        "",
        "---",
        "",
        "## 8. Migration Quality Results",
        "",
    ]

    if audit_rows:
        total_audit = len(audit_rows)
        success = sum(1 for r in audit_rows if r.get("status") == "SUCCESS")
        errors = sum(1 for r in audit_rows if r.get("status") == "ERROR")
        lines += [
            f"| Metric | Value |",
            f"|---|---|",
            f"| Total files processed | {total_audit} |",
            f"| Successfully copied | {success} |",
            f"| Errors | {errors} |",
            f"| Success rate | {success / total_audit * 100:.1f}% |"
            if total_audit
            else "",
        ]
    else:
        lines.append(
            "*Migration not yet executed. Run `python 03_reorganize.py --execute` to perform migration.*"
        )

    lines += [
        "",
        "---",
        "",
        "## 9. Data Analysis Readiness",
        "",
        "Before handing the unified schema to data analysts, verify all of the following:",
        "",
        "- [ ] `04_validate.py` reports **ALL CHECKS PASSED**",
        "- [ ] `unresolved_columns.csv` reviewed and addressed",
        "- [ ] `MasterSchema_UnifiedTable.xlsx` template spot-checked with sample queries",
        "- [ ] `CourseAttendance_Template.xlsx` validated with 2–3 representative source files",
        "- [ ] Data profile metrics meet thresholds (Completeness ≥ 90%, Accuracy ≥ 95%)",
        "- [ ] No ERROR rows in `migration_audit.csv`",
        "- [ ] All 5 template files exist in `_standardization_output/templates/`",
        "",
        "---",
        "",
        "## 10. Output Files Summary",
        "",
        "| File | Location | Purpose |",
        "|---|---|---|",
        "| `file_metadata.json` | `_standardization_output/` | Full per-file metadata |",
        "| `file_inventory.csv` | `_standardization_output/` | Spreadsheet-friendly summary |",
        "| `schema_patterns.json` | `_standardization_output/` | Domain classifications |",
        "| `schema_analysis_report.txt` | `_standardization_output/` | Human-readable analysis |",
        "| `unresolved_columns.csv` | `_standardization_output/` | Columns needing manual review |",
        "| `migration_audit.csv` | `_standardization_output/` | Full copy audit trail |",
        "| `validation_report.txt` | `_standardization_output/` | QA check results |",
        "| `TECHNICAL_REPORT.md` | `_standardization_output/` | This report |",
        "| `CourseAttendance_Template.xlsx` | `_standardization_output/templates/` | Course template |",
        "| `Competition_Template.xlsx` | `_standardization_output/templates/` | Competition template |",
        "| `StaffAttendance_Template.xlsx` | `_standardization_output/templates/` | Staff template |",
        "| `CRM_SAT_Template.xlsx` | `_standardization_output/templates/` | CRM template |",
        "| `MasterSchema_UnifiedTable.xlsx` | `_standardization_output/templates/` | Master schema |",
        "| `_REORGANIZED/` | Root of workspace | Reorganized copy of all files |",
        "",
        "---",
        "",
        f"*Report auto-generated by `run_all.py` — {now}*",
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  [OK] Technical report → {report_path}")
    return report_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def main():
    execute = "--execute" in sys.argv

    print("\n" + "=" * 70)
    print("  DATA STANDARDIZATION PIPELINE — Techno Education Center")
    print(
        f"  Mode: {'EXECUTE (will copy files)' if execute else 'ANALYSIS ONLY (dry-run)'}"
    )
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Import scripts as modules
    import importlib.util, os

    def load_and_run(script_name, function_name, *args, **kwargs):
        script_path = BASE_DIR / "src" / script_name
        spec = importlib.util.spec_from_file_location(
            script_name.replace(".py", ""), script_path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, function_name)
        return run_step(script_name, func, *args, **kwargs)

    # Step 1: Scan
    load_and_run("01_analyze_files.py", "scan_all_files")

    # Step 2: Schema analysis
    load_and_run("02_schema_analysis.py", "analyze_schemas")

    # Step 3: Reorganize
    if execute:
        load_and_run("03_reorganize.py", "reorganize", dry_run=False)
    else:
        load_and_run("03_reorganize.py", "reorganize", dry_run=True)

    # Step 4: Validate
    load_and_run("04_validate.py", "run_validation")

    # Step 5: Templates
    load_and_run("05_generate_schema_template.py", "generate_all_templates")

    # Step 6: Technical report
    run_step("generate_technical_report", generate_technical_report)

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print(f"  All outputs in: {OUTPUT_DIR}")
    print(f"  Technical report: {OUTPUT_DIR / 'TECHNICAL_REPORT.md'}")
    if not execute:
        print("\n  ⚠  This was a DRY-RUN. No files were copied.")
        print("  To execute migration: python run_all.py --execute")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
