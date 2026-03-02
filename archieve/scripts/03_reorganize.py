"""
Script 3: Folder Reorganization with Audit Trail
================================================
Reads schema_patterns.json from 02_schema_analysis.py and:
  - Builds a mapping of source file → recommended destination
  - In dry-run mode (default): prints proposed moves, no file operations
  - With --execute flag: COPIES (never moves) files to _REORGANIZED/ structure
  - Writes a full audit trail to migration_audit.csv

Usage:
  python 03_reorganize.py             # dry-run (safe preview)
  python 03_reorganize.py --execute   # perform actual copy

Outputs:
  _REORGANIZED/ (all copied files in new hierarchy)
  _standardization_output/migration_audit.csv
"""

import json
import sys
import csv
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "_standardization_output"
REORG_DIR = BASE_DIR / "data" / "processed" / "_REORGANIZED"
PATTERNS_FILE = OUTPUT_DIR / "schema_patterns.json"
AUDIT_FILE = OUTPUT_DIR / "migration_audit.csv"

# Folder structure labels
FOLDER_LABELS = {
    "01_CourseAttendance": "Course Attendance Registers",
    "01_CourseAttendance/Active": "Active Course Registers (Current Academic Year)",
    "01_CourseAttendance/Archive": "Archived Course Registers (Previous Months/Years)",
    "02_CompetitionTracking": "Competition Tracking",
    "02_CompetitionTracking/FLL": "FIRST Lego League (FLL) Competition Files",
    "02_CompetitionTracking/Robofest": "Robofest Competition Files",
    "03_StaffAttendance": "Staff/Instructor Attendance Records",
    "04_CRM_SAT": "CRM and SAT Group Records",
    "05_Unclassified": "Unclassified / Needs Manual Review",
    "05_Unclassified/corrupt": "Corrupt or Unreadable Files",
    "05_Unclassified/protected": "Password-Protected Files",
}

AUDIT_FIELDS = [
    "timestamp",
    "action",
    "original_path",
    "original_abs_path",
    "destination_path",
    "destination_abs_path",
    "domain",
    "confidence",
    "file_size_bytes",
    "status",
    "error_message",
]


def build_destination_path(file_class: dict) -> Path:
    """Compute the destination path for a file inside _REORGANIZED/."""
    rec_folder = file_class.get("recommended_folder", "05_Unclassified")
    base_name = Path(file_class["file_path"]).name
    return REORG_DIR / rec_folder / base_name


def make_unique(dest_path: Path) -> Path:
    """If destination exists, append (1), (2), … to filename."""
    if not dest_path.exists():
        return dest_path
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def create_folder_readme(folder: Path, label: str):
    """Create a README.txt inside each newly created folder."""
    readme = folder / "README.txt"
    if not readme.exists():
        readme.write_text(
            f"Folder: {label}\n"
            f"Created by standardization script on {datetime.now().strftime('%Y-%m-%d')}\n"
            f"All files in this folder share the same business domain.\n",
            encoding="utf-8",
        )


