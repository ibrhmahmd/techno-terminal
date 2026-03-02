"""
Script 2: Schema Pattern Analysis & Domain Classification
==========================================================
Reads file_metadata.json produced by 01_analyze_files.py and:
  - Clusters files into schema groups using column fingerprint similarity
  - Classifies each file into a business domain
  - Identifies the top recurring schema patterns
  - Flags unresolvable columns

Outputs:
  _standardization_output/schema_patterns.json
  _standardization_output/schema_analysis_report.txt
  _standardization_output/unresolved_columns.csv

Usage:
  python 02_schema_analysis.py
"""

import json
import csv
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "_standardization_output"
METADATA_FILE = OUTPUT_DIR / "file_metadata.json"

# ─────────────────────────────────────────────────────────────────────────────
# SYNONYM TABLE  (normalized header → canonical field name)
# ─────────────────────────────────────────────────────────────────────────────
COURSE_ATTENDANCE_SYNONYMS = {
    # Name
    "name",
    "student_name",
    "student",
    "pupils",
    "child_name",
    "اسم_الطالب",
    "full_name",
    "name_full",
    "الاسم",
    "childname",
    "studentname",
    # Phone
    "phone",
    "mobile",
    "tel",
    "telephone",
    "contact",
    "phone_number",
    "mobile_number",
    "رقم_التليفون",
    "رقم_الهاتف",
    "رقم",
    # Course
    "course",
    "subject",
    "class",
    "program",
    "level",
    "lv",
    "lvl",
    "course_name",
    "course_level",
    "session",
    # Day / time
    "day",
    "session_day",
    "weekday",
    "time",
    "time_slot",
    "from_to",
    "start_time",
    "end_time",
    # Instructor
    "instructor",
    "teacher",
    "coach",
    "trainer",
    "staff",
}

COMPETITION_SYNONYMS = {
    "team",
    "team_name",
    "فريق",
    "اسم_الفريق",
    "members",
    "member_list",
    "participants",
    "score",
    "points",
    "result",
    "final_score",
    "category",
    "event",
    "event_type",
    "round",
    "heat",
    "match",
    "robot",
    "robot_name",
    "fll",
    "robofest",
    "wro",
    "sumo",
    "parade",
    "arts",
    "competition",
}

STAFF_ATTENDANCE_SYNONYMS = {
    "name",
    "employee",
    "employee_name",
    "staff",
    "staff_name",
    "instructor",
    "teacher",
    "role",
    "position",
    "department",
    "salary",
    "working_days",
    "attendance",
    "total",
    "days_present",
    "days_absent",
}

CRM_SAT_SYNONYMS = {
    "client",
    "client_name",
    "customer",
    "sat",
    "sat_group",
    "group",
    "group_code",
    "batch",
    "batch_code",
    "grade",
    "score",
    "result",
    "mark",
    "status",
    "payment",
    "paid",
    "enrollment",
    "source",
    "referral",
    # Actual discovered columns
    "number",
    "age",
    "fee_paid",
    "month_paid",
    "fees",
    "birth_date",
    "start",
}

# Domain-to-signature mapping: sets of columns that strongly indicate a domain
DOMAIN_SIGNATURES = {
    "CourseAttendance": {
        "strong": {
            "student_name",
            "name",
            "phone",
            "mobile",
            "course",
            "day",
            "time",
            "paid",
            "number",
            "age",
            "fee_paid",
            "month_paid",
            "teacher",
            "start",
        },
        "weak": {
            "level",
            "instructor",
            "session",
            "subject",
            "grade",
            "fees",
            "birth_date",
        },
        "min_strong_match": 1,
    },
    "CompetitionTracking": {
        "strong": {
            "team",
            "team_name",
            "members",
            "score",
            "points",
            "round",
            "sumo",
            "parade",
            "competition",
        },
        "weak": {"fll", "robofest", "category", "robot", "arts"},
        "min_strong_match": 1,
    },
    "StaffAttendance": {
        "strong": {
            "employee",
            "staff_name",
            "role",
            "position",
            "salary",
            "attendance",
            "days_present",
            "days_absent",
        },
        "weak": {"department", "working_days", "total"},
        "min_strong_match": 1,
    },
    "CRM_SAT": {
        "strong": {
            "sat",
            "sat_group",
            "group_code",
            "batch",
            "client",
            "enrollment",
            "group",
        },
        "weak": {"grade", "payment", "status", "mark"},
        "min_strong_match": 1,
    },
}

# Filename-based classification heuristics (applied when fingerprint gives no match)
FILENAME_DOMAIN_RULES = [
    # (list_of_keywords_in_lower_filename, domain, recommended_subfolder)
    (["staff attendance", "staff_attendance"], "StaffAttendance", "03_StaffAttendance"),
    (["employee", "hr ", "payroll"], "StaffAttendance", "03_StaffAttendance"),
    (["sat group", "sat groups", "sat.xlsx"], "CRM_SAT", "04_CRM_SAT"),
    (["crm", "client", "customer"], "CRM_SAT", "04_CRM_SAT"),
    (
        ["fll ", "fll.", "fll_", "first lego"],
        "CompetitionTracking",
        "02_CompetitionTracking/FLL",
    ),
    (
        ["robofest", "robo fest"],
        "CompetitionTracking",
        "02_CompetitionTracking/Robofest",
    ),
    (["online and private"], "CRM_SAT", "04_CRM_SAT"),
]

