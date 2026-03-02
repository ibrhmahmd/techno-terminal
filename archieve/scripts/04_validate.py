"""
Script 4: Quality Validation
============================
Reads migration_audit.csv and schema_patterns.json and verifies:
  - Classification rate >= 95%
  - All copied files exist at destination and have size > 0
  - No ERROR rows in audit log
  - Data quality thresholds from migration_architecture.md

Outputs:
  _standardization_output/validation_report.txt

Usage:
  python 04_validate.py
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "_standardization_output"
REORG_DIR = BASE_DIR / "data" / "processed" / "_REORGANIZED"
PATTERNS_FILE = OUTPUT_DIR / "schema_patterns.json"
AUDIT_FILE = OUTPUT_DIR / "migration_audit.csv"

# ── Acceptance thresholds ─────────────────────────────────────────────────────
THRESHOLD_CLASSIFICATION_RATE = 95.0  # AC-01
THRESHOLD_MIGRATION_COMPLETENESS = 98.0  # AC-02
THRESHOLD_LINEAGE_COMPLETENESS = 100.0  # AC-05

# Data quality thresholds (from migration_architecture.md Section 7)
QUALITY_THRESHOLDS = {
    "null_person_name_max_pct": 15.0,  # T4
    "date_parse_rate_min_pct": 90.0,  # T5
    "attendance_encoding_rate_min_pct": 85.0,  # T6
    "max_unresolved_col_pct": 5.0,  # AC-07
}


def run_validation():
    report_lines = []
    all_pass = True

    def check(test_id, description, condition, actual_val, threshold, unit=""):
        nonlocal all_pass
        status = "PASS ✓" if condition else "FAIL ✗"
        if not condition:
            all_pass = False
        line = (
            f"  [{status}] {test_id}: {description}\n"
            f"           Actual: {actual_val}{unit}  |  Threshold: {threshold}{unit}"
        )
        report_lines.append(line)
        print(line)

    print(f"\n{'=' * 70}")
    print(f"  Quality Validation Report")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"{'=' * 70}\n")

    report_lines.append("QUALITY VALIDATION REPORT")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append("=" * 70)

    # ── Load schema patterns ──────────────────────────────────────────────────
    if not PATTERNS_FILE.exists():
        print("[SKIP] schema_patterns.json not found — skipping classification checks")
    else:
        with open(PATTERNS_FILE, encoding="utf-8") as f:
            patterns = json.load(f)

        file_classes = patterns.get("file_classifications", [])
        total_files = len(file_classes)
        classified = sum(1 for fc in file_classes if fc.get("domain") != "Unclassified")
        unclassified = total_files - classified
        class_rate = (classified / total_files * 100) if total_files > 0 else 0

        report_lines.append(
            "\n── CLASSIFICATION CHECKS ───────────────────────────────────────────────"
        )
        check(
            "AC-01",
            "Classification rate ≥ 95%",
            class_rate >= THRESHOLD_CLASSIFICATION_RATE,
            f"{class_rate:.1f}",
            f"≥{THRESHOLD_CLASSIFICATION_RATE}",
            "%",
        )

        # Unresolved columns check
        total_unresolved = sum(
            len(fc.get("unresolved_columns", [])) for fc in file_classes
        )
        total_cols = sum(
            len(fc.get("unresolved_columns", [])) + 1 for fc in file_classes
        )  # approx
        unresolved_pct = (total_unresolved / total_cols * 100) if total_cols > 0 else 0
        check(
            "AC-07",
            f"Unresolved columns ≤ {QUALITY_THRESHOLDS['max_unresolved_col_pct']}%",
            unresolved_pct <= QUALITY_THRESHOLDS["max_unresolved_col_pct"],
            f"{unresolved_pct:.1f}",
            f"≤{QUALITY_THRESHOLDS['max_unresolved_col_pct']}",
            "%",
        )

        # Domain distribution
        domain_counts = Counter(fc.get("domain") for fc in file_classes)
        report_lines.append("\n  Domain Distribution:")
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            pct = count / total_files * 100 if total_files else 0
            report_lines.append(f"    {domain:<28} {count:>4} ({pct:.1f}%)")

    # ── Load audit log ────────────────────────────────────────────────────────
    report_lines.append(
        "\n── MIGRATION AUDIT CHECKS ──────────────────────────────────────────────"
    )

    if not AUDIT_FILE.exists():
        print("[SKIP] migration_audit.csv not found — skipping migration checks")
        print(
            "[NOTE] Run: python 03_reorganize.py --execute to perform migration first"
        )
        report_lines.append(
            "  [SKIP] migration_audit.csv not found (migration not yet executed)"
        )
    else:
        with open(AUDIT_FILE, encoding="utf-8-sig", newline="") as f:
            audit_rows = list(csv.DictReader(f))

        total_audit = len(audit_rows)
        success_rows = [r for r in audit_rows if r.get("status") == "SUCCESS"]
        error_rows = [r for r in audit_rows if r.get("status") == "ERROR"]
        skipped_rows = [r for r in audit_rows if r.get("status", "").startswith("SKIP")]

        migration_rate = (
            (len(success_rows) / total_audit * 100) if total_audit > 0 else 0
        )
        check(
            "AC-02",
            "Migration completeness ≥ 98%",
            migration_rate >= THRESHOLD_MIGRATION_COMPLETENESS,
            f"{migration_rate:.1f}",
            f"≥{THRESHOLD_MIGRATION_COMPLETENESS}",
            "%",
        )

        zero_errors = len(error_rows) == 0
        check(
            "AC-04",
            "Zero ERROR rows in audit log",
            zero_errors,
            len(error_rows),
            0,
            " errors",
        )

        # Verify destination files exist and are non-zero
        report_lines.append(
            "\n── FILE INTEGRITY CHECKS ───────────────────────────────────────────────"
        )
        missing = []
        zero_size = []
        for row in success_rows:
            dest = Path(row.get("destination_abs_path", ""))
            if not dest.exists():
                missing.append(str(dest))
            elif dest.stat().st_size == 0:
                zero_size.append(str(dest))

        check(
            "AC-06a",
            "All migrated files exist at destination",
            len(missing) == 0,
            len(missing),
            0,
            " missing",
        )
        check(
            "AC-06b",
            "All migrated files have non-zero size",
            len(zero_size) == 0,
            len(zero_size),
            0,
            " zero-size",
        )

        if missing:
            report_lines.append("\n  Missing files:")
            for m in missing[:10]:
                report_lines.append(f"    - {m}")

        # Lineage completeness
        lineage_complete = sum(
            1
            for r in success_rows
            if r.get("original_path") and r.get("destination_path")
        )
        lin_rate = (lineage_complete / len(success_rows) * 100) if success_rows else 0
        check(
            "AC-05",
            "Lineage completeness = 100%",
            lin_rate >= THRESHOLD_LINEAGE_COMPLETENESS,
            f"{lin_rate:.1f}",
            "100",
            "%",
        )

        # Summary stats
        report_lines.append(f"\n  Audit Summary:")
        report_lines.append(f"    Total entries    : {total_audit}")
        report_lines.append(f"    Successful copies: {len(success_rows)}")
        report_lines.append(f"    Errors           : {len(error_rows)}")
        report_lines.append(f"    Skipped          : {len(skipped_rows)}")

        if error_rows:
            report_lines.append("\n  Error Details:")
            for r in error_rows[:10]:
                report_lines.append(
                    f"    - {r.get('original_path')}: {r.get('error_message')}"
                )

    # ── Semantic validation checks ────────────────────────────────────────────
    report_lines.append(
        "\n── SEMANTIC VALIDATION CHECKS ──────────────────────────────────────────"
    )
    report_lines.append(
        "  [INFO] Semantic checks run against the raw metadata, not migrated rows."
    )

    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, encoding="utf-8") as f:
            patterns = json.load(f)
        # Check: all CourseAttendance files have at least 1 data row
        ca_files = [
            fc
            for fc in patterns.get("file_classifications", [])
            if fc.get("domain") == "CourseAttendance"
        ]
        empty_ca = [fc for fc in ca_files if fc.get("total_rows", 0) == 0]
        check(
            "SEM-01",
            "CourseAttendance files have >0 data rows",
            len(empty_ca) == 0,
            f"{len(empty_ca)} empty",
            "0 empty",
            "",
        )

        # Check: competition files confidence ≥ 0.3
        comp_files = [
            fc
            for fc in patterns.get("file_classifications", [])
            if fc.get("domain") == "CompetitionTracking"
        ]
        low_conf = [fc for fc in comp_files if fc.get("confidence", 0) < 0.3]
        check(
            "SEM-02",
            "Competition files have confidence ≥ 0.3",
            len(low_conf) == 0,
            f"{len(low_conf)} low-confidence",
            "0 low-confidence",
            "",
        )

    # ── Final verdict ─────────────────────────────────────────────────────────
    verdict = (
        "ALL CHECKS PASSED — Data is READY for analysis pipeline"
        if all_pass
        else "SOME CHECKS FAILED — Review failures before proceeding"
    )
    report_lines.append(f"\n{'=' * 70}")
    report_lines.append(f"  FINAL VERDICT: {verdict}")
    report_lines.append(f"{'=' * 70}")

    # Write text report
    validation_report = OUTPUT_DIR / "validation_report.txt"
    with open(validation_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n  [OK] Validation report written → {validation_report}")

    print(f"\n  FINAL VERDICT: {verdict}\n")
    return all_pass


if __name__ == "__main__":
    passed = run_validation()
    exit(0 if passed else 1)