def reorganize(dry_run: bool = True):
    if not PATTERNS_FILE.exists():
        print(f"[ERROR] {PATTERNS_FILE} not found. Run 02_schema_analysis.py first.")
        return

    with open(PATTERNS_FILE, encoding="utf-8") as f:
        patterns = json.load(f)

    file_classes = patterns.get("file_classifications", [])
    if not file_classes:
        print("[ERROR] No file classifications found in schema_patterns.json")
        return

    mode_label = "DRY-RUN (preview only)" if dry_run else "EXECUTE (copying files)"
    print(f"\n{'=' * 70}")
    print(f"  Folder Reorganization — {mode_label}")
    print(f"  Files to process: {len(file_classes)}")
    print(f"  Destination root: {REORG_DIR}")
    print(f"{'=' * 70}\n")

    audit_rows = []
    counters = {"copied": 0, "skipped": 0, "error": 0, "dry_run": 0}
    domain_counters = {}

    for fc in file_classes:
        src_rel = fc.get("file_path", "")
        src_abs = RAW_DIR / src_rel
        domain = fc.get("domain", "Unclassified")
        confidence = fc.get("confidence", 0.0)

        dest_path = build_destination_path(fc)
        dest_rel = str(dest_path.relative_to(BASE_DIR))

        audit_row = {
            "timestamp": datetime.now().isoformat(),
            "action": "DRY_RUN_COPY" if dry_run else "COPY",
            "original_path": src_rel,
            "original_abs_path": str(src_abs),
            "destination_path": dest_rel,
            "destination_abs_path": str(dest_path),
            "domain": domain,
            "confidence": confidence,
            "file_size_bytes": fc.get("file_size_bytes", ""),
            "status": "",
            "error_message": "",
        }

        domain_counters[domain] = domain_counters.get(domain, 0) + 1

        if dry_run:
            print(f"  [DRY-RUN] {src_rel}")
            print(f"         → _REORGANIZED/{fc.get('recommended_folder', '?')}/")
            print(f"           domain={domain}  conf={confidence:.2f}")
            audit_row["status"] = "DRY_RUN"
            counters["dry_run"] += 1
        else:
            # Skip if source doesn't exist
            if not src_abs.exists():
                print(f"  [SKIP]  Source not found: {src_rel}")
                audit_row["status"] = "SKIPPED_MISSING_SOURCE"
                counters["skipped"] += 1
                audit_rows.append(audit_row)
                continue

            try:
                dest_path = make_unique(dest_path)
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Create folder README
                label = FOLDER_LABELS.get(fc.get("recommended_folder", ""), "")
                create_folder_readme(dest_path.parent, label)

                shutil.copy2(str(src_abs), str(dest_path))
                print(f"  [COPY]  {src_rel}")
                print(f"       - {dest_path.relative_to(BASE_DIR)}")
                audit_row["status"] = "SUCCESS"
                audit_row["destination_abs_path"] = str(dest_path)
                audit_row["destination_path"] = str(dest_path.relative_to(BASE_DIR))
                counters["copied"] += 1
            except Exception as e:
                print(f"  [ERROR] {src_rel} — {e}")
                audit_row["status"] = "ERROR"
                audit_row["error_message"] = str(e)
                counters["error"] += 1

        audit_rows.append(audit_row)

    # ── Write audit CSV ──────────────────────────────────────────────────────
    audit_mode = "dry_run_" if dry_run else ""
    audit_path = OUTPUT_DIR / f"{audit_mode}migration_audit.csv"
    with open(audit_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"\n  [OK] Audit trail → {audit_path}")

    # ── Create top-level _REORGANIZED README if executing ───────────────────
    if not dry_run:
        readme = REORG_DIR / "README.txt"
        readme.write_text(
            "REORGANIZED DATA — Techno Education Center\n"
            f"Migration performed: {datetime.now().isoformat()}\n"
            "This directory contains reorganized copies of Excel files.\n"
            "Original source files are unchanged in their original locations.\n\n"
            "Folder Structure:\n"
            "  01_CourseAttendance/  — Course/student attendance registers\n"
            "  02_CompetitionTracking/ — FLL and Robofest competition files\n"
            "  03_StaffAttendance/   — Staff/instructor attendance records\n"
            "  04_CRM_SAT/           — CRM and SAT group records\n"
            "  05_Unclassified/      — Files requiring manual review\n",
            encoding="utf-8",
        )

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    if dry_run:
        print(f"  DRY-RUN COMPLETE — no files were actually copied")
        print(f"  To execute: python 03_reorganize.py --execute")
    else:
        print(f"  MIGRATION COMPLETE")
        print(f"  Files copied        : {counters['copied']}")
        print(f"  Files skipped       : {counters['skipped']}")
        print(f"  Errors              : {counters['error']}")
    print(f"\n  DOMAIN DISTRIBUTION IN NEW STRUCTURE:")
    for domain, count in sorted(domain_counters.items(), key=lambda x: -x[1]):
        print(f"    {domain:<30} {count} files")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    reorganize(dry_run=not execute)