# Columns known to be "date attendance" columns (after normalization)
DATE_COLUMN_PATTERN = re.compile(
    r"^\d{1,2}[_/\-\.]\d{1,2}([_/\-\.]\d{2,4})?$|"  # date-like: 01/05, 1-5-2024
    r"^(sat|sun|mon|tue|wed|thu|fri)\d*$|"  # weekday abbreviations
    r"^week\d+$|^session\d+$|^s\d+$|^w\d+$|^d\d+$"  # week/session numbers
)


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def jaccard_similarity(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def classify_domain(fingerprint, file_path=""):
    """Return (domain_name, confidence_score, recommended_folder) for a column fingerprint."""
    fp = set(fingerprint)
    best_domain = "Unclassified"
    best_score = 0.0
    best_folder = None

    for domain, sig in DOMAIN_SIGNATURES.items():
        strong_hits = len(fp & sig["strong"])
        weak_hits = len(fp & sig["weak"])
        if strong_hits < sig["min_strong_match"]:
            continue
        score = (strong_hits * 2.0 + weak_hits * 1.0) / (
            len(sig["strong"]) * 2 + len(sig["weak"])
        )
        if score > best_score:
            best_score = score
            best_domain = domain

    # Heuristic: many date-like columns → likely an attendance sheet
    date_cols = sum(1 for c in fp if DATE_COLUMN_PATTERN.match(str(c)))
    if date_cols >= 3 and best_domain == "Unclassified":
        best_domain = "CourseAttendance"
        best_score = date_cols / max(len(fp), 1) * 0.6

    # Filename-based fallback: if still unclassified or low confidence, try filename
    if best_domain == "Unclassified" or best_score < 0.05:
        path_lower = str(file_path).lower().replace("\\", "/")
        fname_lower = path_lower.split("/")[-1] if "/" in path_lower else path_lower
        full_lower = path_lower  # include folder path in search
        for keywords, domain, folder in FILENAME_DOMAIN_RULES:
            if any(kw in full_lower for kw in keywords):
                best_domain = domain
                best_score = 0.5  # moderate confidence (filename-derived)
                best_folder = folder
                break

    return best_domain, round(best_score, 3), best_folder


def identify_unresolved(fingerprint):
    """Return columns not in any synonym table."""
    all_known = (
        COURSE_ATTENDANCE_SYNONYMS
        | COMPETITION_SYNONYMS
        | STAFF_ATTENDANCE_SYNONYMS
        | CRM_SAT_SYNONYMS
    )
    all_known_normalized = {re.sub(r"[_\s]+", "_", k.lower()) for k in all_known}
    unresolved = []
    for col in fingerprint:
        is_date = bool(DATE_COLUMN_PATTERN.match(str(col)))
        if col not in all_known_normalized and not is_date:
            unresolved.append(col)
    return unresolved


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def analyze_schemas():
    if not METADATA_FILE.exists():
        print(f"[ERROR] {METADATA_FILE} not found. Run 01_analyze_files.py first.")
        return

    with open(METADATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", [])
    print(f"\n{'=' * 70}")
    print(f"  Schema Pattern Analysis")
    print(f"  Loaded {len(files)} file records")
    print(f"{'=' * 70}\n")

    domain_counts = Counter()
    schema_groups = defaultdict(list)  # fingerprint_key → [file_paths]
    unresolved_rows = []
    file_classifications = []

    for file_rec in files:
        if file_rec.get("error"):
            file_classifications.append(
                {
                    "file_path": file_rec["file_path"],
                    "domain": "Unclassified",
                    "confidence": 0.0,
                    "reason": "unreadable",
                    "recommended_folder": "05_Unclassified/corrupt",
                    "sheet_count": 0,
                    "total_rows": 0,
                }
            )
            domain_counts["Unclassified"] += 1
            continue

        for sheet in file_rec.get("sheets", []):
            fp = sheet.get("fingerprint", [])
            fp_key = "|".join(sorted(fp))
            schema_groups[fp_key].append(
                f"{file_rec['file_path']}::{sheet['sheet_name']}"
            )

        # Classify using the union of all sheet fingerprints
        combined_fp = set()
        for sheet in file_rec.get("sheets", []):
            combined_fp.update(sheet.get("fingerprint", []))

        domain, confidence, override_folder = classify_domain(
            list(combined_fp), file_rec.get("file_path", "")
        )
        unresolved = identify_unresolved(list(combined_fp))

        total_rows = sum(s.get("row_count", 0) for s in file_rec.get("sheets", []))

        # Recommended folder path
        folder_map = {
            "CourseAttendance": "01_CourseAttendance",
            "CompetitionTracking": "02_CompetitionTracking",
            "StaffAttendance": "03_StaffAttendance",
            "CRM_SAT": "04_CRM_SAT",
            "Unclassified": "05_Unclassified",
        }
        rec_folder = folder_map.get(domain, "05_Unclassified")

        # If filename-based override gave a specific subfolder, use it
        if override_folder:
            rec_folder = override_folder
        else:
            # Sub-folder heuristics
            path_lower = file_rec["file_path"].lower()
            if domain == "CourseAttendance":
                if any(
                    x in path_lower
                    for x in [
                        "old",
                        "march",
                        "april",
                        "may",
                        "june",
                        "july",
                        "august",
                        "sept",
                        "october",
                        "مايو",
                        "يونيو",
                        "يوليو",
                        "شهر",
                    ]
                ):
                    rec_folder += "/Archive"
                else:
                    rec_folder += "/Active"
            elif domain == "CompetitionTracking":
                if "fll" in path_lower:
                    rec_folder += "/FLL"
                elif any(x in path_lower for x in ["robofest", "robo"]):
                    rec_folder += "/Robofest"

        file_classifications.append(
            {
                "file_path": file_rec["file_path"],
                "filename": file_rec["filename"],
                "domain": domain,
                "confidence": confidence,
                "reason": f"{len(combined_fp)} columns, {len(unresolved)} unresolved",
                "recommended_folder": rec_folder,
                "sheet_count": len(file_rec.get("sheets", [])),
                "total_rows": total_rows,
                "unresolved_columns": unresolved,
            }
        )

        domain_counts[domain] += 1

        # Collect unresolved columns
        for col in unresolved:
            unresolved_rows.append(
                {
                    "file_path": file_rec["file_path"],
                    "column": col,
                    "domain_guess": domain,
                    "action_required": "manually_map_or_ignore",
                }
            )

    # ── Schema group clustering ──────────────────────────────────────────────
    top_clusters = sorted(schema_groups.items(), key=lambda x: -len(x[1]))[:20]

    # ── Compute coverage ────────────────────────────────────────────────────
    total_classified = sum(v for k, v in domain_counts.items() if k != "Unclassified")
    total = sum(domain_counts.values())
    classification_rate = (total_classified / total * 100) if total > 0 else 0

    # ── Write outputs ────────────────────────────────────────────────────────
    patterns_path = OUTPUT_DIR / "schema_patterns.json"
    with open(patterns_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_timestamp": datetime.now().isoformat(),
                "classification_rate_pct": round(classification_rate, 1),
                "domain_counts": dict(domain_counts),
                "file_classifications": file_classifications,
                "top_schema_clusters": [
                    {"fingerprint": k, "file_count": len(v), "examples": v[:3]}
                    for k, v in top_clusters
                ],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"  [OK] Schema patterns → {patterns_path}")

    # Unresolved columns CSV
    unresolved_path = OUTPUT_DIR / "unresolved_columns.csv"
    if unresolved_rows:
        with open(unresolved_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=unresolved_rows[0].keys())
            writer.writeheader()
            writer.writerows(unresolved_rows)
    print(f"  [OK] Unresolved columns → {unresolved_path}")

    # Text report
    report_path = OUTPUT_DIR / "schema_analysis_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("SCHEMA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total files analyzed      : {total}\n")
        f.write(f"Classification rate        : {classification_rate:.1f}%\n")
        f.write(f"Unresolved column entries  : {len(unresolved_rows)}\n\n")
        f.write("DOMAIN DISTRIBUTION\n")
        f.write("-" * 40 + "\n")
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            pct = count / total * 100 if total else 0
            f.write(f"  {domain:<30} {count:>4} files ({pct:.1f}%)\n")
        f.write("\n\nTOP SCHEMA PATTERNS (by file count)\n")
        f.write("-" * 40 + "\n")
        for i, (fp_key, file_list) in enumerate(top_clusters[:10], 1):
            cols = fp_key.split("|")
            f.write(f"\n  Pattern #{i} — {len(file_list)} files\n")
            f.write(f"  Columns: {', '.join(cols[:12])}")
            if len(cols) > 12:
                f.write(f" ... (+{len(cols) - 12} more)")
            f.write("\n  Examples:\n")
            for ex in file_list[:3]:
                f.write(f"    - {ex}\n")
        f.write("\n\nFILE-LEVEL CLASSIFICATIONS\n")
        f.write("-" * 40 + "\n")
        for fc in file_classifications:
            f.write(
                f"  [{fc['domain']:<22}] conf={fc['confidence']:.2f}  → {fc['file_path']}\n"
            )
            f.write(f"    Recommended: _REORGANIZED/{fc['recommended_folder']}\n")
    print(f"  [OK] Report → {report_path}")

    # ── Console summary ──────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  CLASSIFICATION SUMMARY")
    print(f"  Classification rate : {classification_rate:.1f}%  (target ≥ 95%)")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100 if total else 0
        bar = "█" * int(pct / 5)
        print(f"  {domain:<28} {bar:<20} {count:>3} ({pct:.0f}%)")
    print(f"{'=' * 70}\n")

    return file_classifications


if __name__ == "__main__":
    analyze_schemas()
