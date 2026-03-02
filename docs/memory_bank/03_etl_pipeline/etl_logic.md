# ETL Process & Edge Case History

## Core ETL Philosophy: Unpivoting

The most complex part of this project was transforming **wide-format** human-readable Excel grids into **long-format** relational database rows.

### The Problem

Instructors recorded attendance like this:

| Name | Phone | 12-Oct | 19-Oct | 26-Oct |
|---|---|---|---|---|
| Adam | 0123... | 1 | 0 | 1 |

### The Solution

`06_transform_data.py` reads the header row and identifies any column that looks like a date/time stamp (e.g. `12-Oct`, `session1`, `sat4`). It maps these uniquely as an "Attendance Column".

When it iterates down the data row for "Adam", it generates a new database record for *every single date*.
Instead of 1 row for Adam, it generates 3 normalized rows:

- `Adam, 12-Oct, 1`
- `Adam, 19-Oct, 0`
- `Adam, 26-Oct, 1`

## Known Bugs & Edge Cases

### The "oday" (Today) Metadata Leak

**Symptom**: The resulting `Master_Database.xlsx` was generating 3,600+ rows where the `person_name` was literally "Session Date", "Teacher Name", "Session Time", or "oday" (typo for Today).
**Root Cause**: In many sheets, the actual header row (containing `student_name`) was row 3. Rows 4, 5, and 6 contained course metadata (e.g., Row 4's first cell was "Session Date:"). Because the ETL script blindly started reading students immediately below the header row, it ingested these metadata rows as people.
**Resolution**: The `transform_data` script was updated to scan ahead and aggressively filter out any row whose leading cell contained keywords like `date, time, today, oday, session, teacher`.

### The "s1" Date Masking

**Symptom**: Some columns were labelled simply "s1, s2, s3". This meant the final database had "s1" as the attendance date, which is useless for time-series analysis.
**Root Cause**: The true dates were hidden in the aforementioned "Session Date" metadata row (row 4/5).
**Resolution**: The script now intelligently reads the "Session Date" row *before* discarding it, extracts the true datestamps, and injects them back into the "s1, s2" column headers during the unpivoting phase.

### Windows Terminal Encoding (UnicodeEncodeError)

**Symptom**: The script crashed silently via PowerShell when trying to print an arrow character `→`.
**Resolution**: Strings were sanitized to use standard ASCII hyphens `-`, and `sys.stdout.reconfigure(encoding='utf-8')` was added to all core scripts to prevent Arabic filenames from crashing the shell prints.
